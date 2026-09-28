

document.addEventListener("DOMContentLoaded", () => {
  // 1. Define Your Common Presets Here
  const sliderPresets = {
    "slider-1-col": {
      breakpoints: { 0: { slidesPerView: 1 } },
    },
    "slider-2-col": {
      breakpoints: {
        0: { slidesPerView: 1 },
        640: { slidesPerView: 2 },
      },
    },
    "slider-3-col": {
      breakpoints: {
        0: { slidesPerView: 1 },
        640: { slidesPerView: 2 },
        1024: { slidesPerView: 3 },
      },
    },
    "slider-4-col": {
      breakpoints: {
        0: { slidesPerView: 1 },
        640: { slidesPerView: 2 },
        1024: { slidesPerView: 3 },
        1280: { slidesPerView: 4 },
      },
    },
    "slider-3-5-col": {
      centeredSlides: true,
      breakpoints: {
        0: { slidesPerView: 1.2 }, // Mobile: shows a bit of the next slide
        640: { slidesPerView: 2 }, // Tablet: shows 2 slides
        1024: { slidesPerView: 3 }, // Desktop: shows 3 slides
        1280: { slidesPerView: 3.5 }, // Large Desktop
      },
    },

    "slider-2-5-col": {
      centeredSlides: true,
      breakpoints: {
        0: { slidesPerView: 1.1 },
        640: { slidesPerView: 2.5 },
      },
    },
    "slider-hero-creative": {
      effect: "creative",
      speed: 1500,
      autoplay: { delay: 5000, disableOnInteraction: false },
      creativeEffect: {
        prev: {
          translate: ["-80%", 0, 0],
        },
        next: {
          translate: ["100%", 0, 0],
        },
      },
    },
    "slider-hero-fade": {
      effect: "fade",
      autoplay: { delay: 5000, disableOnInteraction: false },
      breakpoints: { 0: { slidesPerView: 1 } },
    },
    "slider-hero-cube": {
      effect: "cube",
      grabCursor: true,
      speed: 2000,
      autoplay: { delay: 5000, disableOnInteraction: false },
      cubeEffect: {
        shadow: true,
        slideShadows: true,
        shadowOffset: 20,
        shadowScale: 0.94,
      },
      breakpoints: { 0: { slidesPerView: 1 } },
    },
  };

  // 2. Select All Sliders
  const sliders = document.querySelectorAll(".swiper-container");

  sliders.forEach((container) => {
    let options = {
      loop: true,
      speed: 800,
      spaceBetween: 20,
      keyboard: { enabled: true, onlyInViewport: true },
      grabCursor: true,
      // Auto-find navigation inside THIS container only
      navigation: {
        nextEl: container.querySelector(".swiper-btn-next"),
        prevEl: container.querySelector(".swiper-btn-prev"),
      },
      // Auto-find pagination inside THIS container only
      pagination: {
        el: container.querySelector(".swiper-pagination"),
        clickable: true,
      },
    };

    // 3. Merge Preset based on Class Name
    // Checks if the container has any class matching our presets
    for (const [className, presetOptions] of Object.entries(sliderPresets)) {
      if (container.classList.contains(className)) {
        options = { ...options, ...presetOptions };
        break; // Stop after finding the first match
      }
    }

    // 4. Handle Autoplay Override via Data Attribute (Optional)
    if (container.dataset.autoplay) {
      options.autoplay = {
        delay: parseInt(container.dataset.autoplay),
        disableOnInteraction: false,
      };
    }

    // Initialize
    new Swiper(container, options);
  });
});
