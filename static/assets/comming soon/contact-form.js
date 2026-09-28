/**
 * Contact Form Handler
 * - Safe to include on all pages (no-ops if #contactForm not present).
 * - Submission settings are configured directly in this file.
 * - Set the endpoint or EmailJS constants below.
 */

"use strict";

function initContactForm() {
  const form = document.getElementById("contactForm");
  if (!form) return;

  const endpoint = ""; // Set this to your backend endpoint if using server submission
  const emailjsService = "YOUR_EMAILJS_SERVICE_ID";
  const emailjsTemplate = "YOUR_EMAILJS_TEMPLATE_ID";
  const emailjsPublicKey = "YOUR_EMAILJS_PUBLIC_KEY";

  if (!endpoint && !(emailjsService && emailjsTemplate)) {
    console.warn(
      "Contact form is active but no submission method is configured. " +
        "Edit the constants in assets/js/contact-form.js.",
    );
  }

  // Custom Select Functionality
  const customSelect = document.getElementById("contactSubjectWrapper");
  const selectSelected = document.getElementById("selectSelected");
  const selectItems = document.querySelector(".select-items");
  const hiddenInput = document.getElementById("contactSubject");
  const selectedText = selectSelected.querySelector(".selected-text");

  if (customSelect && selectSelected && selectItems && hiddenInput) {
    // Toggle dropdown
    selectSelected.addEventListener("click", function () {
      customSelect.classList.toggle("open");
      selectItems.classList.toggle("select-hide");
    });

    // Select item
    selectItems.addEventListener("click", function (e) {
      if (e.target.classList.contains("select-item") || e.target.closest(".select-item")) {
        const item = e.target.classList.contains("select-item") ? e.target : e.target.closest(".select-item");
        const value = item.getAttribute("data-value");
        const text = item.textContent.trim();

        selectedText.textContent = text;
        hiddenInput.value = value;

        // Update selected state
        selectItems.querySelectorAll(".select-item").forEach((i) => i.classList.remove("selected"));
        item.classList.add("selected");

        // Close dropdown
        customSelect.classList.remove("open");
        selectItems.classList.add("select-hide");
      }
    });

    // Close dropdown when clicking outside
    document.addEventListener("click", function (e) {
      if (!customSelect.contains(e.target)) {
        customSelect.classList.remove("open");
        selectItems.classList.add("select-hide");
      }
    });
  }

  const status = document.getElementById("formStatus");
  const submitButton = form.querySelector('button[type="submit"]');

  const setStatus = (message, type) => {
    if (!status) return;
    status.textContent = message;
    status.classList.remove(
      "hidden",
      "bg-green-50",
      "text-green-700",
      "border",
      "border-green-200",
      "bg-red-50",
      "text-red-700",
      "border-red-200",
    );

    if (type === "success") status.classList.add("bg-green-50", "text-green-700", "border", "border-green-200");
    if (type === "error") status.classList.add("bg-red-50", "text-red-700", "border", "border-red-200");
  };

  const setLoading = (isLoading) => {
    if (!submitButton) return;
    submitButton.disabled = isLoading;
    submitButton.classList.toggle("opacity-70", isLoading);
    submitButton.classList.toggle("pointer-events-none", isLoading);
  };

  const getPayload = () => {
    const data = new FormData(form);
    const payload = Object.fromEntries(data.entries());
    return {
      name: String(payload.name || "").trim(),
      email: String(payload.email || "").trim(),
      phone: String(payload.phone || "").trim(),
      subject: String(payload.subject || "").trim(),
      message: String(payload.message || "").trim(),
    };
  };

  const validate = (payload) => {
    if (!payload.name) return "Please enter your full name.";
    if (!payload.email) return "Please enter your email address.";
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(payload.email)) return "Please enter a valid email address.";
    if (!payload.subject) return "Please select a subject.";
    if (!payload.message) return "Please enter your message.";
    return null;
  };

  const setFieldInvalid = (field, isInvalid) => {
    if (!field) return;
    field.setAttribute("aria-invalid", isInvalid ? "true" : "false");
    if (field.id === "contactSubject") {
      // For custom select, style the selected div
      const selectedDiv = document.getElementById("selectSelected");
      if (selectedDiv) {
        selectedDiv.classList.toggle("border-red-400", isInvalid);
        selectedDiv.classList.toggle("focus:border-red-400", isInvalid);
        selectedDiv.classList.toggle("focus:ring-red-200", isInvalid);
      }
    } else {
      field.classList.toggle("border-red-400", isInvalid);
      field.classList.toggle("focus:border-red-400", isInvalid);
      field.classList.toggle("focus:ring-red-200", isInvalid);
    }
  };

  const clearFieldErrors = () => {
    setFieldInvalid(document.getElementById("contactName"), false);
    setFieldInvalid(document.getElementById("contactEmail"), false);
    setFieldInvalid(document.getElementById("contactSubject"), false);
    setFieldInvalid(document.getElementById("contactMessage"), false);
  };

  const focusFirstInvalid = (payload) => {
    const nameEl = document.getElementById("contactName");
    const emailEl = document.getElementById("contactEmail");
    const subjectEl = document.getElementById("selectSelected");
    const messageEl = document.getElementById("contactMessage");

    if (!payload.name) return nameEl && nameEl.focus();
    if (!payload.email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(payload.email)) return emailEl && emailEl.focus();
    if (!payload.subject) return subjectEl && subjectEl.focus();
    if (!payload.message) return messageEl && messageEl.focus();
  };

  async function submitToEndpoint(endpoint, payload) {
    const response = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const text = await response.text().catch(() => "");
      throw new Error(text || "Request failed.");
    }
  }

  async function submitWithEmailJS({ serviceId, templateId, publicKey }, payload) {
    if (!window.emailjs || typeof window.emailjs.send !== "function") {
      throw new Error("EmailJS SDK is not loaded. Include EmailJS script before `contact-form.js`.");
    }

    const params = {
      from_name: payload.name,
      reply_to: payload.email,
      phone: payload.phone,
      subject: payload.subject,
      message: payload.message,
    };

    if (typeof window.emailjs.init === "function" && publicKey) {
      try {
        window.emailjs.init(publicKey);
      } catch (_) {
        // ignore repeated init errors
      }
    }

    await window.emailjs.send(serviceId, templateId, params, publicKey || undefined);
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const payload = getPayload();
    clearFieldErrors();
    const error = validate(payload);
    if (error) {
      setFieldInvalid(document.getElementById("contactName"), !payload.name);
      setFieldInvalid(
        document.getElementById("contactEmail"),
        !payload.email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(payload.email),
      );
      setFieldInvalid(document.getElementById("contactSubject"), !payload.subject);
      setFieldInvalid(document.getElementById("contactMessage"), !payload.message);
      setStatus(error, "error");
      focusFirstInvalid(payload);
      return;
    }

    setLoading(true);
    setStatus("Sending your message…", null);

    try {
      if (endpoint) {
        await submitToEndpoint(endpoint, payload);
      } else if (emailjsService && emailjsTemplate) {
        await submitWithEmailJS(
          { serviceId: emailjsService, templateId: emailjsTemplate, publicKey: emailjsPublicKey },
          payload,
        );
      } else {
        throw new Error(
          "No submission method configured. Set endpoint or EmailJS constants directly in assets/js/contact-form.js.",
        );
      }

      form.reset();
      if (customSelect && selectItems && selectedText) {
        selectedText.textContent = "Select a subject";
        selectItems.querySelectorAll(".select-item").forEach((i) => i.classList.remove("selected"));
        customSelect.classList.remove("open");
        selectItems.classList.add("select-hide");
      }
      setStatus("Thanks! Your message has been sent.", "success");
    } catch (e) {
      setStatus(e && e.message ? e.message : "Something went wrong. Please try again.", "error");
    } finally {
      setLoading(false);
    }
  });
}

document.addEventListener("DOMContentLoaded", initContactForm);
