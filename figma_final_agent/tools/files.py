from __future__ import annotations

from pathlib import Path

from figma_final_agent.models import ReadFileResult, WriteFileResult


def read_file(path: str) -> ReadFileResult:
    try:
        file_path = Path(path)
        return ReadFileResult(success=True, path=str(file_path), content=file_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return ReadFileResult(success=False, error=str(exc), path=path)


def write_file(path: str, content: str) -> WriteFileResult:
    try:
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        return WriteFileResult(success=True, path=str(file_path))
    except Exception as exc:
        return WriteFileResult(success=False, error=str(exc), path=path)

