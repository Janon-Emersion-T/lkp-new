"use strict";

/**
 * Helpers
 */
const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => Array.from(root.querySelectorAll(selector));

/**
 * Search Modal
 * - Opens via: `[data-search-open]`, `.js-search-open`, `#searchBtn*`
 * - Closes via: `#closeBtn` or clicking the overlay
 */
function initSearchModal() {
  const modal = $("#searchModal");
  if (!modal) return;

  const open = () => {
    modal.classList.remove("invisible", "opacity-0", "-translate-y-1/2");
    modal.classList.add("visible", "opacity-100", "translate-y-0");
  };

  const close = () => {
    modal.classList.add("invisible", "opacity-0", "-translate-y-1/2");
    modal.classList.remove("visible", "opacity-100", "translate-y-0");
  };

  $$("[data-search-open], .js-search-open, #searchBtn, #searchBtnDesktop, #searchBtnMobile").forEach((button) => {
    button.addEventListener("click", open);
  });

  const closeBtn = $("#closeBtn");
  if (closeBtn) closeBtn.addEventListener("click", close);

  modal.addEventListener("click", (event) => {
    if (event.target === modal) close();
  });
}

/**
 * Sticky Header
 * - Adds `is-sticky` after `thresholdPx`
 * - Optional logo swap via `#header-logo`
 */
function initStickyHeader({ thresholdPx = 200 } = {}) {
  const headers = $$(".site-header");
  if (headers.length === 0) return;

  const stickyClass = "is-sticky";

  const update = () => {
    const isSticky = window.scrollY > thresholdPx;

    headers.forEach((header) => {
      // 1. Toggle sticky class on the header itself
      header.classList.toggle(stickyClass, isSticky);

      // 2. Find the logo INSIDE this specific header
      const logo = header.querySelector("#header-logo");

      if (logo) {
        // 3. Update source only for this specific logo
        logo.src = isSticky ? "assets/images/logo.png" : "assets/images/logo-white.png";
      }
    });
  };

  update();
  window.addEventListener("scroll", update, { passive: true });
}

/**
 * Footer Year
 */
function initFooterYear() {
  const year = $("#year");
  if (year) year.textContent = String(new Date().getFullYear());
}

/**
 * Video Popup
 * - Requires: `#popup-video` + `#video-iframe`
 * - Opens via: `.video-btn` (optional `data-video-id`)
 */
function initVideoPopup({ defaultVideoId = "FDaF8_5dzzk" } = {}) {
  const popup = $("#popup-video");
  if (!popup) return;

  const iframe = $("#video-iframe", popup);
  const closeBtn = $(".modal-close-btn", popup);
  const buttons = $$(".video-btn");

  const open = (videoId) => {
    const id = videoId || defaultVideoId;
    if (iframe) iframe.src = `https://www.youtube.com/embed/${id}?autoplay=1`;
    popup.classList.add("open");
    document.body.style.overflow = "hidden";
  };

  const close = () => {
    popup.classList.remove("open");
    if (iframe) iframe.src = "";
    document.body.style.overflow = "auto";
  };

  buttons.forEach((button) => {
    button.addEventListener("click", () => open(button.dataset.videoId));
  });

  if (closeBtn) closeBtn.addEventListener("click", close);
  popup.addEventListener("click", (event) => {
    if (event.target === popup) close();
  });
}

/**
 * Fun Fact Counter
 * - Uses IntersectionObserver to run only once when `#fun-fact` becomes visible.
 * - Target values are read from `data-count` on `.fun-fact__number`.
 */
function initFunFactCounter({ durationMs = 2000, threshold = 0.2 } = {}) {
  const section = $("#fun-fact");
  if (!section || typeof IntersectionObserver === "undefined") return;

  const counters = $$(".fun-fact__number");
  if (counters.length === 0) return;

  let hasCounted = false;

  const animateCounter = (element, target) => {
    const startTime = performance.now();

    const step = (currentTime) => {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / durationMs, 1);

      // Ease-out quadratic
      const eased = progress * (2 - progress);
      element.textContent = String(Math.floor(eased * target));

      if (progress < 1) requestAnimationFrame(step);
      else element.textContent = String(target);
    };

    requestAnimationFrame(step);
  };

  const observer = new IntersectionObserver(
    (entries) => {
      const isVisible = entries.some((entry) => entry.isIntersecting);
      if (!isVisible || hasCounted) return;

      counters.forEach((counter) => {
        const raw = counter.getAttribute("data-count");
        const target = Number.parseInt(raw || "0", 10);
        if (!Number.isFinite(target)) return;
        animateCounter(counter, target);
      });

      hasCounted = true;
    },
    { root: null, rootMargin: "0px", threshold },
  );

  observer.observe(section);
}

/**
 * Job Filter Tabs
 * - Requires: `.tab-btn` + `.job-card`
 * - Optional: `#no-results`
 */
