"""
HRmod-files-modal

Modal-safe upload/download helpers for MiniMax H3 RefMod files.

This package is intended to be dropped into a ComfyUI custom nodes folder and
provides two custom nodes:

- HRmodUploadRefMod: accepts a browser uploaded .safetensors file and writes it
  into the active ComfyUI refmods folder so the built-in Load H3 RefMods node
  can see it later.

- HRmodDownloadRefMod: accepts a H3_REF_MODS bundle from Create H3 RefMod and
  writes a safetensors file to a temp/download directory, exposing a browser
  download URL.

The repo is intentionally minimal and cloud-friendly for Modal environments.
"""

from .upload_refmod import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
