import os

from aiohttp import web


def register_modal_download_route(server):
    """Expose a download route for the temp download directory created by HRmodDownloadRefMod."""
    @server.routes.get("/refmods/download")
    async def refmods_download(request):
        filename = request.query.get("file", "")
        if not filename:
            return web.Response(status=400, text="Missing file parameter")

        downloads = []
        base_roots = [
            os.path.join("/root/comfy/ComfyUI", "models", "refmods", "_downloads"),
            os.path.join("/root", "comfy", "ComfyUI", "models", "refmods", "_downloads"),
        ]
        for root in base_roots:
            if os.path.isdir(root):
                downloads.append(root)

        if not downloads:
            return web.Response(status=404, text="No refmod download directory found")

        for root in downloads:
            candidate = os.path.join(root, filename)
            if os.path.isfile(candidate):
                return web.FileResponse(candidate, headers={"Content-Disposition": f'attachment; filename="{os.path.basename(filename)}"'})

        return web.Response(status=404, text="File not found")
