from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from figma_final_agent.agent import FigmaFinalAgent
from figma_final_agent.executor import PlanExecutor
from figma_final_agent.generators import generate_project_files
from figma_final_agent.models import (
    DesignTokenSet,
    FigmaFileResult,
    FigmaUrlInfo,
    ImageExportResult,
    StyleResult,
    StructurePlan,
    Task,
    TaskPlan,
    ToolResult,
)
from figma_final_agent.planner import build_task_plan
from figma_final_agent.project import create_project_folder
from figma_final_agent.quality import check_generated_files
from figma_final_agent.url_parser import parse_figma_url


class FigmaFinalAgentTests(unittest.TestCase):
    def test_default_max_iterations_is_three(self) -> None:
        self.assertEqual(FigmaFinalAgent().max_iterations, 3)

    def test_valid_figma_url_extracts_file_key_and_node_id(self) -> None:
        result = parse_figma_url("https://www.figma.com/design/ABC123/My-File?node-id=1%3A2")
        self.assertTrue(result.success)
        self.assertEqual(result.file_key, "ABC123")
        self.assertEqual(result.node_id, "1:2")

    def test_invalid_figma_url_returns_structured_error(self) -> None:
        result = parse_figma_url("https://example.com/design/ABC123")
        self.assertFalse(result.success)
        self.assertIn("figma.com", result.error or "")

    def test_each_project_folder_is_unique(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            first = create_project_folder(temp_dir, "Landing Page", "ABC123456")
            second = create_project_folder(temp_dir, "Landing Page", "ABC123456")
            self.assertTrue(first.success)
            self.assertTrue(second.success)
            self.assertNotEqual(first.project_dir, second.project_dir)
            self.assertTrue(str(second.project_dir).endswith("-2"))

    def test_planner_creates_required_tool_tasks(self) -> None:
        plan = build_task_plan("https://www.figma.com/file/ABC123/Test", "token", "./projects")
        self.assertEqual([task.tool for task in plan.tasks], [
            "parse_figma_url",
            "get_figma_file",
            "get_figma_styles",
            "create_project_folder",
            "get_figma_images",
        ])

    def test_executor_rejects_unknown_tool(self) -> None:
        plan = TaskPlan(request="x", tasks=[Task(step=1, action="Bad", tool="missing")])
        result = PlanExecutor(tool_registry={}).validate(plan)
        self.assertFalse(result.success)
        self.assertIn("Unknown tool", result.error or "")

    def test_executor_rejects_invalid_dependency(self) -> None:
        plan = TaskPlan(request="x", tasks=[Task(step=1, action="Bad", tool="ok", depends_on=99)])
        result = PlanExecutor(tool_registry={"ok": lambda: ToolResult(success=True)}).validate(plan)
        self.assertFalse(result.success)
        self.assertIn("depends", result.error or "")

    def test_executor_retries_failed_tool_once(self) -> None:
        calls = {"count": 0}

        def flaky_tool() -> ToolResult:
            calls["count"] += 1
            return ToolResult(success=calls["count"] == 2, error=None if calls["count"] == 2 else "try again")

        plan = TaskPlan(request="x", tasks=[Task(step=1, action="Retry", tool="flaky")])
        executor = PlanExecutor(tool_registry={"flaky": flaky_tool}, retry_count=1)
        executor.execute_until(plan, target_step=1)
        self.assertEqual(calls["count"], 2)
        self.assertEqual(plan.tasks[0].status, "done")

    def test_approval_rejection_writes_no_generated_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fake_file = FigmaFileResult(
                success=True,
                file_key="ABC123456",
                name="Test File",
                document={"id": "0:1", "name": "Home", "type": "DOCUMENT", "children": [{"id": "1:1", "name": "Hero", "type": "FRAME"}]},
            )
            registry = {
                "parse_figma_url": lambda figma_url: FigmaUrlInfo(success=True, file_key="ABC123456", original_url=figma_url),
                "get_figma_file": lambda file_key, token: fake_file,
                "get_figma_styles": lambda file_key, token: StyleResult(success=True),
                "create_project_folder": create_project_folder,
                "get_figma_images": lambda file_key, node_ids, token: ImageExportResult(success=True),
                "read_file": lambda path: ToolResult(success=True),
                "write_file": lambda path, content: ToolResult(success=True),
            }
            agent = FigmaFinalAgent()
            agent.executor = PlanExecutor(tool_registry=registry)
            with patch.object(agent, "_request_approval", return_value=False):
                result = agent.run("https://www.figma.com/file/ABC123456/Test", "token", temp_dir, require_approval=True)
            self.assertEqual(result.status, "aborted")
            self.assertFalse((Path(result.project_dir) / "index.html").exists())

    def test_generated_files_pass_quality_guards(self) -> None:
        plan = StructurePlan(
            success=True,
            pages_sections=["Hero", "Features"],
            components=["site-header", "feature-card"],
            css_variables=["--color-bg"],
            interactions=["navigation"],
            breakpoints=["375px", "768px"],
        )
        tokens = DesignTokenSet(
            success=True,
            colors={"--color-bg": "#ffffff", "--color-text": "#111827", "--color-primary": "#2563eb", "--color-surface": "#f8fafc"},
            typography={"--font-body": "Inter, Arial, sans-serif", "--font-size-body": "16px", "--line-height-body": "1.5"},
            spacing={"--spacing-sm": "8px", "--spacing-md": "16px", "--spacing-lg": "24px", "--spacing-xl": "32px"},
            shadows={"--shadow-card": "0 12px 32px rgba(15, 23, 42, 0.12)"},
            radii={"--radius-md": "8px"},
        )
        files = generate_project_files(plan, tokens)
        result = check_generated_files(files)
        self.assertTrue(result.success, result.warnings)


if __name__ == "__main__":
    unittest.main()
