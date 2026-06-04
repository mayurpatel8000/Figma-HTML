from __future__ import annotations

from .models import Task, TaskPlan


def build_task_plan(figma_url: str, token: str, output_root: str) -> TaskPlan:
    return TaskPlan(
        request=figma_url,
        tasks=[
            Task(step=1, action="Parse Figma URL", tool="parse_figma_url", params={"figma_url": figma_url}),
            Task(step=2, action="Fetch Figma file", tool="get_figma_file", params={"token": token}, depends_on=1),
            Task(step=3, action="Fetch Figma styles", tool="get_figma_styles", params={"token": token}, depends_on=1),
            Task(step=4, action="Create project folder", tool="create_project_folder", params={"output_root": output_root}, depends_on=2),
            Task(step=5, action="Export Figma assets", tool="get_figma_images", params={"token": token}, depends_on=1),
        ],
    )

