import json
import logging
from typing import List, Optional
from api.models import Role
from api.services.ai_client import chat_completion, is_ai_available

logger = logging.getLogger(__name__)


class HRAgentService:
    """
    HR Agent 服务 - 辅助填充角色职责。
    当配置了 OPENAI_API_KEY 或 ANTHROPIC_API_KEY 时，使用 AI 生成。
    否则回退到模板生成。
    """

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
        根据角色信息建议职责。当 AI 可用时优先使用 AI 生成。
        """
        # Template fallback
        templates = self.RESPONSIBILITY_TEMPLATES.get(division, {})
        if hierarchy_level in templates:
            responsibilities = templates[hierarchy_level].copy()
        else:
            responsibilities = self.DEFAULT_RESPONSIBILITIES.get(
                max(1, min(4, hierarchy_level)),
                self.DEFAULT_RESPONSIBILITIES[1]
            ).copy()

        if description:
            expanded = self._expand_from_description(description, responsibilities)
            responsibilities = expanded[:5]

        # AI enhancement
        if is_ai_available():
            ai_result = self._ai_suggest_responsibilities(
                name, description, division, hierarchy_level
            )
            if ai_result:
                responsibilities = ai_result

        return responsibilities

    def _ai_suggest_responsibilities(
        self,
        name: str,
        description: Optional[str],
        division: Optional[str],
        hierarchy_level: int
    ) -> Optional[List[str]]:
        level_labels = {1: "Junior/Entry", 2: "Mid-level", 3: "Senior/Lead", 4: "Executive/Director"}
        level = level_labels.get(hierarchy_level, "Mid-level")

        system_prompt = (
            "You are an HR assistant helping define job responsibilities. "
            "Return ONLY a JSON array of 5-7 specific, actionable responsibilities. "
            "No explanation, no markdown, just a JSON array of strings."
        )
        user_prompt = (
            f"Role name: {name}\n"
            f"Description: {description or 'Not provided'}\n"
            f"Department/Division: {division or 'General'}\n"
            f"Hierarchy level: {level}\n\n"
            f"Suggest 5-7 concrete responsibilities for this role, "
            f"specific to the {division or 'general'} context at {level} level. "
            f"Format: JSON array of strings."
        )

        result = chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            model="doubao-seed-2-0-pro-260215",
            temperature=0.7,
            max_tokens=512,
        )

        if result:
            try:
                parsed = json.loads(result)
                if isinstance(parsed, list):
                    return parsed
                if isinstance(parsed, dict) and "responsibilities" in parsed:
                    return parsed["responsibilities"]
            except (json.JSONDecodeError, TypeError):
                logger.warning(f"Failed to parse AI responsibilities: {result[:100]}")

        return None

    def _expand_from_description(
        self,
        description: str,
        base_responsibilities: List[str]
    ) -> List[str]:
        """基于描述扩展职责"""
        description_lower = description.lower()
        expanded = base_responsibilities.copy()

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
        生成 SOUL.md 模板。当 AI 可用时优先使用 AI 生成。
        """
        # Template fallback
        if division and division in self.SOUL_TEMPLATES:
            template = self.SOUL_TEMPLATES[division]
        else:
            template = self.SOUL_TEMPLATES["Engineering"]

        soul = template.format(name=name)

        if responsibilities:
            responsibilities_text = "\n".join([f"- {r}" for r in responsibilities[:5]])
            soul += f"\n\n## Specific Responsibilities\n\n{responsibilities_text}"

        # AI generation
        if is_ai_available():
            ai_result = self._ai_generate_soul_template(
                name, description, division, responsibilities, soul
            )
            if ai_result:
                soul = ai_result

        return soul

    def _ai_generate_soul_template(
        self,
        name: str,
        description: Optional[str],
        division: Optional[str],
        responsibilities: List[str],
        template_fallback: str
    ) -> Optional[str]:
        system_prompt = (
            "You are an HR/culture consultant helping define the SOUL.md for an AI agent role. "
            "SOUL.md defines identity, values, work style, collaboration, and growth. "
            "Write in a confident, specific voice. Use markdown format. "
            "Keep it under 400 words total."
        )
        user_prompt = (
            f"Role name: {name}\n"
            f"Role description: {description or 'Not provided'}\n"
            f"Department: {division or 'General'}\n"
            f"Responsibilities:\n" + "\n".join(f"- {r}" for r in responsibilities[:7]) + "\n\n"
            f"Generate a complete SOUL.md for this role. Include these sections:\n"
            f"## Identity\n## Core Values (4 bullet points)\n## Work Style (4 bullet points)\n"
            f"## Collaboration\n## Growth\n\n"
            f"Be specific and memorable, not generic."
        )

        result = chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            model="doubao-seed-2-0-pro-260215",
            temperature=0.8,
            max_tokens=600,
        )

        if result:
            if responsibilities:
                resp_text = "\n".join(f"- {r}" for r in responsibilities[:5])
                result += f"\n\n## Specific Responsibilities\n{resp_text}"
            return result

        return None

    def suggest_division(self, name: str, description: str) -> Optional[str]:
        """
        根据名称和描述建议部门。当 AI 可用时优先使用 AI 分类。
        """
        # Keyword fallback
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

        # AI classification
        if is_ai_available():
            ai_result = self._ai_suggest_division(name, description)
            if ai_result:
                return ai_result

        return None

    def _ai_suggest_division(
        self,
        name: str,
        description: str
    ) -> Optional[str]:
        divisions = ["Engineering", "Product", "Design", "Marketing", "Sales", "Operations", "HR", "Finance"]

        system_prompt = (
            "You are an HR assistant classifying job roles into departments. "
            "Return ONLY a JSON object with 'division' (string) and 'alternatives' (list of strings). "
            "No explanation, no markdown."
        )
        user_prompt = (
            f"Role name: {name}\n"
            f"Role description: {description}\n\n"
            f"Classify this role into one of these departments: {', '.join(divisions)}. "
            f"Return JSON: {{'division': '...', 'alternatives': ['...', '...']}}"
        )

        result = chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            model="doubao-seed-2-0-pro-260215",
            temperature=0.3,
            max_tokens=200,
        )

        if result:
            try:
                parsed = json.loads(result)
                return parsed.get("division")
            except (json.JSONDecodeError, TypeError):
                logger.warning(f"Failed to parse AI division: {result[:100]}")

        return None
