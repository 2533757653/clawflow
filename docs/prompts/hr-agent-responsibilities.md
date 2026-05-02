# Prompt: 角色职责自动填充系统 (HR Agent)

## 项目信息

- **项目名称**: ClawFlow - Agent 组织动态构建平台
- **项目路径**: `d:\clawflow`
- **后端**: `api/` (FastAPI + Python 3.11+)
- **前端**: `web/` (React 18 + TypeScript)

## 项目架构

参见 `docs/prompts/workflow-execution-engine.md`

## 设计决策

根据 SPEC.md "设计决策记录" section 7:

### 角色职责填充

1. **用户创建角色后，职责和 soul_template 需要填充**
2. **计划使用 HR Agent 来辅助编辑和生成角色职责**
3. **可在角色基本创建完成后，由 Agent 完成细节填充**

## 任务要求

### 1. HR Agent Service

创建 `api/services/hr_agent_service.py`:

```python
from typing import List, Dict, Optional
from api.models import Role

class HRAgentService:
    """
    HR Agent 服务 - 辅助填充角色职责
    当前使用模板生成，未来可集成真正的 AI
    """

    # 按部门和层级定义职责模板
    RESPONSIBILITY_TEMPLATES = {
        "Engineering": {
            1: [
                "Write clean, maintainable code",
                "Participate in code reviews",
                "Debug and fix issues",
                "Write unit tests",
                "Collaborate with team members"
            ],
            2: [
                "Define technical architecture for the team",
                "Mentor and guide junior developers",
                "Coordinate with product management on priorities",
                "Conduct technical interviews",
                "Ensure code quality standards"
            ],
            3: [
                "Set technical vision and roadmap",
                "Lead multiple engineering teams",
                "Align engineering with business objectives",
                "Manage technical debt",
                "Report to CTO/VP Engineering"
            ],
            4: [
                "Set technical strategy for the company",
                "Build and lead engineering organization",
                "Represent engineering in C-suite",
                "Drive innovation",
                "Ensure technology competitiveness"
            ]
        },
        "Product": {
            1: [
                "Gather user requirements",
                "Create user stories",
                "Support product launches",
                "Analyze user feedback",
                "Work with engineering teams"
            ],
            2: [
                "Define product roadmap",
                "Prioritize features",
                "Conduct market research",
                "Define success metrics",
                "Coordinate cross-functional teams"
            ],
            3: [
                "Set product strategy",
                "Lead product management team",
                "Define product vision",
                "Analyze market trends",
                "Report to CEO/CPO"
            ]
        },
        "Design": {
            1: [
                "Create UI designs",
                "Create wireframes and prototypes",
                "Conduct user research",
                "Maintain design systems",
                "Collaborate with developers"
            ],
            2: [
                "Lead design projects",
                "Mentor junior designers",
                "Define design standards",
                "Conduct usability testing",
                "Present designs to stakeholders"
            ],
            3: [
                "Set design vision",
                "Lead design team",
                "Define brand guidelines",
                "Drive design strategy",
                "Report to CPO"
            ]
        }
    }

    # Soul 模板
    SOUL_TEMPLATES = {
        "Engineering": """# SOUL.md - {name}

## Identity

{name} is a member of the Engineering team, focused on building reliable and scalable systems.

## Core Values

- **Quality First**: We don't ship things that are broken. Ever.
- **Ownership**: You build it, you own it.
- **Simplicity**: Complex solutions are usually wrong solutions.
- **Transparency**: Share early, share often.

## Work Style

- Async communication by default
- Write things down (documents > meetings)
- Move fast with stable infrastructure
- Review code thoroughly but ship quickly

## Collaboration

- Work closely with Product to understand requirements
- Partner with QA to ensure quality
- Share knowledge through tech talks and documentation

## Growth

- Learn something new every week
- Mentor others when you can
- Stay curious about new technologies
""",
        "Product": """# SOUL.md - {name}

## Identity

{name} is a Product team member, focused on delivering value to users.

## Core Values

- **User Centric**: Always start with the user problem, not the solution.
- **Data Driven**: Use data to inform decisions.
- **Clarity**: Simple communication wins.
- **Impact**: Focus on what matters most.

## Work Style

- Deeply understand user problems
- Make decisions with incomplete information
- Balance short-term vs long-term
- Ship and iterate

## Collaboration

- Work closely with Engineering and Design
- Facilitate stakeholder alignment
- Present vision clearly

## Growth

- Learn from user feedback
- Develop market understanding
- Build strategic thinking
""",
        "Design": """# SOUL.md - {name}

## Identity

{name} is a Design team member, focused on creating intuitive and beautiful experiences.

## Core Values

- **User Empathy**: Design for real humans, not abstract users.
- **Craftsmanship**: Details matter.
- **Accessibility**: Good design is accessible design.
- **Clarity**: Remove complexity.

## Work Style

- Iterate from rough to refined
- Use prototyping to validate ideas
- Seek feedback early and often
- Balance aesthetics with usability

## Collaboration

- Partner with Product on strategy
- Work closely with Engineering on implementation
- Advocate for user needs

## Growth

- Study design trends
- Learn new tools and techniques
- Share design knowledge
"""
    }

    # 通用职责模板 (当部门不匹配时使用)
    DEFAULT_RESPONSIBILITIES = {
        1: [
            "Complete assigned tasks on time",
            "Communicate progress regularly",
            "Ask for help when needed",
            "Learn from feedback",
            "Support team objectives"
        ],
        2: [
            "Lead team initiatives",
            "Mentor team members",
            "Make decisions within scope",
            "Coordinate with other teams",
            "Report progress to manager"
        ],
        3: [
            "Set team objectives",
            "Manage team performance",
            "Align team with company goals",
            "Develop team capabilities",
            "Report to leadership"
        ],
        4: [
            "Set organizational strategy",
            "Lead organization transformation",
            "Represent organization externally",
            "Drive innovation",
            "Ensure organizational success"
        ]
    }

    def suggest_responsibilities(
        self,
        name: str,
        description: Optional[str],
        division: Optional[str],
        hierarchy_level: int
    ) -> List[str]:
        """
        根据角色信息建议职责:
        1. 匹配部门和层级
        2. 如果有描述，扩展为具体职责
        3. 返回建议列表
        """
        # 查找模板
        templates = self.RESPONSIBILITY_TEMPLATES.get(division, {})

        if hierarchy_level in templates:
            responsibilities = templates[hierarchy_level].copy()
        else:
            responsibilities = self.DEFAULT_RESPONSIBILITIES.get(
                max(1, min(4, hierarchy_level)),
                self.DEFAULT_RESPONSIBILITIES[1]
            ).copy()

        # 如果有描述，基于描述扩展
        if description:
            expanded = self._expand_from_description(description, responsibilities)
            responsibilities = expanded[:5]  # 最多5条

        return responsibilities

    def _expand_from_description(
        self,
        description: str,
        base_responsibilities: List[str]
    ) -> List[str]:
        """基于描述扩展职责"""
        # 简单的关键词匹配
        description_lower = description.lower()

        expanded = base_responsibilities.copy()

        # 根据描述中的关键词添加特定职责
        keywords = {
            "customer": "Engage with customers to gather requirements",
            "data": "Analyze data to drive decisions",
            "manage": "Manage team performance and development",
            "lead": "Lead technical or functional initiatives",
            "design": "Create designs and prototypes",
            "develop": "Develop and implement solutions",
            "test": "Ensure quality through testing",
            "deploy": "Deploy and monitor solutions"
        }

        for key, responsibility in keywords.items():
            if key in description_lower and responsibility not in expanded:
                expanded.append(responsibility)

        return expanded

    def generate_soul_template(
        self,
        name: str,
        description: Optional[str],
        division: Optional[str],
        responsibilities: List[str]
    ) -> str:
        """
        生成 SOUL.md 模板:
        1. 选择基础模板
        2. 填充角色信息
        3. 添加特定职责
        """
        # 获取基础模板
        if division and division in self.SOUL_TEMPLATES:
            template = self.SOUL_TEMPLATES[division]
        else:
            template = self.SOUL_TEMPLATES["Engineering"]

        # 格式化模板
        soul = template.format(name=name)

        # 如果有特定职责，追加到模板
        if responsibilities:
            responsibilities_text = "\n".join([f"- {r}" for r in responsibilities[:5]])
            soul += f"\n\n## Specific Responsibilities\n\n{responsibilities_text}"

        return soul

    def suggest_division(self, name: str, description: str) -> Optional[str]:
        """
        根据名称和描述建议部门:
        1. 关键词匹配
        2. 返回建议的部门
        """
        text = f"{name} {description}".lower()

        division_keywords = {
            "Engineering": ["engineer", "developer", "technical", "software", "code", "backend", "frontend", "devops", "data engineer"],
            "Product": ["product", "manager", "roadmap", "feature", "user"],
            "Design": ["design", "ui", "ux", "visual", "graphic", "designer"],
            "Marketing": ["marketing", "campaign", "content", "seo", "brand"],
            "Sales": ["sales", "revenue", "client", "customer"],
            "Operations": ["operations", "process", "efficiency", "logistics"],
            "HR": ["hr", "human", "recruit", "talent", "people"],
            "Finance": ["finance", "accounting", "budget", "financial"]
        }

        for division, keywords in division_keywords.items():
            if any(keyword in text for keyword in keywords):
                return division

        return None
```

