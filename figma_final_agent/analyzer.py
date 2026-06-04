from __future__ import annotations

import re
from typing import Any

from .models import DesignTokenSet, FigmaFileResult, StructurePlan, StyleResult


def _walk_nodes(node: dict[str, Any]) -> list[dict[str, Any]]:
    nodes = [node]
    for child in node.get("children", []):
        nodes.extend(_walk_nodes(child))
    return nodes


def _safe_token_name(prefix: str, name: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "-", name.strip().lower()).strip("-")
    return f"--{prefix}-{value or 'default'}"


def _paint_to_hex(paint: dict[str, Any]) -> str | None:
    color = paint.get("color")
    if not color:
        return None
    red = round(color.get("r", 0) * 255)
    green = round(color.get("g", 0) * 255)
    blue = round(color.get("b", 0) * 255)
    return f"#{red:02x}{green:02x}{blue:02x}"


def extract_design_tokens(figma_file: FigmaFileResult, style_result: StyleResult) -> DesignTokenSet:
    colors: dict[str, str] = {}
    typography: dict[str, str] = {
        "--font-body": "Inter, Arial, sans-serif",
        "--font-size-body": "16px",
        "--line-height-body": "1.5",
    }
    spacing: dict[str, str] = {
        "--spacing-xs": "4px",
        "--spacing-sm": "8px",
        "--spacing-md": "16px",
        "--spacing-lg": "24px",
        "--spacing-xl": "32px",
    }
    shadows: dict[str, str] = {"--shadow-card": "0 12px 32px rgba(15, 23, 42, 0.12)"}
    radii: dict[str, str] = {"--radius-sm": "4px", "--radius-md": "8px", "--radius-lg": "12px"}

    for style_id, style in style_result.styles.items():
        name = style.get("name", style_id)
        style_type = style.get("style_type", style.get("styleType", "")).lower()
        if "fill" in style_type or "color" in style_type:
            colors[_safe_token_name("color", name)] = "#000000"
        if "text" in style_type:
            typography[_safe_token_name("font-size", name)] = "16px"
        if "effect" in style_type:
            shadows[_safe_token_name("shadow", name)] = "0 8px 24px rgba(15, 23, 42, 0.12)"

    for node in _walk_nodes(figma_file.document):
        for paint in node.get("fills", []) or []:
            if paint.get("visible", True) and paint.get("type") == "SOLID":
                hex_value = _paint_to_hex(paint)
                if hex_value:
                    colors.setdefault(_safe_token_name("color", node.get("name", "fill")), hex_value)
        style = node.get("style", {})
        if node.get("type") == "TEXT" and style:
            font_size = style.get("fontSize")
            line_height = style.get("lineHeightPx")
            if font_size:
                typography.setdefault(_safe_token_name("font-size", node.get("name", "text")), f"{round(font_size)}px")
            if line_height:
                typography.setdefault(_safe_token_name("line-height", node.get("name", "text")), f"{round(line_height)}px")
        if "cornerRadius" in node:
            radii.setdefault(_safe_token_name("radius", node.get("name", "node")), f"{round(node['cornerRadius'])}px")

    colors.setdefault("--color-bg", "#ffffff")
    colors.setdefault("--color-text", "#111827")
    colors.setdefault("--color-primary", "#2563eb")
    colors.setdefault("--color-surface", "#f8fafc")
    return DesignTokenSet(success=True, colors=colors, typography=typography, spacing=spacing, shadows=shadows, radii=radii)


def build_structure_plan(figma_file: FigmaFileResult, tokens: DesignTokenSet) -> StructurePlan:
    nodes = _walk_nodes(figma_file.document)
    frames = [node for node in nodes if node.get("type") in {"FRAME", "COMPONENT", "INSTANCE"}]
    texts = [node for node in nodes if node.get("type") == "TEXT"]
    image_nodes = [node for node in nodes if node.get("type") in {"VECTOR", "BOOLEAN_OPERATION"} or node.get("fills")]

    pages_sections = [node.get("name", "Untitled Section") for node in frames[:10]] or [figma_file.name or "Main Page"]
    components = [node.get("name", "Component") for node in frames if node.get("type") in {"COMPONENT", "INSTANCE"}][:12]
    if not components:
        components = ["site-header", "content-section", "cta-card", "site-footer"]

    assets = [node.get("id", "") for node in image_nodes if node.get("id")][:20]
    breakpoints = []
    for node in frames:
        width = node.get("absoluteBoundingBox", {}).get("width")
        if width:
            breakpoints.append(f"{round(width)}px")
    breakpoints = sorted(set(breakpoints), key=lambda item: int(item.replace("px", "")))[:6] or ["375px", "768px", "1200px"]

    interactions = []
    lowered_names = " ".join(node.get("name", "").lower() for node in nodes)
    if any(word in lowered_names for word in ["modal", "dialog", "popup"]):
        interactions.append("modal")
    if any(word in lowered_names for word in ["dropdown", "menu", "select"]):
        interactions.append("dropdown")
    if any(word in lowered_names for word in ["carousel", "slider"]):
        interactions.append("carousel")
    interactions.append("navigation")

    warnings = []
    if not texts:
        warnings.append("No text nodes found; generated copy will use section names.")
    if not assets:
        warnings.append("No exportable asset nodes identified.")

    css_variables = list(tokens.colors) + list(tokens.typography) + list(tokens.spacing) + list(tokens.shadows) + list(tokens.radii)
    return StructurePlan(
        success=True,
        pages_sections=pages_sections,
        components=components,
        assets=assets,
        css_variables=css_variables,
        interactions=interactions,
        breakpoints=breakpoints,
        warnings=warnings,
    )

