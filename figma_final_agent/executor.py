from __future__ import annotations

from collections.abc import Callable
from typing import Any

from pydantic import BaseModel

from .models import Task, TaskPlan, ToolResult
from .tools import TOOL_REGISTRY


def _model_dump(result: Any) -> dict[str, Any]:
    if isinstance(result, BaseModel):
        return result.model_dump()
    return result if isinstance(result, dict) else {}


def _inject_params(task: Task, completed: dict[int, Any]) -> dict[str, Any]:
    params = dict(task.params)
    if task.tool == "get_figma_file" or task.tool == "get_figma_styles":
        url_info = _model_dump(completed[task.depends_on or 1])
        params["file_key"] = url_info.get("file_key", "")
    if task.tool == "create_project_folder":
        figma_file = _model_dump(completed[2])
        url_info = _model_dump(completed[1])
        params["project_name"] = figma_file.get("name", "Figma Project")
        params["file_key"] = figma_file.get("file_key", url_info.get("file_key", ""))
        params["node_id"] = url_info.get("node_id")
    if task.tool == "get_figma_images":
        url_info = _model_dump(completed[1])
        params["file_key"] = url_info.get("file_key", "")
        params["node_ids"] = params.get("node_ids", [])
    return params


class PlanExecutor:
    def __init__(self, tool_registry: dict[str, Callable[..., Any]] | None = None, retry_count: int = 1) -> None:
        self.tool_registry = tool_registry or TOOL_REGISTRY
        self.retry_count = retry_count

    def validate(self, plan: TaskPlan) -> ToolResult:
        steps = {task.step for task in plan.tasks}
        for task in plan.tasks:
            if task.tool not in self.tool_registry:
                return ToolResult(success=False, error=f"Unknown tool: {task.tool}")
            if task.depends_on is not None and task.depends_on not in steps:
                return ToolResult(success=False, error=f"Task {task.step} depends on missing step {task.depends_on}")
        return ToolResult(success=True)

    def execute_task(self, task: Task, completed: dict[int, Any]) -> Task:
        if task.depends_on is not None and task.depends_on not in completed:
            task.status = "failed"
            task.result = ToolResult(success=False, error=f"Dependency {task.depends_on} not completed")
            return task

        task.status = "running"
        params = _inject_params(task, completed)
        tool = self.tool_registry[task.tool]
        result: Any = None
        for attempt in range(self.retry_count + 1):
            result = tool(**params)
            if getattr(result, "success", False):
                task.status = "done"
                task.result = result
                return task
            if attempt >= self.retry_count:
                break

        task.status = "failed"
        task.result = result
        return task

    def execute_until(self, plan: TaskPlan, target_step: int) -> tuple[TaskPlan, dict[int, Any]]:
        validation = self.validate(plan)
        if not validation.success:
            raise ValueError(validation.error)

        completed: dict[int, Any] = {}
        for task in plan.tasks:
            if task.step > target_step:
                break
            if task.status == "done":
                completed[task.step] = task.result
                continue
            executed = self.execute_task(task, completed)
            if executed.status == "failed":
                return plan, completed
            completed[task.step] = executed.result
        return plan, completed

