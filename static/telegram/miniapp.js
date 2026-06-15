(function () {
  const TELEGRAM_SDK_URL = "https://telegram.org/js/telegram-web-app.js";

  function isTelegramWebAppContext() {
    if (window.Telegram && window.Telegram.WebApp) {
      return true;
    }

    const hash = window.location.hash || "";
    if (hash.includes("tgWebAppData") || hash.includes("tgWebAppVersion")) {
      return true;
    }

    const search = window.location.search || "";
    if (search.includes("tgWebAppData") || search.includes("tgWebAppStartParam")) {
      return true;
    }

    const ua = navigator.userAgent || "";
    if (/Telegram/i.test(ua)) {
      return true;
    }

    const ref = document.referrer || "";
    if (/telegram\.(org|me)/i.test(ref)) {
      return true;
    }

    return false;
  }

  function loadTelegramSdk() {
    return new Promise((resolve, reject) => {
      if (window.Telegram && window.Telegram.WebApp) {
        resolve(window.Telegram.WebApp);
        return;
      }

      const script = document.createElement("script");
      script.src = TELEGRAM_SDK_URL;
      script.async = true;
      script.onload = () => {
        if (window.Telegram && window.Telegram.WebApp) {
          resolve(window.Telegram.WebApp);
          return;
        }
        reject(new Error("Telegram WebApp SDK unavailable"));
      };
      script.onerror = () => reject(new Error("Failed to load Telegram WebApp SDK"));
      document.head.appendChild(script);
    });
  }

  function getCookie(name) {
    const match = document.cookie.match(new RegExp("(^| )" + name + "=([^;]+)"));
    return match ? decodeURIComponent(match[2]) : "";
  }

  function initTelegramWebApp(tg) {
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
  }

  if (!isTelegramWebAppContext()) {
    return;
  }

  loadTelegramSdk().then(initTelegramWebApp).catch(() => {});
})();
