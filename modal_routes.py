import os

from aiohttp import web


def _input_dir():
    try:
        import folder_paths
        try:
            return os.path.abspath(folder_paths.get_input_directory())
        except Exception:
            pass
    except Exception:
        pass

    for candidate in [
        "/root/comfy/ComfyUI/input",
        "/root/comfy/ComfyUI/input/",
        "/root/comfy/ComfyUI",
    ]:
        if os.path.isdir(candidate):
            return os.path.abspath(candidate)

    fallback = os.path.abspath(os.path.join("/root/comfy/ComfyUI", "input"))
    os.makedirs(fallback, exist_ok=True)
    return fallback


def _images_root():
    root = os.path.abspath(os.path.join(_input_dir(), "hrmod_images"))
    os.makedirs(root, exist_ok=True)
    return root


def _bucket_dir(name):
    root = _images_root()
    clean = (name or "my_refmod_images").strip().replace("/", "_").replace("\\", "_")
    if not clean:
        clean = "my_refmod_images"
    target = os.path.abspath(os.path.join(root, clean))
    os.makedirs(target, exist_ok=True)
    return target


def _list_buckets():
    root = _images_root()
    if not os.path.isdir(root):
        return ["None"]
    folders = sorted(d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d)))
    return folders or ["None"]


def _list_images(bucket_name):
    if not bucket_name or bucket_name == "None":
        return []
    path = _bucket_dir(bucket_name)
    return sorted(fn for fn in os.listdir(path) if os.path.isfile(os.path.join(path, fn)))


def register_modal_image_upload_route(server):
    @server.routes.post("/hrmod/upload_images")
    async def hrmod_upload_images(request):
        data = await request.post()
        folder_name = (data.get("folder_name") or "my_refmod_images").strip()
        files = data.getall("files") if hasattr(data, "getall") else []
        if not files:
            return web.json_response({"error": "No files uploaded"}, status=400)

        target_dir = _bucket_dir(folder_name)
        saved = []
        for item in files:
            filename = (getattr(item, "filename", "") or "").strip()
            if not filename:
                continue
            if os.path.sep in filename:
                filename = os.path.basename(filename)
            if not filename:
                continue
            if not filename.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tif", ".tiff")):
                continue
            target = os.path.join(target_dir, filename.replace("/", "_").replace("\\", "_"))
            idx = 2
            stem, ext = os.path.splitext(target)
            while os.path.exists(target):
                target = os.path.join(target_dir, f"{stem}_{idx}{ext}")
                idx += 1
            with open(target, "wb") as f:
                f.write(item.file.read())
            saved.append(os.path.basename(target))

        return web.json_response({
            "status": "ok",
            "folder": os.path.basename(target_dir),
            "path": target_dir,
            "files": saved,
        })

    @server.routes.post("/hrmod/remove_image")
    async def hrmod_remove_image(request):
        data = await request.post()
        folder_name = (data.get("folder_name") or "my_refmod_images").strip()
        filename = (data.get("filename") or "").strip()
        if not folder_name or not filename:
            return web.json_response({"error": "Missing folder_name or filename"}, status=400)

        target_dir = _bucket_dir(folder_name)
        target = os.path.join(target_dir, os.path.basename(filename))
        if os.path.isfile(target):
            os.remove(target)
            return web.json_response({"status": "ok", "removed": os.path.basename(filename)})
        return web.json_response({"error": "File not found"}, status=404)

    @server.routes.get("/hrmod/list_images")
    async def hrmod_list_images(request):
        folder_name = (request.query.get("folder_name") or "my_refmod_images").strip()
        return web.json_response({"files": _list_images(folder_name), "folder": folder_name})

