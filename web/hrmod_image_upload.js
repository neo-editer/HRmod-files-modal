import { app } from "../../../scripts/app.js";

app.registerExtension({
  name: "HRmod.ImageUploadButton",
  async beforeRegisterNodeDef(nodeType, nodeData, app) {
    if (nodeData.name !== "HRmodUploadImagesForRefMod") return;

    const onNodeCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function () {
      onNodeCreated?.apply(this, arguments);

      const folderWidget = this.widgets.find((w) => w.name === "folder_name");
      const imageWidget = this.widgets.find((w) => w.name === "image_files");
      if (!folderWidget || !imageWidget) return;

      const fileInput = document.createElement("input");
      fileInput.type = "file";
      fileInput.accept = "image/*";
      fileInput.multiple = true;
      fileInput.style.display = "none";
      document.body.appendChild(fileInput);

      const uploadButton = this.addWidget("button", "Choose images", "", () => {
        fileInput.click();
      });

      const removeButton = this.addWidget("button", "Remove selected", "", async () => {
        const selected = String(imageWidget.value || "").split("|").filter(Boolean);
        if (!selected.length) return;
        const folder = String(folderWidget.value || "my_refmod_images").trim() || "my_refmod_images";
        for (const item of selected) {
          try {
            const r = await fetch("/hrmod/remove_image", {
              method: "POST",
              headers: { "Content-Type": "application/x-www-form-urlencoded" },
              body: new URLSearchParams({ folder_name: folder, filename: item })
            });
            const data = await r.json().catch(() => ({}));
            if (!r.ok) console.warn(data.error || "remove failed");
          } catch (err) {
            console.warn(err);
          }
        }
        imageWidget.value = "";
        await refreshImageList(folderWidget.value, imageWidget, false);
      });

      async function refreshImageList(folderName, widget, keepCurrent = true) {
        const folder = String(folderName || "my_refmod_images").trim() || "my_refmod_images";
        try {
          const response = await fetch(`/hrmod/list_images?folder_name=${encodeURIComponent(folder)}`);
          const data = await response.json();
          const files = Array.isArray(data.files) ? data.files : [];
          widget.options.values = files.length ? files : ["None"];
          if (keepCurrent && String(widget.value || "").trim()) {
            if (!files.includes(widget.value)) {
              widget.value = files[0] || "";
            }
          } else {
            widget.value = files[0] || "";
          }
        } catch (err) {
          console.warn(err);
          widget.options.values = ["None"];
        }
      }

      async function handleFiles(rawFiles) {
        const files = Array.from(rawFiles || []);
        if (!files.length) return;

        const folder = String(folderWidget.value || "my_refmod_images").trim() || "my_refmod_images";
        const formData = new FormData();
        formData.append("folder_name", folder);
        for (const file of files) {
          if (file && typeof file.name === "string") {
            formData.append("files", file);
          }
        }

        if (!formData.has("files")) {
          return;
        }

        try {
          uploadButton.name = "Uploading...";
          this.setDirtyCanvas?.(true);
          const response = await fetch("/hrmod/upload_images", { method: "POST", body: formData });
          const result = await response.json();
          if (!response.ok) {
            throw new Error(result.error || "Upload failed");
          }

          const uploaded = Array.isArray(result.files) ? result.files : [];
          if (uploaded.length) {
            imageWidget.value = uploaded.join("|");
          }
          await refreshImageList(folder, imageWidget, true);
          uploadButton.name = "Choose images";
          this.setDirtyCanvas?.(true);
        } catch (err) {
          uploadButton.name = "Upload failed";
          console.error(err);
        }
      }

      fileInput.addEventListener("change", async () => {
        await handleFiles(Array.from(fileInput.files || []));
        fileInput.value = "";
      });

      this.onDragOver = function (event) {
        if (!event || !event.dataTransfer || !event.dataTransfer.types) {
          return false;
        }
        if (event.dataTransfer.types.includes("Files")) {
          event.preventDefault();
          event.dataTransfer.dropEffect = "copy";
          return true;
        }
        return false;
      };

      this.onDragDrop = async function (event) {
        if (!event || !event.dataTransfer) {
          return false;
        }

        event.preventDefault();
        event.stopPropagation();

        const droppedFiles = Array.from(event.dataTransfer.files || []);
        if (!droppedFiles.length) {
          return false;
        }

        await handleFiles(droppedFiles);
        return true;
      };

      folderWidget.callback = async () => {
        await refreshImageList(folderWidget.value, imageWidget, false);
      };

      refreshImageList(folderWidget.value, imageWidget, false);
    };
  },
});
