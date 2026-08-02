/**
 * VanRakshak AI — Upload Page
 *
 * Handles the image upload UI: drag & drop, browse, client-side
 * validation, preview rendering, removal, sending the selected image
 * to the prediction API, and — now — rendering the result as a
 * dynamically built card with a reset-to-upload action.
 */

(function (document) {
  "use strict";

  /* -----------------------------------------------------
     Configuration
     ----------------------------------------------------- */
  var MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024; // 20 MB
  var ALLOWED_MIME_TYPES = ["image/jpeg", "image/jpg", "image/png"];
  var ALLOWED_EXTENSIONS = ["jpg", "jpeg", "png"];

  var PREDICT_ENDPOINT = "http://127.0.0.1:8000/api/v1/predict";
  var REQUEST_TIMEOUT_MS = 30000; // 30 seconds

  var ANALYZE_LABEL_DEFAULT = "Analyze Image";
  var ANALYZE_LABEL_LOADING = "Analyzing...";

  var RESULT_CARD_ID = "result-card";
  var RESULT_ANIMATION_MS = 300;

  /* -----------------------------------------------------
     State
     ----------------------------------------------------- */
  var state = {
    file: null,
    objectUrl: null,
  };

  /* -----------------------------------------------------
     Element references (populated in init)
     ----------------------------------------------------- */
  var els = {};

  /**
   * Cache references to every DOM element the page interacts with.
   */
  function cacheElements() {
    els.dropzone = document.getElementById("dropzone");
    els.fileInput = document.getElementById("file-input");
    els.browseBtn = document.getElementById("browse-btn");
    els.removeBtn = document.getElementById("remove-btn");
    els.analyzeBtn = document.getElementById("analyze-btn");

    els.errorMessage = document.getElementById("upload-error");
    els.emptyState = document.getElementById("upload-empty-state");
    els.preview = document.getElementById("upload-preview");

    els.previewImage = document.getElementById("preview-image");
    els.previewFilename = document.getElementById("preview-filename");
    els.previewDimensions = document.getElementById("preview-dimensions");
    els.previewFilesize = document.getElementById("preview-filesize");

    els.currentYear = document.getElementById("current-year");

    // Sections toggled between the "uploading" and "result" states.
    els.uploadPanel = document.querySelector(".upload-panel");
    els.uploadActions = document.querySelector(".upload-actions");
    els.resultContainer = document.getElementById("result-container");
  }

  /* -----------------------------------------------------
     Validation
     ----------------------------------------------------- */

  /**
   * Determine whether a File is an acceptable satellite image upload.
   *
   * @param {File} file - The file the user selected or dropped.
   * @returns {{ valid: boolean, error: string|null }} Validation result.
   */
  function validateFile(file) {
    var extension = getFileExtension(file.name);

    var hasAllowedExtension = ALLOWED_EXTENSIONS.indexOf(extension) !== -1;
    var hasAllowedType = file.type === "" || ALLOWED_MIME_TYPES.indexOf(file.type) !== -1;

    if (!hasAllowedExtension || !hasAllowedType) {
      return {
        valid: false,
        error: "Unsupported file format. Please upload a JPG, JPEG, or PNG image.",
      };
    }

    if (file.size > MAX_FILE_SIZE_BYTES) {
      return {
        valid: false,
        error: "That file is larger than the 20 MB limit. Please choose a smaller image.",
      };
    }

    if (file.size === 0) {
      return {
        valid: false,
        error: "That file appears to be empty. Please choose a different image.",
      };
    }

    return { valid: true, error: null };
  }

  /**
   * @param {string} filename
   * @returns {string} The lowercase file extension, without the dot.
   */
  function getFileExtension(filename) {
    var parts = filename.split(".");
    return parts.length > 1 ? parts.pop().toLowerCase() : "";
  }

  /* -----------------------------------------------------
     File handling
     ----------------------------------------------------- */

  /**
   * Validate and, if acceptable, load a file into the preview.
   *
   * @param {File|undefined} file - The candidate file.
   */
  function handleFile(file) {
    if (!file) {
      return;
    }

    var result = validateFile(file);

    if (!result.valid) {
      showError(result.error);
      return;
    }

    clearError();
    loadPreview(file);
  }

  /**
   * Read image dimensions and render the preview panel for a valid file.
   *
   * @param {File} file - A file that has already passed validation.
   */
  function loadPreview(file) {
    revokeCurrentObjectUrl();

    var objectUrl = URL.createObjectURL(file);
    var probeImage = new Image();

    probeImage.onload = function () {
      state.file = file;
      state.objectUrl = objectUrl;

      renderPreview(file, probeImage.naturalWidth, probeImage.naturalHeight, objectUrl);
    };

    probeImage.onerror = function () {
      URL.revokeObjectURL(objectUrl);
      showError("That image could not be read. It may be corrupted.");
    };

    probeImage.src = objectUrl;
  }

  /**
   * Populate and reveal the preview panel; hide the empty state; enable
   * the Analyze button.
   *
   * @param {File} file
   * @param {number} width
   * @param {number} height
   * @param {string} objectUrl
   */
  function renderPreview(file, width, height, objectUrl) {
    els.previewImage.src = objectUrl;
    els.previewImage.alt = "Preview of " + file.name;

    els.previewFilename.textContent = file.name;
    els.previewDimensions.textContent = width + " × " + height + " px";
    els.previewFilesize.textContent = formatFileSize(file.size);

    els.emptyState.hidden = true;
    els.preview.hidden = false;

    setAnalyzeEnabled(true);
  }

  /**
   * Reset the page back to its empty state and release any object URL.
   */
  function removeImage() {
    revokeCurrentObjectUrl();
    state.file = null;

    els.fileInput.value = "";
    els.previewImage.src = "";
    els.previewImage.alt = "";
    els.previewFilename.textContent = "—";
    els.previewDimensions.textContent = "—";
    els.previewFilesize.textContent = "—";

    els.preview.hidden = true;
    els.emptyState.hidden = false;

    clearError();
    setAnalyzeEnabled(false);
  }

  /**
   * Revoke the currently tracked object URL, if any, to avoid leaking
   * memory when a file is replaced or removed.
   */
  function revokeCurrentObjectUrl() {
    if (state.objectUrl) {
      URL.revokeObjectURL(state.objectUrl);
      state.objectUrl = null;
    }
  }

  /**
   * @param {number} bytes
   * @returns {string} A human-readable file size (e.g. "3.4 MB").
   */
  function formatFileSize(bytes) {
    if (bytes < 1024) {
      return bytes + " B";
    }

    var kilobytes = bytes / 1024;

    if (kilobytes < 1024) {
      return kilobytes.toFixed(1) + " KB";
    }

    var megabytes = kilobytes / 1024;
    return megabytes.toFixed(1) + " MB";
  }

  /* -----------------------------------------------------
     UI state helpers
     ----------------------------------------------------- */

  /**
   * @param {string} message
   */
  function showError(message) {
    els.errorMessage.textContent = message;
    els.errorMessage.hidden = false;
    els.dropzone.classList.add("dropzone--error");
  }

  function clearError() {
    els.errorMessage.textContent = "";
    els.errorMessage.hidden = true;
    els.dropzone.classList.remove("dropzone--error");
  }

  /**
   * Enable/disable the Analyze button based on whether a valid image
   * is currently selected. Distinct from `setAnalyzeLoading`, which
   * temporarily disables the button while a request is in flight.
   *
   * @param {boolean} enabled
   */
  function setAnalyzeEnabled(enabled) {
    els.analyzeBtn.disabled = !enabled;
    els.analyzeBtn.setAttribute("aria-disabled", String(!enabled));
  }

  /**
   * Restructure the Analyze button's contents into a label span (and,
   * on demand, a spinner) so its text can be swapped without touching
   * the button's own attributes. Runs once and is safe to call again.
   */
  function ensureAnalyzeButtonStructure() {
    if (els.analyzeBtn.querySelector(".btn-label")) {
      return;
    }

    var originalText = els.analyzeBtn.textContent.trim() || ANALYZE_LABEL_DEFAULT;

    els.analyzeBtn.textContent = "";

    var label = document.createElement("span");
    label.className = "btn-label";
    label.textContent = originalText;

    els.analyzeBtn.appendChild(label);
  }

  /**
   * Toggle the Analyze button's loading state: disables the button,
   * swaps its label between "Analyze Image" and "Analyzing...", and
   * shows/hides a small spinner using the shared `.spinner` component
   * already defined in the design system's components.css.
   *
   * @param {boolean} isLoading
   */
  function setAnalyzeLoading(isLoading) {
    var label = els.analyzeBtn.querySelector(".btn-label");
    var existingSpinner = els.analyzeBtn.querySelector(".spinner");

    els.analyzeBtn.disabled = isLoading;
    els.analyzeBtn.setAttribute("aria-busy", String(isLoading));

    if (label) {
      label.textContent = isLoading ? ANALYZE_LABEL_LOADING : ANALYZE_LABEL_DEFAULT;
    }

    if (isLoading && !existingSpinner) {
      var spinner = document.createElement("span");
      spinner.className = "spinner spinner-sm";
      spinner.setAttribute("aria-hidden", "true");
      els.analyzeBtn.insertBefore(spinner, els.analyzeBtn.firstChild);
    }

    if (!isLoading && existingSpinner) {
      existingSpinner.remove();
    }
  }

  /* -----------------------------------------------------
     Prediction API call
     ----------------------------------------------------- */

  /**
   * Build the multipart/form-data payload expected by the prediction
   * endpoint: a single `image` field containing the file.
   *
   * @param {File} file
   * @returns {FormData}
   */
  function buildPredictionFormData(file) {
    var formData = new FormData();
    formData.append("image", file);
    return formData;
  }

  /**
   * Run `fetch` with a hard timeout, aborting the request if it takes
   * longer than `timeoutMs`. A timed-out request rejects with a
   * DOMException named "AbortError", which callers can detect.
   *
   * @param {string} url
   * @param {RequestInit} options
   * @param {number} timeoutMs
   * @returns {Promise<Response>}
   */
  function fetchWithTimeout(url, options, timeoutMs) {
    var controller = new AbortController();
    var timeoutId = window.setTimeout(function () {
      controller.abort();
    }, timeoutMs);

    var requestOptions = Object.assign({}, options, { signal: controller.signal });

    return fetch(url, requestOptions).finally(function () {
      window.clearTimeout(timeoutId);
    });
  }

  /**
   * Build an Error carrying the HTTP status code, so callers can branch
   * on it without re-parsing the response.
   *
   * @param {number} status
   * @returns {Error}
   */
  function createHttpError(status) {
    var error = new Error("Prediction request failed with status " + status);
    error.status = status;
    return error;
  }

  /**
   * Translate a caught error (network failure, timeout, or HTTP error
   * status) into a short, friendly message safe to show the user.
   *
   * @param {Error} error
   * @returns {string}
   */
  function getFriendlyErrorMessage(error) {
    if (error && error.name === "AbortError") {
      return "The request took too long and timed out. Please check your connection and try again.";
    }

    if (error && typeof error.status === "number") {
      if (error.status === 400 || error.status === 422) {
        return "The server could not process this image. Please try a different file.";
      }

      if (error.status >= 500) {
        return "The server ran into a problem analyzing this image. Please try again shortly.";
      }

      return "The analysis request failed (status " + error.status + "). Please try again.";
    }

    return "Unable to reach the analysis server. Please check your connection and try again.";
  }

  /**
   * Send the currently selected image to the prediction API, render
   * the result card on success, and manage loading/error state around
   * the request.
   *
   * @param {File} file
   */
  function analyzeImage(file) {
    clearError();
    setAnalyzeLoading(true);

    var formData = buildPredictionFormData(file);

    fetchWithTimeout(
      PREDICT_ENDPOINT,
      {
        method: "POST",
        body: formData,
      },
      REQUEST_TIMEOUT_MS
    )
      .then(function (response) {
        if (!response.ok) {
          throw createHttpError(response.status);
        }
        return response.json();
      })
      .then(function (result) {
        console.log("Prediction result:", result);
        showResult(result);
      })
      .catch(function (error) {
        showError(getFriendlyErrorMessage(error));
      })
      .finally(function () {
        setAnalyzeLoading(false);
      });
  }

  /**
   * Click handler for the Analyze button: verifies an image is
   * actually selected before doing anything else.
   *
   * @param {MouseEvent} event
   */
  function handleAnalyzeClick(event) {
    event.preventDefault();

    if (!state.file) {
      showError("Please select an image before analyzing.");
      return;
    }

    analyzeImage(state.file);
  }

  /* -----------------------------------------------------
     Result card
     ----------------------------------------------------- */

  /**
   * @returns {boolean} True if the user has requested reduced motion.
   */
  function prefersReducedMotion() {
    return (
      window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches
    );
  }

  /**
   * Hide the upload panel and Analyze button, then mount and animate
   * in a result card built from the prediction response.
   *
   * @param {{class: string, confidence: number}} result
   */
  function showResult(result) {
    hideUploadUI();

    var card = buildResultCard(result);
    mountResultCard(card);
    animateResultCardIn(card);
  }

  /**
   * Build the result card element from scratch. Reuses existing
   * design-system classes (`.card`, `.upload-detail-list`,
   * `.upload-detail-row`, `.badge`, `.btn`) — no new CSS is introduced.
   *
   * @param {{class: string, confidence: number}} result
   * @returns {HTMLElement}
   */
  function buildResultCard(result) {
    var card = document.createElement("div");
    card.id = RESULT_CARD_ID;
    card.className = "card";
    card.setAttribute("role", "status");

    var reduceMotion = prefersReducedMotion();

    if (!reduceMotion) {
      card.style.opacity = "0";
      card.style.transform = "translateY(20px)";
      card.style.transition =
        "opacity " + RESULT_ANIMATION_MS + "ms ease, transform " + RESULT_ANIMATION_MS + "ms ease";
    }

    var title = document.createElement("h3");
    title.textContent = "Prediction Complete";
    card.appendChild(title);

    var detailList = document.createElement("dl");
    detailList.className = "upload-detail-list";
    detailList.appendChild(createDetailRow("🌳 Predicted Class", String(result.class)));
    detailList.appendChild(createDetailRow("🎯 Confidence", formatConfidence(result.confidence)));
    card.appendChild(detailList);

    var badge = document.createElement("span");
    badge.className = "badge badge-accent";
    badge.textContent = "✔ Analysis Finished Successfully";
    card.appendChild(badge);

    var resetBtn = document.createElement("button");
    resetBtn.type = "button";
    resetBtn.className = "btn btn-secondary";
    resetBtn.textContent = "Analyze Another Image";
    resetBtn.addEventListener("click", handleAnalyzeAnotherClick);
    card.appendChild(resetBtn);

    return card;
  }

  /**
   * @param {string} label
   * @param {string} value
   * @returns {HTMLElement} A `.upload-detail-row` with a term/value pair.
   */
  function createDetailRow(label, value) {
    var row = document.createElement("div");
    row.className = "upload-detail-row";

    var term = document.createElement("dt");
    term.textContent = label;

    var value_ = document.createElement("dd");
    value_.textContent = value;

    row.appendChild(term);
    row.appendChild(value_);

    return row;
  }

  /**
   * @param {number|string} confidence
   * @returns {string} Confidence formatted to two decimal places with a
   *   percent sign (e.g. 96.31 -> "96.31%").
   */
  function formatConfidence(confidence) {
    var numeric = Number(confidence);
    var formatted = isNaN(numeric) ? String(confidence) : numeric.toFixed(2);
    return formatted + "%";
  }

  /**
   * Insert the result card into `#result-container`. Falls back to
   * placing it after the Analyze button if that container is missing
   * from the page, and logs a warning so the placeholder can be added.
   *
   * @param {HTMLElement} card
   */
  function mountResultCard(card) {
    removeExistingResultCard();

    if (els.resultContainer) {
      els.resultContainer.appendChild(card);
      return;
    }

    console.warn(
      'upload.js: no element with id="result-container" found in upload.html; ' +
        "appending the result card after the Analyze button instead."
    );
    els.analyzeBtn.parentNode.appendChild(card);
  }

  function removeExistingResultCard() {
    var existing = document.getElementById(RESULT_CARD_ID);
    if (existing) {
      existing.remove();
    }
  }

  /**
   * Transition the result card from its initial hidden state to fully
   * visible — a 300ms fade in combined with an upward slide.
   *
   * @param {HTMLElement} card
   */
  function animateResultCardIn(card) {
    if (prefersReducedMotion()) {
      return;
    }

    // Double rAF ensures the browser has committed the initial styles
    // before the transition to the final state begins.
    window.requestAnimationFrame(function () {
      window.requestAnimationFrame(function () {
        card.style.opacity = "1";
        card.style.transform = "translateY(0)";
      });
    });
  }

  /**
   * Reveal the upload panel and Analyze button again after a result
   * has been shown.
   */
  function hideUploadUI() {
    if (els.uploadPanel) {
      els.uploadPanel.hidden = true;
    }
    if (els.uploadActions) {
      els.uploadActions.hidden = true;
    }
  }

  function showUploadUI() {
    if (els.uploadPanel) {
      els.uploadPanel.hidden = false;
    }
    if (els.uploadActions) {
      els.uploadActions.hidden = false;
    }
  }

  /**
   * "Analyze Another Image" click handler: removes the result card,
   * restores the upload UI, and clears the previously selected file.
   */
  function handleAnalyzeAnotherClick() {
    removeExistingResultCard();
    showUploadUI();
    removeImage();
    els.analyzeBtn.focus();
  }

  /* -----------------------------------------------------
     Event wiring
     ----------------------------------------------------- */

  function initBrowse() {
    els.browseBtn.addEventListener("click", function (event) {
      event.stopPropagation();
      els.fileInput.click();
    });

    els.fileInput.addEventListener("change", function () {
      handleFile(els.fileInput.files && els.fileInput.files[0]);
    });
  }

  function initDropzone() {
    els.dropzone.addEventListener("click", function () {
      els.fileInput.click();
    });

    els.dropzone.addEventListener("keydown", function (event) {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        els.fileInput.click();
      }
    });

    ["dragenter", "dragover"].forEach(function (eventName) {
      els.dropzone.addEventListener(eventName, function (event) {
        event.preventDefault();
        event.stopPropagation();
        els.dropzone.classList.add("dropzone--active");
      });
    });

    ["dragleave", "dragend"].forEach(function (eventName) {
      els.dropzone.addEventListener(eventName, function (event) {
        event.preventDefault();
        event.stopPropagation();
        els.dropzone.classList.remove("dropzone--active");
      });
    });

    els.dropzone.addEventListener("drop", function (event) {
      event.preventDefault();
      event.stopPropagation();
      els.dropzone.classList.remove("dropzone--active");

      var files = event.dataTransfer && event.dataTransfer.files;
      handleFile(files && files[0]);
    });
  }

  function initRemove() {
    els.removeBtn.addEventListener("click", function (event) {
      event.stopPropagation();
      removeImage();
    });
  }

  /**
   * Prepare the Analyze button's internal structure and wire its click
   * handler. The button starts disabled; `setAnalyzeEnabled` (called
   * from preview/remove flows) controls availability from here on.
   */
  function initAnalyze() {
    ensureAnalyzeButtonStructure();
    setAnalyzeEnabled(false);

    els.analyzeBtn.addEventListener("click", handleAnalyzeClick);
  }

  function setFooterYear() {
    if (els.currentYear) {
      els.currentYear.textContent = String(new Date().getFullYear());
    }
  }

  /* -----------------------------------------------------
     Init
     ----------------------------------------------------- */
  function init() {
    cacheElements();
    initBrowse();
    initDropzone();
    initRemove();
    initAnalyze();
    setFooterYear();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})(document);
