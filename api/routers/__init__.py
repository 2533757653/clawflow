from .organizations import router as organizations_router
from .roles import router as roles_router
from .tasks import router as tasks_router
from .dataflows import router as dataflows_router
from .knowledge import router as knowledge_router
from .skills import router as skills_router
from .rag import router as rag_router
from .systems import router as systems_router
from .generator import router as generator_router

__all__ = [
    "organizations_router",
    "roles_router",
    "tasks_router",
    "dataflows_router",
    "knowledge_router",
    "skills_router",
    "rag_router",
    "systems_router",
    "generator_router"
]
