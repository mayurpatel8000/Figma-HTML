from __future__ import annotations

from figma_final_agent.project import create_project_folder
from figma_final_agent.tools.figma import get_figma_file, get_figma_images, get_figma_styles
from figma_final_agent.tools.files import read_file, write_file
from figma_final_agent.url_parser import parse_figma_url


TOOL_REGISTRY = {
    "parse_figma_url": parse_figma_url,
    "create_project_folder": create_project_folder,
    "get_figma_file": get_figma_file,
    "get_figma_images": get_figma_images,
    "get_figma_styles": get_figma_styles,
    "read_file": read_file,
    "write_file": write_file,
}
