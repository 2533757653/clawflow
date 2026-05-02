import logging
from fastapi import APIRouter, HTTPException
from api.services.execution_service import (
    ExecutionService, ExecuteRequest, ExecutionResult
)

logger = logging.getLogger(__name__)
router = APIRouter()
execution_service = ExecutionService()


@router.post("/organizations/{org_id}/execute", response_model=ExecutionResult)
async def execute_workflow(org_id: str, request: ExecuteRequest):
    logger.info(f"Executing workflow for org={org_id}, input_role={request.input_role_id}")
    result = execution_service.execute_workflow(
        organization_id=org_id,
        input_data=request.input_data,
        dataflow_id=request.dataflow_id,
        input_role_id=request.input_role_id
    )
    if result.status == "failed":
        logger.error(f"Workflow failed for org={org_id}: {result.final_output.get('error')}")
    else:
        logger.info(f"Workflow completed: execution_id={result.execution_id}, nodes={len(result.node_results)}")
    return result


@router.get("/organizations/{org_id}/execution/{execution_id}")
async def get_execution_status(org_id: str, execution_id: str):
    return {
        "execution_id": execution_id,
        "status": "completed",
        "message": "Execution tracking not yet implemented"
    }


@router.get("/organizations/{org_id}/dataflows/{dataflow_id}/validate")
async def validate_dataflow(org_id: str, dataflow_id: str):
    dataflow_service = execution_service._load_dataflow(org_id, dataflow_id)
    if not dataflow_service:
        raise HTTPException(status_code=404, detail="DataFlow not found")

    try:
        execution_order = execution_service.topological_sort(
            dataflow_service.nodes, dataflow_service.edges
        )
        logger.debug(f"DataFlow {dataflow_id} validated: {len(dataflow_service.nodes)} nodes, {len(dataflow_service.edges)} edges")
        return {
            "valid": True,
            "node_count": len(dataflow_service.nodes),
            "edge_count": len(dataflow_service.edges),
            "execution_order": execution_order
        }
    except ValueError as e:
        logger.warning(f"DataFlow {dataflow_id} has cycle: {e}")
        return {
            "valid": False,
            "error": str(e)
        }
