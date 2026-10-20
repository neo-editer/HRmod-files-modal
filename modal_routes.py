import os

from aiohttp import web


def _safe_refmods_dir():
    candidates = []
    try:
        import folder_paths
        try:
            candidates.extend(folder_paths.get_folder_paths("refmods"))
        except Exception:
            pass
    except Exception:
        pass

    candidates.extend([
        os.path.join("/root/comfy/ComfyUI", "models", "refmods"),
        os.path.join("/root", "comfy", "ComfyUI", "models", "refmods"),
    ])

    for c in candidates:
        if c and os.path.isdir(c):
            return os.path.abspath(c)

    fallback = os.path.abspath(os.path.join("/root/comfy/ComfyUI", "models", "refmods"))
    os.makedirs(fallback, exist_ok=True)
    return fallback


def _refmods_roots():
    roots = []
    for base in [
        os.path.join("/root/comfy/ComfyUI", "models", "refmods", "_downloads"),
        os.path.join("/root", "comfy", "ComfyUI", "models", "refmods", "_downloads"),
        os.path.join("/root/comfy/ComfyUI", "models", "refmods"),
    ]:
        if os.path.isdir(base):
            roots.append(base)
    return roots


def register_modal_download_route(server):
    @server.routes.get("/refmods/download")
    async def refmods_download(request):
        filename = (request.query.get("file", "") or "").strip()
        if not filename:
            return web.Response(status=400, text="Missing file parameter")

        safe_name = os.path.basename(filename)
        for root in _refmods_roots():
            candidate = os.path.realpath(os.path.join(root, safe_name))
            if os.path.isfile(candidate):
                return web.FileResponse(
                    candidate,
                    headers={"Content-Disposition": f'attachment; filename="{os.path.basename(candidate)}"'}
                )

        return web.Response(status=404, text=f"File not found: {safe_name}")


def register_modal_upload_route(server):
    @server.routes.post("/hrmod/upload_refmod")
    async def hrmod_upload_refmod(request):
        data = await request.post()
        uploaded = data.get("file")
        if uploaded is None:
            return web.json_response({"error": "No file uploaded"}, status=400)

        filename = (getattr(uploaded, "filename", "") or "").strip()
        if not filename:
            return web.json_response({"error": "No filename"}, status=400)
        if not filename.endswith(".safetensors"):
            return web.json_response({"error": "Only .safetensors files are allowed"}, status=400)

        root = _safe_refmods_dir()
        os.makedirs(root, exist_ok=True)

        safe_name = os.path.basename(filename).replace("/", "_").replace("\\", "_")
        target = os.path.join(root, safe_name)
        idx = 2
        stem, ext = os.path.splitext(safe_name)
        while os.path.exists(target):
            target = os.path.join(root, f"{stem}_{idx}{ext}")
            idx += 1

        with open(target, "wb") as f:
            f.write(uploaded.file.read())

        return web.json_response({"status": "ok", "filename": os.path.basename(target)})
