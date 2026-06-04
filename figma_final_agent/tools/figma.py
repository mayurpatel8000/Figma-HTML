from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from figma_final_agent.models import FigmaFileResult, ImageExportResult, StyleResult


FIGMA_API = "https://api.figma.com/v1"


def _request_json(url: str, token: str) -> dict:
    request = Request(url, headers={"X-Figma-Token": token})
    with urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def get_figma_file(file_key: str, token: str) -> FigmaFileResult:
    try:
        payload = _request_json(f"{FIGMA_API}/files/{file_key}", token)
        return FigmaFileResult(
            success=True,
            file_key=file_key,
            name=payload.get("name", "Figma Project"),
            document=payload.get("document", {}),
            components=payload.get("components", {}),
            schema_version=payload.get("schemaVersion"),
        )
    except HTTPError as exc:
        return FigmaFileResult(success=False, error=f"Figma file request failed: HTTP {exc.code}", file_key=file_key)
    except URLError as exc:
        return FigmaFileResult(success=False, error=f"Figma API unreachable: {exc.reason}", file_key=file_key)
    except Exception as exc:
        return FigmaFileResult(success=False, error=str(exc), file_key=file_key)


def get_figma_styles(file_key: str, token: str) -> StyleResult:
    try:
        payload = _request_json(f"{FIGMA_API}/files/{file_key}/styles", token)
        styles_data = payload.get("meta", {}).get("styles", [])
        if isinstance(styles_data, list):
            styles_dict = {s.get("key", s.get("name", str(i))): s for i, s in enumerate(styles_data)}
        else:
            styles_dict = styles_data
        return StyleResult(success=True, styles=styles_dict)
    except HTTPError as exc:
        return StyleResult(success=False, error=f"Figma styles request failed: HTTP {exc.code}")
    except URLError as exc:
        return StyleResult(success=False, error=f"Figma API unreachable: {exc.reason}")
    except Exception as exc:
        return StyleResult(success=False, error=str(exc))


def get_figma_images(file_key: str, node_ids: list[str], token: str) -> ImageExportResult:
    try:
        if not node_ids:
            return ImageExportResult(success=True, images={})
        query = urlencode({"ids": ",".join(node_ids), "format": "svg"})
        payload = _request_json(f"{FIGMA_API}/images/{file_key}?{query}", token)
        return ImageExportResult(success=True, images=payload.get("images", {}))
    except HTTPError as exc:
        return ImageExportResult(success=False, error=f"Figma image export failed: HTTP {exc.code}")
    except URLError as exc:
        return ImageExportResult(success=False, error=f"Figma API unreachable: {exc.reason}")
    except Exception as exc:
        return ImageExportResult(success=False, error=str(exc))