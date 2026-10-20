try:
    from .upload_refmod import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS
except Exception as exc:
    print(f"[HRmod/files] Failed to import upload_refmod: {exc}")
    NODE_CLASS_MAPPINGS = {}
    NODE_DISPLAY_NAME_MAPPINGS = {}

try:
    from .modal_routes import register_modal_download_route, register_modal_upload_route
except Exception:
    register_modal_download_route = None
    register_modal_upload_route = None

try:
    from server import PromptServer
    if PromptServer.instance is not None:
        if register_modal_download_route is not None:
            register_modal_download_route(PromptServer.instance)
        if register_modal_upload_route is not None:
            register_modal_upload_route(PromptServer.instance)
except Exception:
    pass

WEB_DIRECTORY = "./web"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
