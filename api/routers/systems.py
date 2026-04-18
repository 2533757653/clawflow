from fastapi import APIRouter, HTTPException, status
from typing import List, Optional
from datetime import datetime
from api.models import AgentSystem, SystemLoopStep, SystemNode, SystemEdge, ExecutorType, ExecutorUnit, Role
from api.services import StorageService

router = APIRouter()

MAX_DEPTH = 3


def get_system_storage(org_id: str) -> StorageService[AgentSystem]:
    return StorageService[AgentSystem](f"data/organizations/{org_id}/systems", AgentSystem)


def get_role_storage(org_id: str) -> StorageService[Role]:
    return StorageService[Role](f"data/organizations/{org_id}/roles", Role)


def get_loop_step_storage(system_id: str) -> StorageService[SystemLoopStep]:
    return StorageService[SystemLoopStep](f"data/organizations/systems/{system_id}/steps", SystemLoopStep)


def get_executor_name(executor: ExecutorUnit, org_id: str) -> str:
    if executor.type == ExecutorType.ROLE:
        role_storage = get_role_storage(org_id)
        role = role_storage.get(executor.role_id)
        return role.name if role else executor.role_id
    else:
        sys_storage = get_system_storage(org_id)
        sys = sys_storage.get(executor.system_id)
        return sys.name if sys else executor.system_id


@router.get("/{org_id}/systems", response_model=List[AgentSystem])
async def list_systems(org_id: str):
    storage = get_system_storage(org_id)
    return storage.list()


@router.post("/{org_id}/systems", response_model=AgentSystem, status_code=status.HTTP_201_CREATED)
async def create_system(org_id: str, system: AgentSystem):
    system.organization_id = org_id
    if system.max_depth == 0:
        system.max_depth = MAX_DEPTH
    storage = get_system_storage(org_id)
    return storage.save(system)


@router.get("/{org_id}/systems/{system_id}", response_model=AgentSystem)
async def get_system(org_id: str, system_id: str):
    storage = get_system_storage(org_id)
    system = storage.get(system_id)
    if not system:
        raise HTTPException(status_code=404, detail="System not found")
    return system


@router.put("/{org_id}/systems/{system_id}", response_model=AgentSystem)
async def update_system(org_id: str, system_id: str, system: AgentSystem):
    storage = get_system_storage(org_id)
    existing = storage.get(system_id)
    if not existing:
        raise HTTPException(status_code=404, detail="System not found")
    system.id = system_id
    system.organization_id = org_id
    return storage.save(system)


