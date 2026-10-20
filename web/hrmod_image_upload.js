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

      fileInput.addEventListener("change", async () => {
        const files = Array.from(fileInput.files || []);
        if (!files.length) return;

        const folder = String(folderWidget.value || "my_refmod_images").trim() || "my_refmod_images";
        const formData = new FormData();
        formData.append("folder_name", folder);
        for (const file of files) {
          formData.append("files", file);
        }

        try {
          uploadButton.name = "Uploading...";
          this.setDirtyCanvas?.(true);
          const response = await fetch("/hrmod/upload_images", { method: "POST", body: formData });
          const result = await response.json();
          if (!response.ok) {
            throw new Error(result.error || "Upload failed");
          }
          imageWidget.value = (result.files || []).join("|");
          await refreshImageList(folder, imageWidget, true);
          uploadButton.name = "Choose images";
          fileInput.value = "";
          this.setDirtyCanvas?.(true);
        } catch (err) {
          uploadButton.name = "Upload failed";
          console.error(err);
        }
      });

      folderWidget.callback = async () => {
        await refreshImageList(folderWidget.value, imageWidget, false);
      };

      refreshImageList(folderWidget.value, imageWidget, false);
    };
  },
});
