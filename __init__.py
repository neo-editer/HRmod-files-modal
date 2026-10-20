import os

from .upload_refmod import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS
from .modal_routes import register_modal_download_route

try:
    from server import PromptServer
    if PromptServer.instance is not None:
        register_modal_download_route(PromptServer.instance)
except Exception:
    pass

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