@router.delete("/{org_id}/systems/{system_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_system(org_id: str, system_id: str):
    storage = get_system_storage(org_id)
    if not storage.delete(system_id):
        raise HTTPException(status_code=404, detail="System not found")


@router.post("/{org_id}/systems/{system_id}/decider", response_model=AgentSystem)
async def set_decider(org_id: str, system_id: str, executor: ExecutorUnit):
    storage = get_system_storage(org_id)
    system = storage.get(system_id)
    if not system:
        raise HTTPException(status_code=404, detail="System not found")

    executor.depth = 0
    executor.name = get_executor_name(executor, org_id)
    system.decider = executor
    return storage.save(system)


@router.post("/{org_id}/systems/{system_id}/actors", response_model=AgentSystem)
async def add_actor(org_id: str, system_id: str, executor: ExecutorUnit):
    storage = get_system_storage(org_id)
    system = storage.get(system_id)
    if not system:
        raise HTTPException(status_code=404, detail="System not found")

    executor.depth = 0
    executor.name = get_executor_name(executor, org_id)

    for existing in system.actors:
        if existing.type == executor.type:
            if executor.type == ExecutorType.ROLE and existing.role_id == executor.role_id:
                return system
            if executor.type == ExecutorType.SYSTEM and existing.system_id == executor.system_id:
                return system

    system.actors.append(executor)
    return storage.save(system)


@router.delete("/{org_id}/systems/{system_id}/actors/{actor_idx}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_actor(org_id: str, system_id: str, actor_idx: int):
    storage = get_system_storage(org_id)
    system = storage.get(system_id)
    if not system:
        raise HTTPException(status_code=404, detail="System not found")
    if 0 <= actor_idx < len(system.actors):
        system.actors.pop(actor_idx)
        storage.save(system)


@router.post("/{org_id}/systems/{system_id}/feedbacker", response_model=AgentSystem)
async def set_feedbacker(org_id: str, system_id: str, executor: ExecutorUnit):
    storage = get_system_storage(org_id)
    system = storage.get(system_id)
    if not system:
        raise HTTPException(status_code=404, detail="System not found")

    executor.depth = 0
    executor.name = get_executor_name(executor, org_id)
    system.feedbacker = executor
    return storage.save(system)


@router.post("/{org_id}/systems/{system_id}/start", response_model=AgentSystem)
async def start_system(org_id: str, system_id: str):
    storage = get_system_storage(org_id)
    system = storage.get(system_id)
    if not system:
        raise HTTPException(status_code=404, detail="System not found")
    if not system.decider or not system.actors or not system.feedbacker:
        raise HTTPException(status_code=400, detail="System must have decider, at least one actor, and a feedbacker")
    system.state = "running"
    system.loop_count = 0
    return storage.save(system)


@router.post("/{org_id}/systems/{system_id}/stop", response_model=AgentSystem)
async def stop_system(org_id: str, system_id: str):
    storage = get_system_storage(org_id)
    system = storage.get(system_id)
    if not system:
        raise HTTPException(status_code=404, detail="System not found")
    system.state = "stopped"
    return storage.save(system)


def execute_executor(org_id: str, executor: ExecutorUnit, loop_num: int, current_depth: int) -> dict:
    result = {
        "executor_type": executor.type,
        "executor_name": executor.name,
        "depth": current_depth,
        "phases": {}
    }

    if executor.type == ExecutorType.ROLE:
        result["phases"] = {
            "decider": {"directive": f"[Depth {current_depth}] Role {executor.name} deciding"},
            "actor": {"effect": f"[Depth {current_depth}] Role {executor.name} acting"},
            "feedbacker": {"observation": f"[Depth {current_depth}] Role {executor.name} observing"}
        }
    else:
        if current_depth >= MAX_DEPTH:
            result["phases"] = {
                "error": {"message": f"Max depth {MAX_DEPTH} reached, cannot execute nested system"}
            }
            return result

        sub_system = get_system_storage(org_id).get(executor.system_id)
        if not sub_system:
            result["phases"] = {
                "error": {"message": f"System {executor.system_id} not found"}
            }
            return result

        sub_steps = []
        for i in range(len(sub_system.actors)):
            actor = sub_system.actors[i]
            actor_exec = execute_executor(org_id, actor, loop_num, current_depth + 1)
            sub_steps.append(actor_exec)

        result["phases"] = {
            "decider": {"directive": f"[Depth {current_depth}] System {executor.name} deciding"},
            "actor": {"sub_steps": sub_steps},
            "feedbacker": {"observation": f"[Depth {current_depth}] System {executor.name} observing"}
        }

    return result


@router.post("/{org_id}/systems/{system_id}/loop", response_model=SystemLoopStep)
async def execute_loop_step(org_id: str, system_id: str):
    storage = get_system_storage(org_id)
    system = storage.get(system_id)
    if not system:
        raise HTTPException(status_code=404, detail="System not found")
    if system.state != "running":
        raise HTTPException(status_code=400, detail="System is not running")

    if system.max_loops and system.loop_count >= system.max_loops:
        system.state = "terminated"
        system.updated_at = datetime.now()
        storage.save(system)
        step = SystemLoopStep(
            system_id=system_id,
            step_index=system.loop_count,
            phase="termination",
            terminated=True,
            termination_reason="max_loops_reached"
        )
        return step

    system.loop_count += 1
    system.updated_at = datetime.now()
    storage.save(system)

    decider_result = execute_executor(org_id, system.decider, system.loop_count, 0)

    actor_results = []
    for actor in system.actors:
        actor_result = execute_executor(org_id, actor, system.loop_count, 0)
        actor_results.append(actor_result)

    feedbacker_result = execute_executor(org_id, system.feedbacker, system.loop_count, 0)

    step = SystemLoopStep(
        system_id=system_id,
        step_index=system.loop_count,
        phase="complete",
        depth=0,
        executor_type="system",
        executor_name=system.name,
        decider_output=decider_result,
        actor_output={"actors": actor_results},
        feedbacker_output=feedbacker_result,
        terminated=False
    )

    should_terminate = system.max_loops and system.loop_count >= system.max_loops
    if should_terminate:
        step.terminated = True
        step.termination_reason = "max_loops_reached"

    step_storage = get_loop_step_storage(system_id)
    step_storage.save(step)

    return step


@router.get("/{org_id}/systems/{system_id}/steps", response_model=List[SystemLoopStep])
async def get_loop_steps(org_id: str, system_id: str):
    storage = get_system_storage(org_id)
    system = storage.get(system_id)
    if not system:
        raise HTTPException(status_code=404, detail="System not found")
    step_storage = get_loop_step_storage(system_id)
    return step_storage.list()


@router.get("/{org_id}/available-executors")
async def get_available_executors(org_id: str):
    role_storage = get_role_storage(org_id)
    system_storage = get_system_storage(org_id)

    roles = role_storage.list()
    systems = system_storage.list()

    return {
        "roles": [{"id": r.id, "name": r.name, "type": "role"} for r in roles],
        "systems": [{"id": s.id, "name": s.name, "type": "system"} for s in systems]
    }