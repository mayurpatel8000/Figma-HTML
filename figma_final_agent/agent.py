from __future__ import annotations

from pathlib import Path
from typing import Any

from .analyzer import build_structure_plan, extract_design_tokens
from .executor import PlanExecutor
from .generators import generate_project_files
from .models import AgentRunResult, FigmaFileResult, ImageExportResult, ProjectContext, StyleResult, ToolResult
from .planner import build_task_plan
from .quality import check_generated_files
from .tools.files import write_file


class FigmaFinalAgent:
    def __init__(self, max_iterations: int = 3) -> None:
        self.max_iterations = max_iterations
        self.executor = PlanExecutor()
        self.messages: list[dict[str, Any]] = []

    def _observe(self, phase: str, result: Any) -> None:
        payload = result.model_dump(mode="json") if hasattr(result, "model_dump") else result
        self.messages.append({"phase": phase, "observation": payload})

    def _request_approval(self, structure_plan: str) -> bool:
        print(structure_plan)
        response = input("Type yes to proceed, anything else to abort: ")
        return response.strip().lower() == "yes"

    def run(
        self,
        figma_url: str,
        token: str,
        output_root: str | Path,
        require_approval: bool = True,
        existing_file: str | None = None,
    ) -> AgentRunResult:
        if self.max_iterations < 3:
            return AgentRunResult(success=False, status="max_iterations_reached", error="max_iterations must be at least 3")

        plan = build_task_plan(figma_url=figma_url, token=token, output_root=str(output_root))

        try:
            if existing_file:
                existing = self.executor.tool_registry["read_file"](existing_file)
                self._observe("existing_file", existing)
                if not existing.success:
                    return AgentRunResult(success=False, status="error", error=existing.error, messages=self.messages)

            self.messages.append({"think": "Parse the Figma URL, fetch source data, and initialize project context."})
            plan, completed = self.executor.execute_until(plan, target_step=4)
            for step in range(1, 5):
                self._observe(f"step_{step}", completed.get(step) or plan.tasks[step - 1].result)

            failed_task = next((task for task in plan.tasks if task.step <= 4 and task.status == "failed"), None)
            if failed_task:
                error = getattr(failed_task.result, "error", "Task failed")
                return AgentRunResult(success=False, status="error", error=error, messages=self.messages)

            figma_file = completed[2]
            styles = completed[3]
            project = completed[4]
            if not isinstance(figma_file, FigmaFileResult) or not isinstance(styles, StyleResult) or not isinstance(project, ProjectContext):
                return AgentRunResult(success=False, status="error", error="Unexpected tool result type", messages=self.messages)

            self.messages.append({"think": "Analyze frames, components, assets, responsive widths, and design tokens."})
            tokens = extract_design_tokens(figma_file, styles)
            structure_plan = build_structure_plan(figma_file, tokens)
            self._observe("design_tokens", tokens)
            self._observe("structure_plan", structure_plan)

            if require_approval and not self._request_approval(structure_plan.to_markdown()):
                return AgentRunResult(
                    success=False,
                    status="aborted",
                    project_dir=str(project.project_dir or ""),
                    warnings=structure_plan.warnings,
                    messages=self.messages,
                )

            self.messages.append({"think": "Generate files, export assets, apply quality gates, and summarize."})
            plan.tasks[4].params["node_ids"] = structure_plan.assets
            executed_asset_task = self.executor.execute_task(plan.tasks[4], {1: completed[1]})
            asset_result = executed_asset_task.result if isinstance(executed_asset_task.result, ImageExportResult) else ImageExportResult(success=False)
            self._observe("assets", asset_result)

            files = generate_project_files(structure_plan, tokens, figma_file.document if figma_file else None)
            quality = check_generated_files(files)
            self._observe("quality", quality)
            # Proceed with writing files even if there are quality warnings
            # (warnings are informational only)

            files_created: list[str] = []
            failed_conversions: list[str] = []
            project_dir = Path(project.project_dir or output_root)
            for generated in files:
                write_result = write_file(str(project_dir / generated.relative_path), generated.content)
                self._observe(f"write_{generated.relative_path}", write_result)
                if write_result.success:
                    files_created.append(generated.relative_path)
                else:
                    failed_conversions.append(f"{generated.relative_path}: {write_result.error}")

            return AgentRunResult(
                success=not failed_conversions,
                status="completed" if not failed_conversions else "error",
                error="Quality or write failures occurred" if failed_conversions else None,
                project_dir=str(project_dir),
                files_created=files_created,
                components_extracted=structure_plan.components,
                design_token_count=tokens.count,
                breakpoints=structure_plan.breakpoints,
                interactions=structure_plan.interactions,
                assets_exported=len(asset_result.images),
                warnings=structure_plan.warnings + quality.warnings,
                failed_conversions=failed_conversions,
                messages=self.messages,
            )
        except Exception as exc:
            return AgentRunResult(success=False, status="error", error=str(exc), messages=self.messages)