function initJobFilterTabs() {
  const filterButtons = $$(".tab-btn");
  const jobCards = $$(".job-card");
  if (filterButtons.length === 0 || jobCards.length === 0) return;

  const noResults = $("#no-results");

  filterButtons.forEach((button) => {
    button.addEventListener("click", () => {
      filterButtons.forEach((btn) => btn.classList.remove("active"));
      button.classList.add("active");

      const filterValue = button.getAttribute("data-filter") || "all";
      let visibleCount = 0;

      jobCards.forEach((card) => {
        card.classList.remove("fade-in");

        const isMatch = filterValue === "all" || card.getAttribute("data-category") === filterValue;

        if (isMatch) {
          card.classList.remove("hidden");
          // Restart CSS animation
          void card.offsetWidth;
          card.classList.add("fade-in");
          visibleCount++;
        } else {
          card.classList.add("hidden");
        }
      });

      if (noResults) noResults.classList.toggle("hidden", visibleCount !== 0);
    });
  });
}

/**
 * Social Sidebar
 * - Reveals `#social-sidebar` after `scrollThresholdPx` by toggling Tailwind translate classes
 */
function initSocialSidebar({ scrollThresholdPx = 300 } = {}) {
  const socialSidebar = $("#social-sidebar");
  if (!socialSidebar) return;

  const update = () => {
    const show = window.scrollY > scrollThresholdPx;
    socialSidebar.classList.toggle("-translate-x-full", !show);
    socialSidebar.classList.toggle("translate-x-0", show);
  };

  update();
  window.addEventListener("scroll", update, { passive: true });
}

/**
 * Active Header Menu (Dynamic)
 * - Highlights current page link in both header versions (desktop + mobile drawer).
 * - If a submenu item matches, its parent top-level menu is also highlighted.
 */
function initActiveHeaderMenu() {
  const currentPath = window.location.pathname.replace(/\\/g, "/");
  const currentFile = (currentPath.split("/").pop() || "index.html").toLowerCase();

  const normalizeHrefToFile = (href) => {
    if (!href) return null;

    // Ignore in-page links, mailto, tel, javascript, and placeholders.
    if (
      href === "#" ||
      href.startsWith("#") ||
      href.startsWith("mailto:") ||
      href.startsWith("tel:") ||
      href.startsWith("javascript:")
    ) {
      return null;
    }

    // Strip query/hash and normalize ./ prefixes.
    const clean = href.split("#")[0].split("?")[0].replace(/\\/g, "/").trim();
    const file = clean.split("/").pop() || "";
    return file.toLowerCase();
  };

  const headers = $$(".site-header");
  const drawer = $("#drawer");
  const containers = [...headers, ...(drawer ? [drawer] : [])];
  if (containers.length === 0) return;

  containers.forEach((container) => {
    // Only consider real navigation links (avoid matching logo/CTA links like ./index.html).
    const navRoots = container.id === "drawer" ? [container] : $$("nav", container);

    const navLinks = navRoots.flatMap((root) => $$("a[href]", root));
    if (navLinks.length === 0) return;

    // Reset any previously hardcoded "active" state inside this nav scope.
    navLinks.forEach((link) => {
      link.classList.remove("active", "text-primary");

      const underline = $("span", link);
      if (underline && underline.classList.contains("scale-x-100")) {
        underline.classList.remove("scale-x-100", "origin-bottom-left");
        underline.classList.add("scale-x-0", "origin-bottom-right");
      }
    });

    // Find the best match in this container (supports nested menus).
    let matchedLink = null;
    for (const link of navLinks) {
      const file = normalizeHrefToFile(link.getAttribute("href"));
      if (!file) continue;
      if (file === currentFile) {
        matchedLink = link;
        break;
      }
    }

    if (!matchedLink) return;

    // Highlight the matched link itself (useful for mobile drawer lists).
    matchedLink.classList.add("text-primary", "active");

    // If link is inside a dropdown submenu, also activate its top-level menu link.
    const topLevelLi = matchedLink.closest("li.group");
    if (topLevelLi) {
      const topLevelLink = $("a", topLevelLi);
      if (topLevelLink) {
        topLevelLink.classList.add("text-primary", "active");

        const underline = $("span", topLevelLink);
        if (underline) {
          underline.classList.remove("scale-x-0", "origin-bottom-right");
          underline.classList.add("scale-x-100", "origin-bottom-left");
        }
      }
    }

    // Mobile drawer: if the active link is inside a collapsed accordion, open it.
    const submenu = matchedLink.closest("ul[id$='Menu']");
    if (submenu && submenu.classList.contains("hidden")) {
      const button = submenu.parentElement ? $("button", submenu.parentElement) : null;
      const chevron = button ? $("i", button) : null;

      if (typeof window.openDropdown === "function") {
        window.openDropdown(submenu, chevron || undefined);
      } else {
        submenu.classList.remove("hidden");
        submenu.style.maxHeight = submenu.scrollHeight + "px";
        if (chevron) chevron.style.transform = "rotate(180deg)";
      }
    }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  initSearchModal();
  initStickyHeader();
  initFooterYear();
  initVideoPopup();
  initFunFactCounter();
  initJobFilterTabs();
  initSocialSidebar();
  initActiveHeaderMenu();
});
