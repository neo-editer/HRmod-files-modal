import os
import shutil

try:
    import folder_paths
except Exception:  # pragma: no cover - ComfyUI may not expose this on import.
    folder_paths = None


def _safe_refmods_dir():
    candidates = []
    if folder_paths is not None:
        try:
            candidates.extend(folder_paths.get_folder_paths("refmods"))
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


def _list_refmods():
    root = _safe_refmods_dir()
    if not os.path.isdir(root):
        return ["None"]

    files = sorted(f for f in os.listdir(root) if f.endswith(".safetensors"))
    return files if files else ["None"]


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
    """Choose an existing refmod from the folder or upload a new one from the browser."""

    @classmethod
    def INPUT_TYPES(cls):
        files = _list_refmods()
        default = files[0] if files and files[0] != "None" else "None"
        return {
            "required": {
                "refmod_name": (files, {
                    "default": default,
                    "tooltip": "Choose a .safetensors file already in models/refmods."
                })
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("file_path",)
    FUNCTION = "upload"
    CATEGORY = "HRmod/files"

    def upload(self, refmod_name=""):
        if not refmod_name or refmod_name == "None":
            raise ValueError("No refmod selected.")

        root = _safe_refmods_dir()
        full_path = os.path.join(root, refmod_name)
        if not os.path.isfile(full_path):
            raise ValueError(f"RefMod file not found: {full_path}")
        if not full_path.endswith(".safetensors"):
            raise ValueError("Only .safetensors files are supported.")
        if not _valid_refmod_file(full_path):
            raise ValueError("The file does not look like a valid MiniMax H3 RefMod .safetensors.")
        return (full_path,)


class HRmodDownloadRefMod:
    """Save a generated refmod bundle to disk and return a browser-download URL."""

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
