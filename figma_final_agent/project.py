from __future__ import annotations

import re
from pathlib import Path

from .models import ProjectContext


def safe_project_slug(name: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", name.strip().lower()).strip("-")
    return slug or "figma-project"


def create_project_folder(output_root: str | Path, project_name: str, file_key: str, node_id: str | None = None) -> ProjectContext:
    try:
        root = Path(output_root)
        root.mkdir(parents=True, exist_ok=True)
        base_name = f"{safe_project_slug(project_name)}-{file_key[:8]}"
        candidate = root / base_name
        suffix = 2
        while candidate.exists():
            candidate = root / f"{base_name}-{suffix}"
            suffix += 1

        for subdir in [
            candidate,
            candidate / "css",
            candidate / "js",
            candidate / "js" / "components",
            candidate / "assets",
            candidate / "assets" / "images",
            candidate / "assets" / "icons",
        ]:
            subdir.mkdir(parents=True, exist_ok=True)

        return ProjectContext(
            success=True,
            file_key=file_key,
            node_id=node_id,
            project_name=project_name,
            project_dir=candidate,
        )
    except Exception as exc:
        return ProjectContext(success=False, error=str(exc), file_key=file_key, node_id=node_id, project_name=project_name)

