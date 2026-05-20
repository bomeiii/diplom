function initProfilePhotoPreview() {
  const form = document.getElementById("profile-form");
  const input =
    form && form.querySelector('input[type="file"][name="photo"]');
  const preview = document.getElementById("photo-preview");
  const wrap = document.getElementById("photo-preview-wrap");
  if (!input || !preview || !wrap) return;

  const showPreview = (dataUrl) => {
    preview.onload = () => wrap.classList.remove("is-hidden");
    preview.onerror = () => wrap.classList.add("is-hidden");
    preview.src = dataUrl;
    if (preview.complete && preview.naturalWidth > 0) {
      wrap.classList.remove("is-hidden");
    }
  };

  const onFileSelected = () => {
    const file = input.files && input.files[0];
    if (!file) return;
    if (!file.type.startsWith("image/")) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      const result = event.target && event.target.result;
      if (typeof result === "string") {
        showPreview(result);
      }
    };
    reader.onerror = () => wrap.classList.add("is-hidden");
    reader.readAsDataURL(file);
  };

  input.addEventListener("change", onFileSelected);
  input.addEventListener("input", onFileSelected);
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initProfilePhotoPreview);
} else {
  initProfilePhotoPreview();
}
