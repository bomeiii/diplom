(function () {
  const published = document.getElementById("id_is_published");
  const isPrivate = document.getElementById("id_is_private");
  if (!published || !isPrivate) return;

  const onPublishedChange = () => {
    if (published.checked) {
      isPrivate.checked = false;
    }
    syncPrivateUi();
  };

  const onPrivateChange = () => {
    if (isPrivate.checked) {
      published.checked = false;
    }
    syncPrivateUi();
  };

  const syncPrivateUi = () => {
    document.querySelectorAll("[data-private-link-ui]").forEach((el) => {
      el.classList.toggle("is-hidden", !isPrivate.checked);
    });
  };

  published.addEventListener("change", onPublishedChange);
  isPrivate.addEventListener("change", onPrivateChange);
  syncPrivateUi();
})();
