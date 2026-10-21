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

app.registerExtension({
  name: "HRmod.UploadButton",
  async beforeRegisterNodeDef(nodeType, nodeData, app) {
    if (nodeData.name !== "HRmodUploadRefMod") return;

    const onNodeCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function () {
      onNodeCreated?.apply(this, arguments);

      const combo = this.widgets.find((w) => w.name === "refmod_name");
      if (!combo) return;

      const fileInput = document.createElement("input");
      fileInput.type = "file";
      fileInput.accept = ".safetensors";
      fileInput.multiple = true;
      fileInput.style.display = "none";
      document.body.appendChild(fileInput);

      const clearSelection = () => {
        combo.options.values = ["None"];
        combo.value = "None";
        this.setDirtyCanvas?.(true);
      };

      const dropZone = this.addWidget("button", "Drop .safetensors files here", "", () => {
        fileInput.click();
      });
      if (dropZone?.inputEl) {
        dropZone.inputEl.style.minHeight = "72px";
        dropZone.inputEl.style.padding = "10px";
        dropZone.inputEl.style.whiteSpace = "normal";
        dropZone.inputEl.style.display = "flex";
        dropZone.inputEl.style.alignItems = "center";
        dropZone.inputEl.style.justifyContent = "center";
        dropZone.inputEl.style.border = "1px dashed rgba(120, 140, 180, 0.9)";
        dropZone.inputEl.style.borderRadius = "8px";
        dropZone.inputEl.style.background = "rgba(90, 120, 150, 0.12)";
        dropZone.inputEl.style.color = "#e5eefb";
        dropZone.inputEl.style.fontWeight = "600";
      }

      const uploadButton = this.addWidget("button", "Choose file(s) to upload", "", () => {
        fileInput.click();
      });

      const clearButton = this.addWidget("button", "Clear uploaded list", "", () => {
        clearSelection();
        fileInput.value = "";
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
        if (!files.length) return;

        uploadButton.name = "Uploading...";
        clearButton.name = "Uploading...";
        this.setDirtyCanvas?.(true);

        const uploadedNames = [];

        try {
          for (const file of files) {
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
          uploadButton.name = "Choose file(s) to upload";
          clearButton.name = "Clear uploaded list";
          this.setDirtyCanvas?.(true);
        } catch (err) {
          uploadButton.name = "Upload failed";
          clearButton.name = "Clear uploaded list";
          console.error(err);
        } finally {
          fileInput.value = "";
        }
      };

      fileInput.addEventListener("change", async () => {
        await processFiles(Array.from(fileInput.files || []));
      });

      const handleDropFiles = async (event) => {
        if (!event.dataTransfer || !event.dataTransfer.files || !event.dataTransfer.files.length) {
          return;
        }

        const files = Array.from(event.dataTransfer.files);
        if (!files.some(isSafetensorsFile)) {
          return;
        }

        event.preventDefault();
        event.stopPropagation();
        await processFiles(files);
      };

      if (dropZone?.inputEl) {
        dropZone.inputEl.addEventListener("dragover", (event) => {
          if (!event.dataTransfer || !Array.from(event.dataTransfer.files || []).some(isSafetensorsFile)) {
            return;
          }
          event.preventDefault();
          event.stopPropagation();
          dropZone.inputEl.style.borderColor = "rgba(110, 220, 160, 0.95)";
          dropZone.inputEl.style.background = "rgba(110, 220, 160, 0.12)";
        });

        dropZone.inputEl.addEventListener("dragleave", () => {
          dropZone.inputEl.style.borderColor = "rgba(120, 140, 180, 0.9)";
          dropZone.inputEl.style.background = "rgba(90, 120, 150, 0.12)";
        });

        dropZone.inputEl.addEventListener("drop", handleDropFiles);
      }
    };
  },
});
