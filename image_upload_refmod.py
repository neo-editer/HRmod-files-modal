import os

try:
    import folder_paths
except Exception:  # pragma: no cover
    folder_paths = None


def _input_dir():
    if folder_paths is not None:
        try:
            return os.path.abspath(folder_paths.get_input_directory())
        except Exception:
            pass

    for candidate in [
        "/root/comfy/ComfyUI/input",
        "/root/comfy/ComfyUI/input/",
        "/root/comfy/ComfyUI",  # fallback safety
    ]:
        if os.path.isdir(candidate):
            return os.path.abspath(candidate)

    fallback = os.path.abspath(os.path.join("/root/comfy/ComfyUI", "input"))
    os.makedirs(fallback, exist_ok=True)
    return fallback


def _images_root():
    base = _input_dir()
    return os.path.abspath(os.path.join(base, "hrmod_images"))


def _ensure_image_bucket(bucket_name):
    root = _images_root()
    os.makedirs(root, exist_ok=True)
    target = os.path.abspath(os.path.join(root, bucket_name.strip().replace("/", "_").replace("\\", "_")))
    os.makedirs(target, exist_ok=True)
    return target


def _list_image_folders():
    root = _images_root()
    if not os.path.isdir(root):
        return ["None"]

    folders = sorted(d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d)))
    return folders or ["None"]


def _list_images_in_bucket(bucket_name):
    if not bucket_name or bucket_name == "None":
        return []

    path = _ensure_image_bucket(bucket_name)
    files = []
    for fn in sorted(os.listdir(path)):
        if os.path.isfile(os.path.join(path, fn)):
            files.append(fn)
    return files


class HRmodUploadImagesForRefMod:
    """Upload one or many images into a custom bucket inside ComfyUI's input folder."""

    @classmethod
    def INPUT_TYPES(cls):
        folders = _list_image_folders()
        default = folders[0] if folders and folders[0] != "None" else "my_refmod_images"
        return {
            "required": {
                "folder_name": ("STRING", {
                    "default": default,
                    "tooltip": "Name of the image folder to create under ComfyUI input/hrmod_images."
                }),
                "image_files": ("STRING", {
                    "default": "",
                    "tooltip": "The uploaded image filenames inside the chosen folder."
                }),
            }
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("folder_path", "images")
    FUNCTION = "upload_images"
    CATEGORY = "HRmod/files"

    def upload_images(self, folder_name="my_refmod_images", image_files=""):
        clean_name = (folder_name or "my_refmod_images").strip().replace("/", "_").replace("\\", "_")
        if not clean_name:
            clean_name = "my_refmod_images"

        target_dir = _ensure_image_bucket(clean_name)
        entries = []
        for item in (image_files or "").split("|"):
            item = item.strip()
            if item:
                entries.append(item)

        if not entries:
            files = _list_images_in_bucket(clean_name)
            entries = files

        return (target_dir, "|".join(entries))


NODE_CLASS_MAPPINGS = {
    "HRmodUploadImagesForRefMod": HRmodUploadImagesForRefMod,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "HRmodUploadImagesForRefMod": "Upload Images for HRefMod",
}