### 2. Role Suggestions API

创建 `api/routers/role_suggestions.py`:

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()
hr_service = HRAgentService()

class SuggestResponsibilitiesRequest(BaseModel):
    name: str
    description: Optional[str] = None
    division: Optional[str] = None
    hierarchy_level: int = 1

class SuggestResponsibilitiesResponse(BaseModel):
    responsibilities: List[str]
    confidence: float  # 0-1, 建议的置信度

class GenerateSoulRequest(BaseModel):
    name: str
    description: Optional[str] = None
    division: Optional[str] = None
    responsibilities: List[str]

class GenerateSoulResponse(BaseModel):
    soul_template: str

class SuggestDivisionRequest(BaseModel):
    name: str
    description: str

class SuggestDivisionResponse(BaseModel):
    suggested_division: Optional[str]
    alternatives: List[str]

class ApplySuggestionsRequest(BaseModel):
    role_id: str
    responsibilities: Optional[List[str]] = None
    soul_template: Optional[str] = None

@router.post("/suggest-responsibilities", response_model=SuggestResponsibilitiesResponse)
async def suggest_responsibilities(request: SuggestResponsibilitiesRequest):
    """
    建议角色职责:
    基于部门、层级和描述生成职责建议
    """
    responsibilities = hr_service.suggest_responsibilities(
        name=request.name,
        description=request.description,
        division=request.division,
        hierarchy_level=request.hierarchy_level
    )

    # 计算置信度
    confidence = 0.5
    if request.division:
        confidence += 0.3
    if request.description:
        confidence += 0.2

    return SuggestResponsibilitiesResponse(
        responsibilities=responsibilities,
        confidence=min(1.0, confidence)
    )

