from __future__ import annotations

from urllib.parse import parse_qs, unquote, urlparse

from .models import FigmaUrlInfo


def parse_figma_url(figma_url: str) -> FigmaUrlInfo:
    try:
        parsed = urlparse(figma_url)
        if parsed.netloc not in {"www.figma.com", "figma.com"}:
            return FigmaUrlInfo(success=False, error="URL must be from figma.com", original_url=figma_url)

        parts = [part for part in parsed.path.split("/") if part]
        if len(parts) < 2 or parts[0] not in {"file", "design"}:
            return FigmaUrlInfo(success=False, error="URL must contain /file/<key> or /design/<key>", original_url=figma_url)

        file_key = parts[1].strip()
        if not file_key:
            return FigmaUrlInfo(success=False, error="Figma file key is missing", original_url=figma_url)

        query = parse_qs(parsed.query)
        node_id = query.get("node-id", [None])[0]
        if node_id:
            node_id = unquote(node_id)

        return FigmaUrlInfo(success=True, file_key=file_key, node_id=node_id, original_url=figma_url)
    except Exception as exc:
        return FigmaUrlInfo(success=False, error=str(exc), original_url=figma_url)

