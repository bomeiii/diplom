(function () {
  const tg = window.Telegram && window.Telegram.WebApp;
  if (!tg) {
    return;
  }

  tg.ready();
  tg.expand();

  if (tg.colorScheme === "dark") {
    document.documentElement.classList.add("tg-dark");
  }

  const theme = tg.themeParams || {};
  const root = document.documentElement;
  Object.entries(theme).forEach(([key, value]) => {
    if (value) {
      const cssKey = key.replace(/([A-Z])/g, "-$1").toLowerCase();
      root.style.setProperty(`--tg-theme-${cssKey}`, value);
    }
  });

  document.body.classList.add("twa-telegram");

  const initUrl = document.body.dataset.telegramInitUrl;
  if (initUrl && tg.initData) {
    const csrfInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
    const csrfToken = csrfInput ? csrfInput.value : getCookie("csrftoken");
    fetch(initUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
        "X-Telegram-Init-Data": tg.initData,
        ...(csrfToken ? { "X-CSRFToken": csrfToken } : {}),
      },
      body: new URLSearchParams({ telegram_init_data: tg.initData }),
      credentials: "same-origin",
    }).catch(() => {});
  }

  document.querySelectorAll("form").forEach((form) => {
    if (!form.querySelector('input[name="telegram_init_data"]')) {
      const hidden = document.createElement("input");
      hidden.type = "hidden";
      hidden.name = "telegram_init_data";
      hidden.value = tg.initData || "";
      form.appendChild(hidden);
    }

    const childInput = form.querySelector('input[name="child_name"]');
    const user = tg.initDataUnsafe && tg.initDataUnsafe.user;
    if (childInput && user) {
      const displayName = [user.first_name, user.last_name].filter(Boolean).join(" ").trim();
      if (displayName) {
        childInput.value = displayName;
        const wrapper = childInput.closest(".child-name-field");
        if (wrapper) {
          wrapper.style.display = "none";
        } else {
          childInput.type = "hidden";
        }
      }
    }
  });

  const main = document.querySelector("main");
  if (main) {
    tg.BackButton.onClick(() => {
      if (window.history.length > 1) {
        window.history.back();
      } else {
        tg.close();
      }
    });

    const path = window.location.pathname;
    const isHome = path === "/" || path.endsWith("/");
    if (!isHome) {
      tg.BackButton.show();
    } else {
      tg.BackButton.hide();
    }
  }

  function getCookie(name) {
    const match = document.cookie.match(new RegExp("(^| )" + name + "=([^;]+)"));
    return match ? decodeURIComponent(match[2]) : "";
  }
})();