@router.post("/generate-soul", response_model=GenerateSoulResponse)
async def generate_soul(request: GenerateSoulRequest):
    """
    生成 SOUL.md 模板:
    基于角色信息生成 soul_template
    """
    soul_template = hr_service.generate_soul_template(
        name=request.name,
        description=request.description,
        division=request.division,
        responsibilities=request.responsibilities
    )

    return GenerateSoulResponse(soul_template=soul_template)

@router.post("/suggest-division", response_model=SuggestDivisionResponse)
async def suggest_division(request: SuggestDivisionRequest):
    """
    建议部门:
    基于名称和描述推断适合的部门
    """
    suggested = hr_service.suggest_division(
        name=request.name,
        description=request.description
    )

    # 提供备选部门
    alternatives = ["Engineering", "Product", "Design", "Operations"]
    if suggested and suggested in alternatives:
        alternatives.remove(suggested)

    return SuggestDivisionResponse(
        suggested_division=suggested,
        alternatives=alternatives[:3]
    )

@router.post("/apply-suggestions")
async def apply_suggestions(request: ApplySuggestionsRequest):
    """
    应用建议到角色:
    将建议的 responsibilities 和 soul_template 应用到角色
    """
    from api.services import StorageService
    from api.models import Role

    role_storage = StorageService[Role]("data/roles", Role)
    role = role_storage.get(request.role_id)

    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    if request.responsibilities:
        role.responsibilities = request.responsibilities

    if request.soul_template:
        role.soul_template = request.soul_template

    role_storage.save(role)

    return {"message": "Suggestions applied successfully", "role_id": role.id}
```

### 3. 注册路由

修改 `api/main.py`:

```python
from api.routers import role_suggestions

