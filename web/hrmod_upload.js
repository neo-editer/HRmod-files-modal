import { app } from "../../../scripts/app.js";

function normalizeFileName(fileName) {
  const raw = String(fileName || "").replace(/\\/g, "/");
  const name = raw.split("/").pop() || raw;
  return name.replace(/^\.\//, "").trim();
}

function isSafetensorsFile(file) {
  const name = normalizeFileName(file?.webkitRelativePath || file?.name || file?.path || "");
  return name.toLowerCase().endsWith(".safetensors");
}

function uniqueSafetensorsFiles(files) {
  const seen = new Set();
  const unique = [];

  for (const file of files || []) {
    if (!file || !isSafetensorsFile(file)) continue;

    const name = normalizeFileName(file.webkitRelativePath || file.name || file.path || "");
    const key = name.toLowerCase();
    if (seen.has(key)) continue;

    seen.add(key);
    unique.push(file);
  }

  return unique;
}

const DROPZONE_MIN_H = 96;

app.registerExtension({
  name: "HRmod.UploadButton",
  async beforeRegisterNodeDef(nodeType, nodeData, app) {
    if (nodeData.name !== "HRmodUploadRefMod") return;

    nodeType.canvasOnly = true;

    const onNodeCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function () {
      onNodeCreated?.apply(this, arguments);

      const node = this;
      const combo = this.widgets.find((w) => w.name === "refmod_name");
      if (!combo) return;

      // ── real DOM drop zone (same approach as ComfyUI-Multi-Image-Loader-neo) ──
      const root = document.createElement("div");
      root.style.cssText = "display:flex;flex-direction:column;gap:6px;width:100%;box-sizing:border-box;padding:2px 0;";

      const dropZone = document.createElement("div");
      dropZone.style.cssText = `
        display:flex;flex-direction:column;justify-content:center;align-items:center;
        border:2px dashed #5a7abf;border-radius:10px;padding:14px 10px;text-align:center;
        cursor:pointer;color:#8ebaff;font-size:12px;font-family:sans-serif;
        background:rgba(60,90,150,0.15);transition:background .2s,border-color .2s;
        user-select:none;min-height:${DROPZONE_MIN_H}px;box-sizing:border-box;
      `;
      dropZone.innerHTML = `
        <div style="font-size:18px;margin-bottom:2px;">📦</div>
        <div><strong>Drop .safetensors files here</strong> or <strong>click to browse</strong></div>
        <div class="hrmod-status" style="opacity:.7;margin-top:6px;font-size:10px;min-height:12px;"></div>
      `;
      const statusEl = dropZone.querySelector(".hrmod-status");

      const fileInput = document.createElement("input");
      fileInput.type = "file";
      fileInput.accept = ".safetensors";
      fileInput.multiple = true;
      fileInput.style.display = "none";

      root.appendChild(dropZone);
      root.appendChild(fileInput);

      // Keep the node selected when interacting with the DOM widget.
      root.addEventListener("mousedown", () => {
        app.canvas?.selectNodes?.([node]);
      }, { capture: true });

      const idleLook = () => {
        dropZone.style.background = "rgba(60,90,150,0.15)";
        dropZone.style.borderColor = "#5a7abf";
      };

      node.addDOMWidget("hrmod_dropzone", "HRmodDropZone", root, {
        getValue() { return ""; },
        setValue() {},
        computeSize(width) { return [width, DROPZONE_MIN_H + 12]; },
      });

      if (!node.size || node.size[1] < 200) node.setSize([320, 230]);

      const clearSelection = () => {
        combo.options.values = ["None"];
        combo.value = "None";
        fileInput.value = "";
        if (statusEl) {
          statusEl.textContent = "Cleared.";
          statusEl.style.color = "#8899bb";
        }
        node.setDirtyCanvas?.(true);
      };

      this.addWidget("button", "Clear uploaded list", "", () => {
        clearSelection();
      });

      const mergeUploadedNames = (newNames) => {
        const values = Array.isArray(combo.options.values)
          ? [...combo.options.values]
          : Object.values(combo.options.values || {});

        const cleaned = values.filter((value) => value && value !== "None");
        for (const name of newNames) {
          if (name && !cleaned.includes(name)) {
            cleaned.push(name);
          }
        }

        combo.options.values = cleaned.length ? cleaned : ["None"];
        if (cleaned.length) {
          combo.value = cleaned[cleaned.length - 1];
        } else {
          combo.value = "None";
        }
      };

      const processFiles = async (incomingFiles) => {
        const files = uniqueSafetensorsFiles(incomingFiles);
        if (!files.length) {
          if (statusEl) {
            statusEl.textContent = "No .safetensors file in that drop.";
            statusEl.style.color = "#ffb0b0";
          }
          return;
        }

        const uploadedNames = [];

        try {
          for (let i = 0; i < files.length; i++) {
            const file = files[i];
            if (statusEl) {
              statusEl.textContent = `Uploading ${i + 1}/${files.length}: ${normalizeFileName(file.name)}`;
              statusEl.style.color = "#8ebaff";
            }

            const formData = new FormData();
            const safeName = normalizeFileName(file.webkitRelativePath || file.name || file.path || "");
            formData.append("file", file, safeName);

            const response = await fetch("/hrmod/upload_refmod", {
              method: "POST",
              body: formData,
            });

            const result = await response.json();
            if (!response.ok) {
              throw new Error(result.error || "Upload failed");
            }

            const names = Array.isArray(result.filenames)
              ? result.filenames
              : result.filename
                ? [result.filename]
                : [];

            for (const name of names) {
              if (name && !uploadedNames.includes(name)) {
                uploadedNames.push(name);
              }
            }
          }

          mergeUploadedNames(uploadedNames);
          if (statusEl) {
            statusEl.textContent = `Uploaded ${uploadedNames.length} file(s).`;
            statusEl.style.color = "#8fdcae";
          }
          node.setDirtyCanvas?.(true);
        } catch (err) {
          if (statusEl) {
            statusEl.textContent = `Upload failed: ${err.message}`;
            statusEl.style.color = "#ffb0b0";
          }
          console.error(err);
        } finally {
          fileInput.value = "";
        }
      };

      // ── picker ────────────────────────────────────────────────────────────
      dropZone.addEventListener("click", () => fileInput.click());

      fileInput.addEventListener("change", () => {
        const files = Array.from(fileInput.files || []);
        fileInput.value = "";
        processFiles(files);
      });

      // ── drag & drop on the drop zone ──────────────────────────────────────
      dropZone.addEventListener("dragenter", (event) => {
        event.preventDefault();
        event.stopPropagation();
      });

      dropZone.addEventListener("dragover", (event) => {
        event.preventDefault();
        event.stopPropagation();
        dropZone.style.background = "rgba(90,122,191,0.45)";
        dropZone.style.borderColor = "#aaccff";
      });

      dropZone.addEventListener("dragleave", (event) => {
        if (dropZone.contains(event.relatedTarget)) return;
        idleLook();
      });

      dropZone.addEventListener("drop", (event) => {
        event.preventDefault();
        event.stopPropagation();
        idleLook();
        const files = Array.from(event.dataTransfer?.files || []);
        processFiles(files);
      });

      // ── drop directly onto the node body ──────────────────────────────────
      const prevOnDrop = node.onDrop;
      node.onDrop = async (event) => {
        if (!event?.dataTransfer?.files?.length) {
          return prevOnDrop ? prevOnDrop.call(node, event) : false;
        }
        event.preventDefault?.();
        event.stopPropagation?.();
        await processFiles(Array.from(event.dataTransfer.files));
        return false;
      };
    };
  },
});
