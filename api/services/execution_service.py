import re
import uuid
import time
import os
from typing import List, Optional, Dict, Any
from datetime import datetime

from api.models import (
    Organization, Role, Task, DataFlow, DataFlowNode, DataFlowEdge,
    NodeType, ExecutionMode
)
from api.services.storage import StorageService
from api.services.rag_service import RAGService
from api.services.openclaw_executor import OpenClawExecutor
from pydantic import BaseModel
from api.models.rag_models import RAGQuery


class ExecuteRequest(BaseModel):
    input_data: Dict[str, Any]
    dataflow_id: Optional[str] = None
    input_role_id: Optional[str] = None


class NodeResult(BaseModel):
    node_id: str
    role_id: Optional[str]
    task_id: Optional[str]
    output: Dict[str, Any]
    error: Optional[str]
    execution_time_ms: int


class ExecutionResult(BaseModel):
    execution_id: str
    status: str
    node_results: List[NodeResult]
    final_output: Dict[str, Any]


class ExecutionService:
    def __init__(self):
        self.storage = StorageService[Organization]("data/organizations", Organization)
        self.role_storage = StorageService[Role]("data/roles", Role)
        self.rag_service = RAGService()
        self.executor = OpenClawExecutor()

    def execute_workflow(
        self,
        organization_id: str,
        input_data: dict,
        dataflow_id: Optional[str] = None,
        input_role_id: Optional[str] = None
    ) -> ExecutionResult:
        execution_id = str(uuid.uuid4())
        start_time = time.time()
        node_results = []
        final_output = {}

        org = self.storage.get(organization_id)
        if not org:
            return ExecutionResult(
                execution_id=execution_id,
                status="failed",
                node_results=[],
                final_output={"error": "Organization not found"}
            )

        dataflow = self._load_dataflow(organization_id, dataflow_id)
        if not dataflow:
            return ExecutionResult(
                execution_id=execution_id,
                status="failed",
                node_results=[],
                final_output={"error": "DataFlow not found"}
            )

        try:
            execution_order = self.topological_sort(dataflow.nodes, dataflow.edges)
        except ValueError as e:
            return ExecutionResult(
                execution_id=execution_id,
                status="failed",
                node_results=[],
                final_output={"error": f"Cycle detected: {str(e)}"}
            )

        node_outputs: Dict[str, dict] = {}
        node_context: Dict[str, Any] = {"input_data": input_data}

        for node_id in execution_order:
            node = self._find_node(dataflow.nodes, node_id)
            if not node:
                continue

            node_start = time.time()

            try:
                if node.type == NodeType.INPUT:
                    result = self._execute_input_node(node, input_data, node_context)
                elif node.type == NodeType.ROLE:
                    result = self._execute_role_node(
                        node, org, node_context, node_outputs, dataflow.edges, input_role_id
                    )
                elif node.type == NodeType.TASK:
                    result = self._execute_task_node(
                        node, org, node_context, node_outputs, dataflow.edges
                    )
                elif node.type == NodeType.KNOWLEDGE:
                    result = self._execute_knowledge_node(node, org, node_context)
                elif node.type == NodeType.OUTPUT:
                    result = self._execute_output_node(node, node_outputs, dataflow.edges)
                else:
                    result = {"error": f"Unknown node type: {node.type}"}
            except Exception as e:
                result = {"error": str(e)}

            execution_time = int((time.time() - node_start) * 1000)

            node_result = NodeResult(
                node_id=node_id,
                role_id=node.ref_id if node.type == NodeType.ROLE else None,
                task_id=node.ref_id if node.type == NodeType.TASK else None,
                output=result,
                error=result.get("error"),
                execution_time_ms=execution_time
            )
            node_results.append(node_result)

            node_outputs[node_id] = result

            if node.type == NodeType.OUTPUT and "output" in result:
                final_output = result["output"]

        has_errors = any(nr.error for nr in node_results)

        status = "completed" if not has_errors else "partial" if node_results else "failed"

        return ExecutionResult(
            execution_id=execution_id,
            status=status,
            node_results=node_results,
            final_output=final_output
        )

    def _load_dataflow(self, org_id: str, dataflow_id: Optional[str]) -> Optional[DataFlow]:
        if not dataflow_id:
            dataflow_storage = StorageService[DataFlow](
                f"data/organizations/{org_id}/dataflows", DataFlow
            )
            dataflows = dataflow_storage.list()
            if dataflows:
                return dataflows[0]
            return None
        else:
            dataflow_storage = StorageService[DataFlow](
                f"data/organizations/{org_id}/dataflows", DataFlow
            )
            return dataflow_storage.get(dataflow_id)

    def topological_sort(self, nodes: List[DataFlowNode], edges: List[DataFlowEdge]) -> List[str]:
        adjacency: Dict[str, List[str]] = {n.id: [] for n in nodes}
        in_degree: Dict[str, int] = {n.id: 0 for n in nodes}

        for edge in edges:
            if edge.source in adjacency and edge.target in adjacency:
                adjacency[edge.source].append(edge.target)
                in_degree[edge.target] += 1

        queue = [node_id for node_id, degree in in_degree.items() if degree == 0]
        result = []

        while queue:
            current = queue.pop(0)
            result.append(current)

            for neighbor in adjacency[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(result) != len(nodes):
            raise ValueError("Circular dependency detected in dataflow")

        return result

    def _find_node(self, nodes: List[DataFlowNode], node_id: str) -> Optional[DataFlowNode]:
        for node in nodes:
            if node.id == node_id:
                return node
        return None

    def _execute_input_node(self, node: DataFlowNode, input_data: dict, context: Dict[str, Any]) -> dict:
        return {"output": input_data, "node_label": node.label}

    def _execute_role_node(
        self,
        node: DataFlowNode,
        org: Organization,
        context: Dict[str, Any],
        node_outputs: Dict[str, dict],
        edges: List[DataFlowEdge],
        input_role_id: Optional[str]
    ) -> dict:
        if not node.ref_id:
            return {"error": "Role node has no ref_id"}

        role = self.role_storage.get(node.ref_id)
        if not role:
            return {"error": f"Role not found: {node.ref_id}"}

        agent_path = os.path.join("agents", role.name.lower().replace(" ", "_"))
        if not os.path.exists(agent_path):
            return {
                "error": f"Agent not deployed. Please deploy organization first.",
                "role_id": role.id,
                "role_name": role.name
            }

        task_storage = StorageService[Task](
            f"data/organizations/{org.id}/tasks", Task
        )
        all_tasks = task_storage.list()
        role_tasks = [t for t in all_tasks if t.assigned_role_id == role.id]

        input_mapping = self._get_input_mapping(node.id, edges, node_outputs)
        prompt_context = self._build_prompt_context(role, role_tasks, input_mapping, org.id, context)

        try:
            result = self.executor.execute_role(
                role_name=role.name,
                input_data=input_mapping,
                context={"org_id": org.id, "tasks": role_tasks}
            )
            output = result
        except Exception as e:
            output = {"error": str(e), "role_name": role.name}

        return {
            "role_id": role.id,
            "role_name": role.name,
            "output": output,
            "tasks_executed": [t.id for t in role_tasks],
            "node_label": node.label
        }

    def _execute_task_node(
        self,
        node: DataFlowNode,
        org: Organization,
        context: Dict[str, Any],
        node_outputs: Dict[str, dict],
        edges: List[DataFlowEdge]
    ) -> dict:
        if not node.ref_id:
            return {"error": "Task node has no ref_id"}

        task_storage = StorageService[Task](
            f"data/organizations/{org.id}/tasks", Task
        )
        task = task_storage.get(node.ref_id)
        if not task:
            return {"error": f"Task not found: {node.ref_id}"}

        input_mapping = self._get_input_mapping(node.id, edges, node_outputs)

        prompt = task.prompt or "Execute the task"
        if input_mapping:
            prompt = self._inject_variables(prompt, input_mapping)

        return {
            "task_id": task.id,
            "task_name": task.name,
            "output": {"result": f"Task '{task.name}' executed", "prompt_used": prompt},
            "node_label": node.label
        }

    def _execute_knowledge_node(self, node: DataFlowNode, org: Organization, context: Dict[str, Any]) -> dict:
        query_text = context.get("input_data", {}).get("user_input", "")

        rag_query = RAGQuery(
            query=query_text,
            organization_id=org.id,
            top_k=3,
            doc_types=[]
        )

        rag_result = self.rag_service.query(rag_query)

        knowledge_content = []
        for r in rag_result.results:
            knowledge_content.append({
                "content": r.content,
                "source": r.metadata.get("title", "Unknown"),
                "score": r.score
            })

        return {
            "output": {"knowledge": knowledge_content},
            "query": query_text,
            "node_label": node.label
        }

    def _execute_output_node(
        self,
        node: DataFlowNode,
        node_outputs: Dict[str, dict],
        edges: List[DataFlowEdge]
    ) -> dict:
        input_edges = [e for e in edges if e.target == node.id]

        collected_outputs = {}
        for edge in input_edges:
            source_output = node_outputs.get(edge.source, {})
            mapped_data = self.apply_data_mapping(edge.data_mapping, source_output)
            collected_outputs.update(mapped_data)

        return {
            "output": collected_outputs,
            "node_label": node.label
        }

    def _get_input_mapping(
        self,
        node_id: str,
        edges: List[DataFlowEdge],
        node_outputs: Dict[str, dict]
    ) -> dict:
        input_edges = [e for e in edges if e.target == node_id]

        mapped_data = {}
        for edge in input_edges:
            source_output = node_outputs.get(edge.source, {})
            edge_mapping = self.apply_data_mapping(edge.data_mapping, source_output)
            mapped_data.update(edge_mapping)

        return mapped_data

    def apply_data_mapping(self, mapping: dict, source_output: dict) -> dict:
        result = {}

        for target_key, source_expr in mapping.items():
            if isinstance(source_expr, str):
                value = self._extract_value(source_expr, source_output)
                result[target_key] = value
            else:
                result[target_key] = source_expr

        return result

    def _extract_value(self, expr: str, source_output: dict) -> Any:
        pattern = r'\{\{([^}]+)\}\}'
        match = re.match(pattern, expr.strip())

        if not match:
            return expr

        path = match.group(1).strip()
        parts = path.split('.')

        if parts[0] == 'source':
            parts = parts[1:]

        current = source_output
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return None

        return current

    def _inject_variables(self, template: str, context: dict) -> str:
        result = template

        for key, value in context.items():
            placeholder = f"{{{{{key}}}}}"
            result = result.replace(placeholder, str(value))

        return result

    def _build_prompt_context(
        self,
        role: Role,
        tasks: List[Task],
        input_data: dict,
        org_id: str,
        context: Dict[str, Any]
    ) -> str:
        prompt_parts = []

        if role.identity_template:
            prompt_parts.append(f"## Identity\n{role.identity_template}")

        if role.soul_template:
            prompt_parts.append(f"## Soul\n{role.soul_template}")

        if role.responsibilities:
            prompt_parts.append(f"## Responsibilities\n" + "\n".join(f"- {r}" for r in role.responsibilities))

        if tasks:
            prompt_parts.append("## Assigned Tasks")
            for task in tasks:
                prompt_parts.append(f"- **{task.name}**: {task.description or 'No description'}")

        user_input = input_data.get("user_input", context.get("input_data", {}).get("user_input", ""))
        if user_input:
            prompt_parts.append(f"\n## User Input\n{user_input}")

        knowledge_context = self._get_knowledge_context(org_id, user_input)
        if knowledge_context:
            prompt_parts.append(f"\n## Relevant Knowledge\n{knowledge_context}")

        return "\n\n".join(prompt_parts)

    def _get_knowledge_context(self, org_id: str, query: str) -> str:
        if not query:
            return ""

        rag_query = RAGQuery(
            query=query,
            organization_id=org_id,
            top_k=3,
            doc_types=[]
        )

        result = self.rag_service.query(rag_query)

        if not result.results:
            return ""

        context_parts = ["Based on the knowledge base:"]
        for r in result.results:
            context_parts.append(f"\n- {r.content}")

        return "\n".join(context_parts)

    def _simulate_agent_execution(self, role: Role, prompt_context: str, input_data: dict) -> dict:
        return {
            "status": "completed",
            "role_name": role.name,
            "prompt_length": len(prompt_context),
            "input_received": input_data,
            "result": f"Agent '{role.name}' processed the request successfully",
            "timestamp": datetime.now().isoformat()
        }