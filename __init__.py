try:
    from .upload_refmod import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS
except Exception as exc:
    print(f"[HRmod/files] Failed to import upload_refmod: {exc}")
    NODE_CLASS_MAPPINGS = {}
    NODE_DISPLAY_NAME_MAPPINGS = {}

try:
    from .modal_routes import register_modal_download_route
except Exception:
    register_modal_download_route = None

try:
    from server import PromptServer
    if PromptServer.instance is not None and register_modal_download_route is not None:
        register_modal_download_route(PromptServer.instance)
except Exception:
    pass

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
