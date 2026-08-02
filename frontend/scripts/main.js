/**
 * VanRakshak AI — Frontend Foundation
 *
 * Small, dependency-free interaction layer for the landing page:
 *  - Mobile navigation toggle
 *  - Scroll-triggered reveal animations (IntersectionObserver)
 *  - Footer copyright year
 *
 * No frameworks. No upload, prediction, or map logic lives here —
 * this file only supports the static landing page shell.
 */

(function () {
  "use strict";

  /**
   * Wire up the mobile navigation toggle button so it opens/closes the
   * nav link list and keeps its aria-expanded state in sync.
   */
  function initNavToggle() {
    var toggle = document.querySelector(".nav-toggle");
    var links = document.getElementById("primary-nav-links");

    if (!toggle || !links) {
      return;
    }

    toggle.addEventListener("click", function () {
      var isOpen = links.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", String(isOpen));
    });

    // Close the mobile menu after a link is chosen.
    links.addEventListener("click", function (event) {
      if (event.target.tagName === "A") {
        links.classList.remove("is-open");
        toggle.setAttribute("aria-expanded", "false");
      }
    });
  }

  /**
   * Reveal elements marked with the `.reveal` class as they scroll into
   * view, using IntersectionObserver rather than a scroll listener.
   * Falls back to showing everything immediately if the API is
   * unavailable.
   */
  function initScrollReveal() {
    var revealElements = document.querySelectorAll(".reveal");

    if (!("IntersectionObserver" in window)) {
      revealElements.forEach(function (el) {
        el.classList.add("is-visible");
      });
      return;
    }

    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.15, rootMargin: "0px 0px -40px 0px" }
    );

    revealElements.forEach(function (el) {
      observer.observe(el);
    });
  }

  /**
   * Keep the footer copyright year current without hardcoding it.
   */
  function initFooterYear() {
    var yearEl = document.getElementById("current-year");

    if (!yearEl) {
      return;
    }

    yearEl.textContent = String(new Date().getFullYear());
  }

  document.addEventListener("DOMContentLoaded", function () {
    initNavToggle();
    initScrollReveal();
    initFooterYear();
  });
})();
