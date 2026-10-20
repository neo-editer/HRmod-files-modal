import { app } from "../../../scripts/app.js";

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
      fileInput.style.display = "none";
      document.body.appendChild(fileInput);

      const uploadButton = this.addWidget("button", "Choose file to upload", "", () => {
        fileInput.click();
      });

      fileInput.addEventListener("change", async () => {
        const file = fileInput.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append("file", file);

        uploadButton.name = "Uploading...";
        this.setDirtyCanvas?.(true);

        try {
          const response = await fetch("/hrmod/upload_refmod", {
            method: "POST",
            body: formData,
          });

          const result = await response.json();
          if (!response.ok) {
            throw new Error(result.error || "Upload failed");
          }

          const values = Array.isArray(combo.options.values)
            ? combo.options.values
            : Object.values(combo.options.values || {});

          if (!values.includes(result.filename)) {
            values.push(result.filename);
          }

          combo.options.values = values;
          combo.value = result.filename;
          uploadButton.name = "Choose file to upload";
          this.setDirtyCanvas?.(true);
        } catch (err) {
          uploadButton.name = "Upload failed";
          console.error(err);
        }
      });
    };
  },
});
