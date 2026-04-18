from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
import uuid


class SystemTemplateType(str, Enum):
    SIMPLE = "simple"
    HIERARCHICAL = "hierarchical"
    PARALLEL = "parallel"


class GeneratedRole(BaseModel):
    name: str
    description: str
    responsibilities: List[str]
    role_type: str
    hierarchy_level: int = 1


class GeneratedActor(BaseModel):
    name: str
    is_nested_system: bool = False
    nested_roles: List["GeneratedRole"] = []
    is_group: bool = False
    group_members: List[str] = []


class GeneratedSystem(BaseModel):
    name: str
    description: str
    template_type: SystemTemplateType
    decider: GeneratedRole
    actors: List[GeneratedActor]
    feedbacker: GeneratedRole
    nested_systems: List["GeneratedSystem"] = []


class GenerateRequest(BaseModel):
    description: str
    org_id: Optional[str] = None


class GenerateResponse(BaseModel):
    roles: List[GeneratedRole]
    systems: List[GeneratedSystem]
    suggestions: List[str] = []


GeneratedSystem.model_rebuild()
GeneratedActor.model_rebuild()


class ArchitectureGenerator:
    def __init__(self):
        self.decision_keywords = ["领导", "决策", "指挥", "管理", "负责", "制定", "规划", "策略", "经理", "总监", "主管", "负责人", "cto", "ceo", "coo", "cfo", "chief", "director", "lead", "head"]
        self.action_keywords = ["执行", "实施", "开发", "制作", "设计", "写", "完成", "实现", "操作", "干活", "工程师", "开发者", "设计师", "策划", "analyst", "developer", "designer", "engineer", "executer"]
        self.feedback_keywords = ["监督", "审核", "检查", "评审", "验收", "评估", "监控", "质量", "测试", "reviewer", "auditor", "supervisor", "qa", "tester", "qc", "quality"]
        self.nested_keywords = ["组", "团队", "部门", "team", "department", "group", "unit", "包含", "下设"]

    def _classify_role(self, name: str, description: str = "") -> str:
        text = (name + " " + description).lower()
        for kw in self.decision_keywords:
            if kw.lower() in text:
                return "decider"
        for kw in self.feedback_keywords:
            if kw.lower() in text:
                return "feedbacker"
        for kw in self.action_keywords:
            if kw.lower() in text:
                return "actor"
        return "actor"

    def _parse_single_role(self, text: str) -> Optional[GeneratedRole]:
        text = text.strip().rstrip(',，')
        if not text or len(text) < 2:
            return None

        name = text.split("（")[0].split("(")[0].strip()
        name = name.split("：")[0].split(":")[0].strip()

        desc = ""
        if "（" in text:
            desc = text.split("（")[1].split("）")[0]
        elif "(" in text:
            desc = text.split("(")[1].split(")")[0]

        role_type = self._classify_role(name, desc)

        responsibilities = []
        if "负责" in text:
            resp_part = text.split("负责")[1] if "负责" in text else ""
            responsibilities = [r.strip() for r in resp_part.split("、") if r.strip()]

        hierarchy_level = 1
        for hl in ["高层", "总监", "director", "chief", "VP", "vp"]:
            if hl.lower() in text.lower():
                hierarchy_level = 4
                break
        for hl in ["经理", "manager", "lead"]:
            if hl.lower() in text.lower():
                hierarchy_level = 2
                break
        for hl in ["主管", "head"]:
            if hl.lower() in text.lower():
                hierarchy_level = 3
                break

        return GeneratedRole(
            name=name,
            description=desc,
            responsibilities=responsibilities,
            role_type=role_type,
            hierarchy_level=hierarchy_level
        )

    def _parse_roles_from_text(self, text: str) -> List[GeneratedRole]:
        roles = []
        separators = ['、', '，', ',', '和', '与', '以及', '\n', ';', '；']

        for sep in separators:
            if sep in text:
                parts = text.split(sep)
                for part in parts:
                    role = self._parse_single_role(part)
                    if role and role.name not in [r.name for r in roles]:
                        roles.append(role)
                break
        else:
            role = self._parse_single_role(text)
            if role:
                roles.append(role)

        return roles

    def _is_nested_system(self, name: str, description: str = "") -> bool:
        text = (name + " " + description).lower()
        for kw in self.nested_keywords:
            if kw.lower() in text:
                return True
        return False

    def _create_nested_actors(self, roles: List[GeneratedRole]) -> List[GeneratedActor]:
        actors = []
        action_roles = [r for r in roles if r.role_type == "actor"]

        if len(action_roles) > 2:
            actors.append(GeneratedActor(
                name="执行小组",
                is_nested_system=True,
                is_group=True,
                group_members=[r.name for r in action_roles],
                nested_roles=action_roles
            ))
        else:
            for r in action_roles:
                actors.append(GeneratedActor(name=r.name))

        return actors

    def generate(self, description: str) -> GenerateResponse:
        description = description.strip()
        if not description:
            return GenerateResponse(roles=[], systems=[], suggestions=["请输入组织描述"])

        roles = self._parse_roles_from_text(description)

        if not roles:
            suggestion = "未能识别角色。请使用逗号分隔角色名称，例如：产品经理、设计师、开发人员"
            return GenerateResponse(roles=[], systems=[], suggestions=[suggestion])

        deciders = [r for r in roles if r.role_type == "decider"]
        feedbackers = [r for r in roles if r.role_type == "feedbacker"]
        actors_roles = [r for r in roles if r.role_type == "actor"]

        if not deciders:
            if len(actors_roles) >= 2:
                decider = GeneratedRole(
                    name="决策者",
                    description="负责制定方向和决策",
                    responsibilities=["分析需求", "制定策略", "分配任务"],
                    role_type="decider",
                    hierarchy_level=3
                )
                roles.append(decider)
                deciders = [decider]
                actors_roles = [r for r in roles if r.role_type == "actor"]
            else:
                return GenerateResponse(
                    roles=roles,
                    systems=[],
                    suggestions=["至少需要 2 个角色才能形成系统", "建议格式：产品经理（负责决策）、开发人员（负责执行）、测试人员（负责反馈）"]
                )

        if not feedbackers:
            feedbacker = GeneratedRole(
                name="反馈者",
                description="负责监督和评估结果",
                responsibilities=["观察效果", "评估质量", "提出改进"],
                role_type="feedbacker",
                hierarchy_level=2
            )
            roles.append(feedbacker)
            feedbackers = [feedbacker]

        nested_systems = []
        actors = []

        action_roles = [r for r in roles if r.role_type == "actor"]
        if len(action_roles) > 3 and self._is_nested_system(description):
            sub_decider = GeneratedRole(
                name="子决策者",
                description="协助主决策者进行子任务规划",
                responsibilities=["分解任务", "协调资源", "跟踪进度"],
                role_type="decider",
                hierarchy_level=2
            )
            sub_feedbacker = GeneratedRole(
                name="子反馈者",
                description="协助主反馈者进行质量把控",
                responsibilities=["质量检查", "进度跟踪", "风险评估"],
                role_type="feedbacker",
                hierarchy_level=2
            )

            sub_actors = []
            for r in action_roles:
                sub_actors.append(GeneratedActor(name=r.name, nested_roles=[r]))

            sub_system = GeneratedSystem(
                name="执行子系统",
                description="由多个执行角色组成的子系统",
                template_type=SystemTemplateType.HIERARCHICAL,
                decider=sub_decider,
                actors=sub_actors,
                feedbacker=sub_feedbacker
            )
            nested_systems.append(sub_system)

            roles.extend([sub_decider, sub_feedbacker])
            actors = [GeneratedActor(
                name="执行子系统",
                is_nested_system=True,
                nested_roles=[]
            )]
        else:
            for r in action_roles:
                actors.append(GeneratedActor(name=r.name))

        main_system = GeneratedSystem(
            name="主决策系统",
            description=description,
            template_type=SystemTemplateType.SIMPLE if not nested_systems else SystemTemplateType.HIERARCHICAL,
            decider=deciders[0],
            actors=actors,
            feedbacker=feedbackers[0],
            nested_systems=nested_systems
        )

        suggestions = []
        if len(roles) >= 5:
            suggestions.append("角色较多，可以考虑分层管理形成更复杂的组织结构")
        if nested_systems:
            suggestions.append("检测到嵌套系统架构，执行者将作为子系统运行")
        suggestions.append("系统生成成功，可在下方查看并调整角色配置")

        return GenerateResponse(
            roles=roles,
            systems=[main_system],
            suggestions=suggestions
        )


generator = ArchitectureGenerator()


def generate_architecture(description: str) -> GenerateResponse:
    return generator.generate(description)
