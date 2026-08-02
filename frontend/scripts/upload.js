/**
 * VanRakshak AI — Upload Page
 *
 * Handles the image upload UI only: drag & drop, browse, client-side
 * validation, preview rendering, and removal. Enables the "Analyze
 * Image" button once a valid image is selected.
 *
 * No network requests are made from this file — sending the image to
 * the backend is a separate, later task.
 */

(function (document) {
  "use strict";

  /* -----------------------------------------------------
     Configuration
     ----------------------------------------------------- */
  var MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024; // 20 MB
  var ALLOWED_MIME_TYPES = ["image/jpeg", "image/jpg", "image/png"];
  var ALLOWED_EXTENSIONS = ["jpg", "jpeg", "png"];

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
   * @param {boolean} enabled
   */
  function setAnalyzeEnabled(enabled) {
    els.analyzeBtn.disabled = !enabled;
    els.analyzeBtn.setAttribute("aria-disabled", String(!enabled));
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
    // Clicking or pressing Enter/Space on the dropzone itself opens the
    // file picker too, since the whole area is a `role="button"`.
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
   * The Analyze button is intentionally inert beyond its enabled/disabled
   * state — no click handler and no network request. Sending the image
   * to the backend is implemented in a later task.
   */
  function initAnalyzeButtonState() {
    setAnalyzeEnabled(false);
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
    initAnalyzeButtonState();
    setFooterYear();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})(document);
