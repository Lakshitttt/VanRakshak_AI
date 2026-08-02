/**
 * VanRakshak AI — Shared UI Layer
 *
 * Reusable, page-agnostic JavaScript for the design system:
 *  - Mobile navigation toggle
 *  - Scroll-triggered reveal animations
 *  - Smooth in-page scrolling (with sticky navbar offset)
 *  - Shared DOM/utility helpers
 *  - Animation helpers (stagger, page fade-in)
 *
 * No upload logic and no API calls live here — pages that need
 * those wire them up separately, using the helpers below.
 *
 * Everything is exposed under a single global namespace,
 * `window.VanRakshakUI`, so any page can call individual pieces
 * (e.g. `VanRakshakUI.qs`, `VanRakshakUI.staggerReveal`) instead
 * of relying only on the automatic init on page load.
 */

(function (window, document) {
  "use strict";

  /* -----------------------------------------------------
     DOM helpers
     ----------------------------------------------------- */

  /**
   * Shorthand for `document.querySelector`, optionally scoped.
   *
   * @param {string} selector - CSS selector to match.
   * @param {ParentNode} [scope=document] - Element to search within.
   * @returns {Element|null} The first matching element, or null.
   */
  function qs(selector, scope) {
    return (scope || document).querySelector(selector);
  }

  /**
   * Shorthand for `document.querySelectorAll`, returned as a
   * real array so array methods (forEach, map, filter) work
   * directly on the result.
   *
   * @param {string} selector - CSS selector to match.
   * @param {ParentNode} [scope=document] - Element to search within.
   * @returns {Element[]} All matching elements.
   */
  function qsa(selector, scope) {
    return Array.prototype.slice.call((scope || document).querySelectorAll(selector));
  }

  /**
   * Run a callback once the DOM is ready, or immediately if it
   * already is.
   *
   * @param {Function} callback - Function to run on DOM ready.
   */
  function onReady(callback) {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", callback);
    } else {
      callback();
    }
  }

  /* -----------------------------------------------------
     Function utilities
     ----------------------------------------------------- */

  /**
   * Return a debounced version of `fn` that only runs after
   * `wait` milliseconds have passed without it being called
   * again. Useful for resize/input handlers.
   *
   * @param {Function} fn - Function to debounce.
   * @param {number} [wait=150] - Delay in milliseconds.
   * @returns {Function} The debounced function.
   */
  function debounce(fn, wait) {
    var timeoutId;
    var delay = typeof wait === "number" ? wait : 150;

    return function debounced() {
      var args = arguments;
      var context = this;
      window.clearTimeout(timeoutId);
      timeoutId = window.setTimeout(function () {
        fn.apply(context, args);
      }, delay);
    };
  }

  /**
   * Return a throttled version of `fn` that runs at most once
   * every `wait` milliseconds. Useful for scroll handlers.
   *
   * @param {Function} fn - Function to throttle.
   * @param {number} [wait=150] - Minimum gap in milliseconds.
   * @returns {Function} The throttled function.
   */
  function throttle(fn, wait) {
    var isWaiting = false;
    var delay = typeof wait === "number" ? wait : 150;

    return function throttled() {
      var args = arguments;
      var context = this;

      if (isWaiting) {
        return;
      }

      isWaiting = true;
      fn.apply(context, args);
      window.setTimeout(function () {
        isWaiting = false;
      }, delay);
    };
  }

  /* -----------------------------------------------------
     Mobile navigation toggle
     Works with the `.nav-toggle` / `.nav-links` components
     in components.css. The toggle button's `aria-controls`
     attribute must point to the id of the links list.
     ----------------------------------------------------- */

  /**
   * Wire up every `.nav-toggle` button on the page so it opens
   * and closes its associated `.nav-links` element and keeps
   * `aria-expanded` in sync.
   */
  function initNavToggle() {
    qsa(".nav-toggle").forEach(function (toggle) {
      var targetId = toggle.getAttribute("aria-controls");
      var links = targetId ? document.getElementById(targetId) : null;

      if (!links) {
        return;
      }

      toggle.addEventListener("click", function () {
        var isOpen = links.classList.toggle("is-open");
        toggle.setAttribute("aria-expanded", String(isOpen));
      });

      // Close the mobile menu once a link is chosen.
      links.addEventListener("click", function (event) {
        if (event.target.tagName === "A") {
          links.classList.remove("is-open");
          toggle.setAttribute("aria-expanded", "false");
        }
      });

      // Close on Escape for keyboard users.
      document.addEventListener("keydown", function (event) {
        if (event.key === "Escape" && links.classList.contains("is-open")) {
          links.classList.remove("is-open");
          toggle.setAttribute("aria-expanded", "false");
          toggle.focus();
        }
      });
    });
  }

  /* -----------------------------------------------------
     Scroll reveal
     Adds `.is-visible` to any `.reveal` element as it enters
     the viewport, driving the CSS transitions defined in
     animations.css.
     ----------------------------------------------------- */

  /**
   * Observe every `.reveal` element on the page and mark it
   * `.is-visible` once it scrolls into view. Falls back to
   * revealing everything immediately if IntersectionObserver
   * is unavailable. Supports an optional `data-reveal-delay`
   * attribute (milliseconds) for manual stagger control.
   */
  function initScrollReveal() {
    var revealElements = qsa(".reveal");

    if (revealElements.length === 0) {
      return;
    }

    if (!("IntersectionObserver" in window)) {
      revealElements.forEach(function (el) {
        el.classList.add("is-visible");
      });
      return;
    }

    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) {
            return;
          }

          var el = entry.target;
          var delay = parseInt(el.getAttribute("data-reveal-delay") || "0", 10);

          if (delay > 0) {
            window.setTimeout(function () {
              el.classList.add("is-visible");
            }, delay);
          } else {
            el.classList.add("is-visible");
          }

          observer.unobserve(el);
        });
      },
      { threshold: 0.15, rootMargin: "0px 0px -40px 0px" }
    );

    revealElements.forEach(function (el) {
      observer.observe(el);
    });
  }

  /**
   * Reveal a group of elements matched by `selector` one after
   * another, `stepMs` apart, by setting `data-reveal-delay`
   * before scroll observation begins. Call before
   * `initScrollReveal` (or re-run reveal observation) for the
   * delays to take effect.
   *
   * @param {string} selector - CSS selector for the group.
   * @param {number} [stepMs=100] - Delay increment per element.
   */
  function staggerReveal(selector, stepMs) {
    var step = typeof stepMs === "number" ? stepMs : 100;

    qsa(selector).forEach(function (el, index) {
      el.classList.add("reveal");
      el.setAttribute("data-reveal-delay", String(index * step));
    });
  }

  /* -----------------------------------------------------
     Smooth in-page scrolling
     Accounts for the sticky navbar height so anchored
     sections aren't hidden underneath it.
     ----------------------------------------------------- */

  /**
   * Intercept clicks on same-page anchor links (`href="#id"`)
   * and scroll to the target smoothly, offset by the height of
   * a sticky `.navbar` if one is present.
   */
  function initSmoothScroll() {
    var navbar = qs(".navbar");

    qsa('a[href^="#"]').forEach(function (link) {
      link.addEventListener("click", function (event) {
        var targetId = link.getAttribute("href");

        if (!targetId || targetId === "#") {
          return;
        }

        var target = qs(targetId);

        if (!target) {
          return;
        }

        event.preventDefault();

        var offset = navbar ? navbar.getBoundingClientRect().height : 0;
        var targetPosition = target.getBoundingClientRect().top + window.pageYOffset - offset - 12;

        window.scrollTo({
          top: targetPosition,
          behavior: prefersReducedMotion() ? "auto" : "smooth",
        });

        // Move focus for keyboard/screen-reader users once scrolling settles.
        target.setAttribute("tabindex", "-1");
        target.focus({ preventScroll: true });
      });
    });
  }

  /**
   * @returns {boolean} True if the user has requested reduced motion.
   */
  function prefersReducedMotion() {
    return (
      window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches
    );
  }

  /* -----------------------------------------------------
     Page transition
     Fades the main content in on load using the
     `.page-fade-in` utility from animations.css.
     ----------------------------------------------------- */

  /**
   * Add the `.page-fade-in` animation class to the page's
   * `<main>` element (or a custom target) once the DOM is ready.
   *
   * @param {string} [selector="main"] - Element to fade in.
   */
  function initPageTransition(selector) {
    var target = qs(selector || "main");

    if (target) {
      target.classList.add("page-fade-in");
    }
  }

  /* -----------------------------------------------------
     Auto-init
     ----------------------------------------------------- */
  onReady(function () {
    initNavToggle();
    initScrollReveal();
    initSmoothScroll();
    initPageTransition();
  });

  /* -----------------------------------------------------
     Public namespace
     ----------------------------------------------------- */
  window.VanRakshakUI = {
    qs: qs,
    qsa: qsa,
    onReady: onReady,
    debounce: debounce,
    throttle: throttle,
    initNavToggle: initNavToggle,
    initScrollReveal: initScrollReveal,
    staggerReveal: staggerReveal,
    initSmoothScroll: initSmoothScroll,
    initPageTransition: initPageTransition,
    prefersReducedMotion: prefersReducedMotion,
  };
})(window, document);
