import os

from aiohttp import web


def register_modal_download_route(server):
    @server.routes.get("/refmods/download")
    async def refmods_download(request):
        filename = request.query.get("file", "")
        if not filename:
            return web.Response(status=400, text="Missing file parameter")

        roots = []
        for base in [
            os.path.join("/root/comfy/ComfyUI", "models", "refmods", "_downloads"),
            os.path.join("/root", "comfy", "ComfyUI", "models", "refmods", "_downloads"),
            os.path.join("/root/comfy/ComfyUI", "models", "refmods"),
        ]:
            if os.path.isdir(base):
                roots.append(base)

        for root in roots:
            candidate = os.path.join(root, filename)
            if os.path.isfile(candidate):
                return web.FileResponse(
                    candidate,
                    headers={"Content-Disposition": f'attachment; filename="{os.path.basename(filename)}"'}
                )

        return web.Response(status=404, text=f"File not found: {filename}")
