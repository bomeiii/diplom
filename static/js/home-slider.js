(function () {
  const slider = document.querySelector("[data-hero-slider]");
  if (!slider) return;

  const slides = Array.from(slider.querySelectorAll("[data-hero-slide]"));
  if (slides.length <= 1) return;

  const dotsContainer = slider.querySelector("[data-hero-dots]");
  const prevBtn = slider.querySelector("[data-hero-prev]");
  const nextBtn = slider.querySelector("[data-hero-next]");
  let current = slides.findIndex((slide) => slide.classList.contains("is-active"));
  if (current < 0) current = 0;

  let timer = null;
  const INTERVAL_MS = 6000;

  function goTo(index) {
    slides[current].classList.remove("is-active");
    slides[current].setAttribute("aria-hidden", "true");
    if (dotsContainer) {
      const dots = dotsContainer.querySelectorAll("[data-hero-dot]");
      if (dots[current]) dots[current].classList.remove("is-active");
    }

    current = (index + slides.length) % slides.length;

    slides[current].classList.add("is-active");
    slides[current].setAttribute("aria-hidden", "false");
    if (dotsContainer) {
      const dots = dotsContainer.querySelectorAll("[data-hero-dot]");
      if (dots[current]) dots[current].classList.add("is-active");
    }
  }

  function next() {
    goTo(current + 1);
  }

  function prev() {
    goTo(current - 1);
  }

  function startAutoplay() {
    stopAutoplay();
    timer = window.setInterval(next, INTERVAL_MS);
  }

  function stopAutoplay() {
    if (timer !== null) {
      window.clearInterval(timer);
      timer = null;
    }
  }

  if (dotsContainer) {
    slides.forEach((_, index) => {
      const dot = document.createElement("button");
      dot.type = "button";
      dot.className = "hero-slider__dot" + (index === current ? " is-active" : "");
      dot.setAttribute("data-hero-dot", "");
      dot.setAttribute("aria-label", "Слайд " + (index + 1));
      dot.addEventListener("click", () => {
        goTo(index);
        startAutoplay();
      });
      dotsContainer.appendChild(dot);
    });
  }

  if (prevBtn) {
    prevBtn.addEventListener("click", () => {
      prev();
      startAutoplay();
    });
  }

  if (nextBtn) {
    nextBtn.addEventListener("click", () => {
      next();
      startAutoplay();
    });
  }

  slider.addEventListener("mouseenter", stopAutoplay);
  slider.addEventListener("mouseleave", startAutoplay);
  slider.addEventListener("focusin", stopAutoplay);
  slider.addEventListener("focusout", startAutoplay);

  startAutoplay();
})();
