from fastapi import APIRouter, HTTPException, status
from typing import List
from api.models import DataFlow, DataFlowNode, DataFlowEdge
from api.services import StorageService

router = APIRouter()


def get_dataflow_storage(org_id: str) -> StorageService[DataFlow]:
    return StorageService[DataFlow](f"data/organizations/{org_id}/dataflows", DataFlow)


@router.get("/{org_id}/dataflows", response_model=List[DataFlow])
async def list_dataflows(org_id: str):
    storage = get_dataflow_storage(org_id)
    return storage.list()


@router.post("/{org_id}/dataflows", response_model=DataFlow, status_code=status.HTTP_201_CREATED)
async def create_dataflow(org_id: str, dataflow: DataFlow):
    dataflow.organization_id = org_id
    storage = get_dataflow_storage(org_id)
    return storage.save(dataflow)


@router.get("/{org_id}/dataflows/{dataflow_id}", response_model=DataFlow)
async def get_dataflow(org_id: str, dataflow_id: str):
    storage = get_dataflow_storage(org_id)
    dataflow = storage.get(dataflow_id)
    if not dataflow:
        raise HTTPException(status_code=404, detail="DataFlow not found")
    return dataflow


@router.put("/{org_id}/dataflows/{dataflow_id}", response_model=DataFlow)
async def update_dataflow(org_id: str, dataflow_id: str, dataflow: DataFlow):
    storage = get_dataflow_storage(org_id)
    existing = storage.get(dataflow_id)
    if not existing:
        raise HTTPException(status_code=404, detail="DataFlow not found")
    dataflow.id = dataflow_id
    dataflow.organization_id = org_id
    return storage.save(dataflow)


@router.delete("/{org_id}/dataflows/{dataflow_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dataflow(org_id: str, dataflow_id: str):
    storage = get_dataflow_storage(org_id)
    if not storage.delete(dataflow_id):
        raise HTTPException(status_code=404, detail="DataFlow not found")


@router.post("/{org_id}/dataflows/{dataflow_id}/nodes", response_model=DataFlow)
async def add_node(org_id: str, dataflow_id: str, node: DataFlowNode):
    storage = get_dataflow_storage(org_id)
    dataflow = storage.get(dataflow_id)
    if not dataflow:
        raise HTTPException(status_code=404, detail="DataFlow not found")
    dataflow.nodes.append(node)
    return storage.save(dataflow)


@router.delete("/{org_id}/dataflows/{dataflow_id}/nodes/{node_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_node(org_id: str, dataflow_id: str, node_id: str):
    storage = get_dataflow_storage(org_id)
    dataflow = storage.get(dataflow_id)
    if not dataflow:
        raise HTTPException(status_code=404, detail="DataFlow not found")
    dataflow.nodes = [n for n in dataflow.nodes if n.id != node_id]
    dataflow.edges = [e for e in dataflow.edges if e.source != node_id and e.target != node_id]
    storage.save(dataflow)


@router.post("/{org_id}/dataflows/{dataflow_id}/edges", response_model=DataFlow)
async def add_edge(org_id: str, dataflow_id: str, edge: DataFlowEdge):
    storage = get_dataflow_storage(org_id)
    dataflow = storage.get(dataflow_id)
    if not dataflow:
        raise HTTPException(status_code=404, detail="DataFlow not found")
    dataflow.edges.append(edge)
    return storage.save(dataflow)


@router.delete("/{org_id}/dataflows/{dataflow_id}/edges/{edge_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_edge(org_id: str, dataflow_id: str, edge_id: str):
    storage = get_dataflow_storage(org_id)
    dataflow = storage.get(dataflow_id)
    if not dataflow:
        raise HTTPException(status_code=404, detail="DataFlow not found")
    dataflow.edges = [e for e in dataflow.edges if e.id != edge_id]
    storage.save(dataflow)
