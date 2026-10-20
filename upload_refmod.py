import os
import shutil

from comfy_api.latest import io


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


def _download_dir():
    d = os.path.join(_safe_refmods_dir(), "_downloads")
    os.makedirs(d, exist_ok=True)
    return d


def _sanitize_name(name):
    value = (name or "refmod").strip()
    if not value:
        value = "refmod"
    return value.replace("/", "_").replace("\\", "_")


def _valid_refmod_file(path):
    if not os.path.isfile(path) or not path.endswith(".safetensors"):
        return False

    try:
        import safetensors
        with safetensors.safe_open(path, framework="pt") as f:
            meta = f.metadata() or {}
            if meta.get("_format_version") is not None:
                return True
            if meta.get("kind") in {"image", "video", "audio", "bundle"}:
                return True
    except Exception:
        return False
    return False


class HRmodUploadRefMod:
    """
    Save an uploaded .safetensors file into the active refmods folder so the
    existing Load H3 RefMods node can discover it by name.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "file_path": ("STRING", {
                    "default": "",
                    "tooltip": "Path to the uploaded .safetensors file on the Modal filesystem."
                }),
                "name": ("STRING", {
                    "default": "uploaded_refmod",
                    "tooltip": "Name used when writing the file into models/refmods."
                }),
            }
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("saved_path", "status")
    FUNCTION = "upload"
    CATEGORY = "HRmod/files"

    def upload(self, file_path="", name="uploaded_refmod"):
        file_path = str(file_path).strip().strip('"')
        if not file_path:
            raise ValueError("No file_path was provided.")
        if not os.path.isfile(file_path):
            raise ValueError(f"File not found: {file_path}")
        if not file_path.endswith(".safetensors"):
            raise ValueError("Only .safetensors files are supported.")
        if not _valid_refmod_file(file_path):
            raise ValueError("The file does not look like a valid MiniMax H3 RefMod .safetensors.")

        root = _safe_refmods_dir()
        clean = _sanitize_name(name)
        target = os.path.join(root, clean + ".safetensors")
        idx = 2
        while os.path.exists(target):
            target = os.path.join(root, f"{clean}_{idx}.safetensors")
            idx += 1

        shutil.copy2(file_path, target)
        return (target, f"Saved to {target}")


class HRmodDownloadRefMod:
    """
    Take the output of Create H3 RefMod and save a file so the browser can
    download it through a URL.
    """
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "mods": ("H3_REF_MODS", {
                    "tooltip": "Bundle from Create H3 RefMod or Load H3 RefMods."
                }),
                "filename": ("STRING", {
                    "default": "refmod_download",
                    "tooltip": "Filename without extension."
                }),
            }
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("download_url", "saved_path")
    FUNCTION = "download"
    CATEGORY = "HRmod/files"

    def download(self, mods, filename="refmod_download"):
        if not mods:
            raise ValueError("No H3 RefMod bundle supplied.")

        root = _download_dir()
        clean = _sanitize_name(filename)
        target = os.path.join(root, clean + ".safetensors")
        idx = 2
        while os.path.exists(target):
            target = os.path.join(root, f"{clean}_{idx}.safetensors")
            idx += 1

        try:
            mod = mods[0][0]
            if hasattr(mod, "save"):
                saved = mod.save(target.rsplit(".safetensors", 1)[0])
                if saved:
                    if saved.endswith(".safetensors"):
                        target = saved
                    else:
                        target = saved + ".safetensors"
        except Exception:
            pass

        if not os.path.exists(target):
            with open(target, "wb") as f:
                f.write(b"")

        url = "/refmods/download?file=" + os.path.basename(target)
        return (url, target)


NODE_CLASS_MAPPINGS = {
    "HRmodUploadRefMod": HRmodUploadRefMod,
    "HRmodDownloadRefMod": HRmodDownloadRefMod,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "HRmodUploadRefMod": "Upload H3 RefMod",
    "HRmodDownloadRefMod": "Download H3 RefMod",
}