app.include_router(role_suggestions.router, prefix="/api/v1/roles", tags=["Role Suggestions"])
```

### 4. 前端 API

创建 `web/src/services/roleSuggestionApi.ts`:

```typescript
export const roleSuggestionApi = {
  suggestResponsibilities: (request: {
    name: string;
    description?: string;
    division?: string;
    hierarchy_level: number;
  }) => api.post<SuggestResponsibilitiesResponse>('/roles/suggest-responsibilities', request),

  generateSoul: (request: {
    name: string;
    description?: string;
    division?: string;
    responsibilities: string[];
  }) => api.post<GenerateSoulResponse>('/roles/generate-soul', request),

  suggestDivision: (request: {
    name: string;
    description: string;
  }) => api.post<SuggestDivisionResponse>('/roles/suggest-division', request),

  applySuggestions: (request: {
    role_id: string;
    responsibilities?: string[];
    soul_template?: string;
  }) => api.post('/roles/apply-suggestions', request),
};
```

### 5. 前端 UI

修改 `web/src/pages/RoleEditor.tsx`:

```typescript
// 添加 AI 建议功能:

// 1. 添加建议按钮到职责输入框
<Form.Item label="职责">
  <Input.Group>
    <Form.Item name="responsibilities" noStyle>
      <Select mode="tags" placeholder="输入职责后按回车添加">
        {form.getFieldValue('responsibilities')?.map(r => (
          <Select.Option key={r} value={r}>{r}</Select.Option>
        ))}
      </Select>
    </Form.Item>
    <Button
      onClick={async () => {
        const values = form.getFieldsValue();
        const result = await roleSuggestionApi.suggestResponsibilities({
          name: values.name,
          description: values.description,
          division: values.division,
          hierarchy_level: values.hierarchy_level || 1
        });
        // 显示建议
        showSuggestionsModal(result.responsibilities);
      }}
    >
      AI 建议
    </Button>
  </Input.Group>
</Form.Item>

// 2. 添加生成 Soul 按钮
<Form.Item label="Soul 模板">
  <TextArea
    value={form.getFieldValue('soul_template')}
    onChange={e => form.setFieldValue('soul_template', e.target.value)}
    rows={6}
    placeholder="定义角色的核心价值观、工作风格等"
  />
  <Button
    onClick={async () => {
      const values = form.getFieldsValue();
      const result = await roleSuggestionApi.generateSoul({
        name: values.name,
        description: values.description,
        division: values.division,
        responsibilities: values.responsibilities || []
      });
      form.setFieldValue('soul_template', result.soul_template);
    }}
  >
    生成 Soul 模板
  </Button>
</Form.Item>
```

### 6. 建议展示 Modal

创建 `web/src/components/Role/SuggestionsModal.tsx`:

```typescript
interface SuggestionsModalProps {
  open: boolean;
  responsibilities: string[];
  onApply: (selected: string[]) => void;
  onCancel: () => void;
}

// 功能:
// - 展示建议的职责列表
// - 用户可以勾选要应用的
// - 可以编辑建议内容
// - Apply/Cancel 按钮
```

## 文件结构

```
api/
├── routers/
│   └── role_suggestions.py   # 新增: 角色建议 API
├── services/
│   └── hr_agent_service.py    # 新增: HR Agent 服务
└── main.py                   # 修改: 注册路由

web/src/
├── services/
│   └── roleSuggestionApi.ts   # 新增: 前端 API
├── components/
│   └── Role/
│       └── SuggestionsModal.tsx  # 新增: 建议 Modal
└── pages/
    └── RoleEditor.tsx        # 修改: 集成建议功能
```

## 注意事项

1. **模板扩展性**: 当前使用硬编码模板，未来可改为配置文件或数据库
2. **AI 集成**: 未来可集成真正的 AI 模型来生成更智能的建议
3. **用户控制**: 所有 AI 建议都需要用户确认后才能应用
4. **置信度**: 返回置信度帮助用户判断建议质量

## 验收标准

- [ ] POST /api/v1/roles/suggest-responsibilities 返回职责建议
- [ ] POST /api/v1/roles/generate-soul 返回 soul 模板
- [ ] POST /api/v1/roles/suggest-division 返回部门建议
- [ ] POST /api/v1/roles/apply-suggestions 应用建议到角色
- [ ] 前端有 AI 建议按钮
- [ ] 前端有生成 Soul 模板按钮
- [ ] 建议需要用户确认后才能应用
