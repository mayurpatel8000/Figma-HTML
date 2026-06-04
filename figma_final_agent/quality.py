from __future__ import annotations

import re

from .models import GeneratedFile, QualityCheckResult


HEX_COLOR = re.compile(r"#[0-9a-fA-F]{3,8}")


def check_generated_file(file: GeneratedFile) -> QualityCheckResult:
    warnings: list[str] = []
    content = file.content
    path = file.relative_path

    if path.endswith(".html"):
        if " style=" in content:
            warnings.append(f"{path}: inline style attribute found.")
        if "<main" not in content or "<section" not in content:
            warnings.append(f"{path}: semantic main/section structure missing.")
        if "data-component=" not in content:
            warnings.append(f"{path}: data-component attributes missing.")
    if path.endswith(".css"):
        stripped = re.sub(r":root\s*\{.*?\}", "", content, flags=re.DOTALL)
        if HEX_COLOR.search(stripped):
            warnings.append(f"{path}: hardcoded color found outside tokens.")
        if ":hover" not in content and "components.css" in path:
            warnings.append(f"{path}: hover states missing.")
        if ":focus" not in content and "components.css" in path:
            warnings.append(f"{path}: focus states missing.")
    if path.endswith(".js"):
        if "console.log" in content:
            warnings.append(f"{path}: console.log found.")
        if ".style." in content:
            warnings.append(f"{path}: inline JS style mutation found.")
        if "DOMContentLoaded" not in content and path == "js/main.js":
            warnings.append(f"{path}: DOMContentLoaded init missing.")
        if "data-component" not in content and "components/" in path:
            warnings.append(f"{path}: data attribute selection missing.")

    return QualityCheckResult(success=not warnings, warnings=warnings)


def check_generated_files(files: list[GeneratedFile]) -> QualityCheckResult:
    warnings: list[str] = []
    for file in files:
        warnings.extend(check_generated_file(file).warnings)
    return QualityCheckResult(success=not warnings, warnings=warnings)

