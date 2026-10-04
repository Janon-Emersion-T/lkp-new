
(function () {
  "use strict";

  const currentScript = document.currentScript;
  const scriptList = (currentScript?.dataset.siteScripts || "")
    .split(",")
    .map((src) => src.trim())
    .filter(Boolean);

  function loadPartial(element) {
    const src = element.dataset.include;
    if (!src) return Promise.resolve();

    return fetch(src)
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Unable to load partial: ${src}`);
        }
        return response.text();
      })
      .then((html) => {
        element.outerHTML = html;
      })
      .catch((error) => {
        console.error(error);
      });
  }

  function loadScript(src) {
    return new Promise((resolve, reject) => {
      const script = document.createElement("script");
      script.src = src;
      script.onload = resolve;
      script.onerror = () => reject(new Error(`Unable to load script: ${src}`));
      document.body.appendChild(script);
    });
  }

  function loadScriptsInOrder(sources) {
    return sources.reduce(
      (chain, src) =>
        chain.then(() =>
          loadScript(src).catch((error) => {
            console.error(error);
          }),
        ),
      Promise.resolve(),
    );
  }

  function initQuoteModal() {
    const modal = document.querySelector("#quoteModal");
    if (!modal || modal.dataset.quoteReady === "true") return;

    modal.dataset.quoteReady = "true";

    const form = modal.querySelector("#quoteForm");
    const status = modal.querySelector("#quoteFormStatus");
    let lastFocusedElement = null;

    function open(event) {
      if (event) event.preventDefault();

      lastFocusedElement = document.activeElement;
      modal.classList.remove("invisible", "opacity-0");
      modal.classList.add("visible", "opacity-100");
      document.body.style.overflow = "hidden";

      const firstInput = modal.querySelector("input, select, textarea, button");
      if (firstInput) firstInput.focus();
    }

    function close() {
      modal.classList.add("invisible", "opacity-0");
      modal.classList.remove("visible", "opacity-100");
      document.body.style.overflow = "auto";

      if (lastFocusedElement && typeof lastFocusedElement.focus === "function") {
        lastFocusedElement.focus();
      }
    }

    document.addEventListener("click", (event) => {
      const trigger = event.target.closest("[data-quote-open]");
      if (trigger) open(event);
    });

    modal.querySelectorAll("[data-quote-close]").forEach((button) => {
      button.addEventListener("click", close);
    });

    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && modal.classList.contains("visible")) close();
    });

    if (form) {
      form.addEventListener("submit", async (event) => {
        event.preventDefault();

        const submitButton = form.querySelector('button[type="submit"]');
        const payload = Object.fromEntries(new FormData(form).entries());
        payload.source = "quote";
        payload.subject = "Quote Request";

        if (status) {
          status.textContent = "Sending your quote request...";
          status.classList.remove("hidden");
        }

        if (submitButton) {
          submitButton.disabled = true;
          submitButton.classList.add("opacity-70", "pointer-events-none");
        }

        try {
          const response = await fetch("/api/leads/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
          });

          if (!response.ok) {
            const data = await response.json().catch(() => ({}));
            throw new Error(data.error || "Unable to send your quote request.");
          }

          if (status) {
            status.textContent = "Thank you. Your quote request has been received and our team will contact you shortly.";
          }
          form.reset();
        } catch (error) {
          if (status) {
            status.textContent = error && error.message ? error.message : "Something went wrong. Please try again.";
          }
        } finally {
          if (submitButton) {
            submitButton.disabled = false;
            submitButton.classList.remove("opacity-70", "pointer-events-none");
          }
        }
      });
    }
  }

  function boot() {
    const includes = Array.from(document.querySelectorAll("[data-include]"));

    Promise.all(includes.map(loadPartial))
      .then(() => {
        initQuoteModal();
        document.dispatchEvent(new CustomEvent("site:partials-loaded"));
        return loadScriptsInOrder(scriptList);
      })
      .catch((error) => {
        console.error(error);
      });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
