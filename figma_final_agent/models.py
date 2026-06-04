from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field


class ToolResult(BaseModel):
    success: bool
    error: str | None = None


class FigmaUrlInfo(ToolResult):
    file_key: str = ""
    node_id: str | None = None
    original_url: str = ""


class ProjectContext(ToolResult):
    file_key: str = ""
    node_id: str | None = None
    project_name: str = ""
    project_dir: Path | None = None


class FigmaFileResult(ToolResult):
    file_key: str = ""
    name: str = ""
    document: dict[str, Any] = Field(default_factory=dict)
    components: dict[str, Any] = Field(default_factory=dict)
    schema_version: int | None = None


class StyleResult(ToolResult):
    styles: dict[str, Any] = Field(default_factory=dict)


class ImageExportResult(ToolResult):
    images: dict[str, str] = Field(default_factory=dict)


class ReadFileResult(ToolResult):
    path: str = ""
    content: str = ""


class WriteFileResult(ToolResult):
    path: str = ""


class DesignTokenSet(ToolResult):
    colors: dict[str, str] = Field(default_factory=dict)
    typography: dict[str, str] = Field(default_factory=dict)
    spacing: dict[str, str] = Field(default_factory=dict)
    shadows: dict[str, str] = Field(default_factory=dict)
    radii: dict[str, str] = Field(default_factory=dict)

    @property
    def count(self) -> int:
        return sum(len(group) for group in [self.colors, self.typography, self.spacing, self.shadows, self.radii])


class StructurePlan(ToolResult):
    pages_sections: list[str] = Field(default_factory=list)
    components: list[str] = Field(default_factory=list)
    assets: list[str] = Field(default_factory=list)
    css_variables: list[str] = Field(default_factory=list)
    interactions: list[str] = Field(default_factory=list)
    breakpoints: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    def to_markdown(self) -> str:
        def line(label: str, values: list[str]) -> str:
            return f"- {label}: {', '.join(values) if values else 'None identified'}"

        return "\n".join(
            [
                "STRUCTURE PLAN:",
                line("Pages/Sections identified", self.pages_sections),
                line("Components to extract", self.components),
                line("Assets needed", self.assets),
                line("CSS variables needed", self.css_variables),
                line("JavaScript interactions needed", self.interactions),
                line("Responsive breakpoints", self.breakpoints),
            ]
        )


class GeneratedFile(BaseModel):
    relative_path: str
    content: str


class QualityCheckResult(ToolResult):
    warnings: list[str] = Field(default_factory=list)


class Task(BaseModel):
    step: int
    action: str
    tool: str
    params: dict[str, Any] = Field(default_factory=dict)
    depends_on: int | None = None
    status: Literal["pending", "running", "done", "failed"] = "pending"
    result: Any | None = None


class TaskPlan(BaseModel):
    request: str
    tasks: list[Task]
    approved: bool = False


class AgentRunResult(ToolResult):
    status: Literal["completed", "error", "aborted", "max_iterations_reached"] = "completed"
    project_dir: str = ""
    files_created: list[str] = Field(default_factory=list)
    components_extracted: list[str] = Field(default_factory=list)
    design_token_count: int = 0
    breakpoints: list[str] = Field(default_factory=list)
    interactions: list[str] = Field(default_factory=list)
    assets_exported: int = 0
    warnings: list[str] = Field(default_factory=list)
    failed_conversions: list[str] = Field(default_factory=list)
    messages: list[dict[str, Any]] = Field(default_factory=list)

