/**
 * VanRakshak AI — Map Page
 *
 * A standalone location selection system: fullscreen Leaflet map with
 * OpenStreetMap tiles, a Nominatim-powered search box, click-to-place
 * marker, and a sidebar reflecting the current selection.
 *
 * "Analyze" sends the selected coordinates to the backend's
 * POST /api/v1/satellite-predict endpoint, which downloads Sentinel
 * imagery and returns AI inference results to render in the sidebar.
 */

(function (window, document, L) {
  "use strict";

  /* -----------------------------------------------------
     Configuration
     ----------------------------------------------------- */
  var DEFAULT_CENTER = [22.9734, 78.6569]; // Geographic center of India
  var DEFAULT_ZOOM = 5;
  var MAX_ZOOM = 19;

  var NOMINATIM_SEARCH_URL = "https://nominatim.openstreetmap.org/search";
  var SEARCH_RESULT_LIMIT = 5;
  var SEARCH_DEBOUNCE_MS = 400;
  var SEARCH_MIN_CHARS = 3;
  var SEARCH_RESULT_ZOOM = 12;

  var TILE_URL = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png";
  var TILE_ATTRIBUTION =
    '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">OpenStreetMap</a> contributors';

  var PREDICT_ENDPOINT = "http://127.0.0.1:8000/api/v1/satellite-predict/";
  var PREDICT_REQUEST_TIMEOUT_MS = 60000; // ~60 seconds — satellite search + download + inference can take a while

  var LOADING_MESSAGES = [
    "Searching Sentinel imagery…",
    "Downloading image…",
    "Running AI model…",
  ];
  var LOADING_MESSAGE_INTERVAL_MS = 4000;

  /* -----------------------------------------------------
     State
     ----------------------------------------------------- */
  var map = null;
  var marker = null;
  var searchResults = [];
  var activeResultIndex = -1;
  var searchDebounceTimer = null;
  var loadingMessageTimer = null;
  var loadingMessageIndex = 0;

  /* -----------------------------------------------------
     Element references (populated in init)
     ----------------------------------------------------- */
  var els = {};

  /**
   * Cache references to every DOM element the page interacts with.
   */
  function cacheElements() {
    els.searchForm = document.getElementById("search-form");
    els.searchInput = document.getElementById("location-search");
    els.searchResultsList = document.getElementById("search-results");
    els.searchStatus = document.getElementById("search-status");

    els.detailLatitude = document.getElementById("detail-latitude");
    els.detailLongitude = document.getElementById("detail-longitude");
    els.detailZoom = document.getElementById("detail-zoom");

    els.sidebarHint = document.getElementById("sidebar-hint");
    els.analyzeBtn = document.getElementById("analyze-btn");
    els.resetBtn = document.getElementById("reset-btn");
    els.predictionResults = document.getElementById("prediction-results");
  }

  /* -----------------------------------------------------
     Map setup
     ----------------------------------------------------- */

  /**
   * Create the Leaflet map, add the OpenStreetMap tile layer, and wire
   * up click-to-select and zoom-tracking behavior.
   */
  function initMap() {
    map = L.map("map", {
      center: DEFAULT_CENTER,
      zoom: DEFAULT_ZOOM,
      zoomControl: true,
    });

    L.tileLayer(TILE_URL, {
      attribution: TILE_ATTRIBUTION,
      maxZoom: MAX_ZOOM,
    }).addTo(map);

    map.on("click", function (event) {
      placeMarker(event.latlng);
    });

    map.on("zoomend", updateZoomDisplay);

    updateZoomDisplay();
  }

  /**
   * Build the custom branded marker icon (an inline SVG pin, styled
   * via styles/map.css rather than Leaflet's default image marker).
   *
   * @returns {L.DivIcon}
   */
  function buildMarkerIcon() {
    var svg =
      '<svg viewBox="0 0 32 42" xmlns="http://www.w3.org/2000/svg">' +
      '<path class="marker-pin" d="M16 0C7.16 0 0 7.16 0 16c0 11 16 26 16 26s16-15 16-26C32 7.16 24.84 0 16 0Z" />' +
      '<circle class="marker-dot" cx="16" cy="16" r="6" />' +
      "</svg>";

    return L.divIcon({
      className: "map-marker-icon",
      html: svg,
      iconSize: [32, 42],
      iconAnchor: [16, 42],
      popupAnchor: [0, -38],
    });
  }

  /* -----------------------------------------------------
     Marker + sidebar sync
     ----------------------------------------------------- */

  /**
   * Place (or move) the single marker to the given position and
   * update the sidebar and Analyze button to match.
   *
   * @param {L.LatLng} latlng
   */
  function placeMarker(latlng) {
    if (marker) {
      marker.setLatLng(latlng);
    } else {
      marker = L.marker(latlng, { icon: buildMarkerIcon() }).addTo(map);
    }

    clearPredictionResults();
    updateSidebar(latlng);
    setAnalyzeEnabled(true);
  }

  /**
   * Remove the marker (if any), clear the sidebar's coordinate fields,
   * and disable the Analyze button.
   */
  function resetMarker() {
    if (marker) {
      map.removeLayer(marker);
      marker = null;
    }

    els.detailLatitude.textContent = "—";
    els.detailLongitude.textContent = "—";
    els.sidebarHint.textContent = "No location selected yet.";

    stopLoadingMessages();
    clearPredictionResults();
    setAnalyzeEnabled(false);
  }

  /**
   * Update the sidebar's latitude/longitude readout for a selected point.
   *
   * @param {L.LatLng} latlng
   */
  function updateSidebar(latlng) {
    els.detailLatitude.textContent = latlng.lat.toFixed(6);
    els.detailLongitude.textContent = latlng.lng.toFixed(6);
    els.sidebarHint.textContent = "Location selected. Ready to analyze.";
  }

  /**
   * Keep the sidebar's zoom readout in sync with the map's current
   * zoom level, independent of whether a marker is placed.
   */
  function updateZoomDisplay() {
    if (els.detailZoom) {
      els.detailZoom.textContent = String(map.getZoom());
    }
  }

  /**
   * @param {boolean} enabled
   */
  function setAnalyzeEnabled(enabled) {
    els.analyzeBtn.disabled = !enabled;
    els.analyzeBtn.setAttribute("aria-disabled", String(!enabled));
  }

  /**
   * Analyze button click handler: sends the currently selected
   * coordinates to the location API.
   */
  function handleAnalyzeClick() {
    if (!marker) {
      return;
    }

    var latlng = marker.getLatLng();
    requestPrediction(latlng.lat, latlng.lng);
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
  function createPredictionHttpError(status, data) {
    var message = "Location request failed with status " + status;
    var error = new Error(message);

    error.status = status;
    error.apiError = data && data.detail ? data.detail : null;

    return error;
  }

  /**
   * Translate a caught error (network failure, timeout, or HTTP error
   * status) into a short, friendly message safe to show in the sidebar.
   *
   * @param {Error} error
   * @returns {string}
   */
  function getFriendlyPredictionErrorMessage(error) {
    if (error && error.name === "AbortError") {
      return "The satellite request timed out. Please check your connection and try again.";
    }

    if (error && error.apiError) {
      var apiError = error.apiError;

      if (typeof apiError === "object") {
        switch (apiError.error) {
          case "SATELLITE_NETWORK_ERROR":
            return "Internet connection problem. Please check your connection and try again.";

          case "SATELLITE_QUOTA_ERROR":
            return "Sentinel Hub processing quota has been exhausted. Please try again later or check your Sentinel Hub account.";

          case "SATELLITE_AUTHENTICATION_ERROR":
            return "Satellite authentication failed. Please check the Sentinel Hub credentials.";

          case "SATELLITE_SERVICE_ERROR":
            return "Sentinel Hub is temporarily unavailable. Please try again later.";

          case "NO_SATELLITE_IMAGERY":
            return "No suitable satellite imagery is available for this location.";

          case "SATELLITE_ERROR":
            return apiError.message || "A satellite processing error occurred. Please try again.";

          default:
            return apiError.message || "The satellite analysis failed. Please try again.";
        }
      }

      if (typeof apiError === "string") {
        return apiError;
      }
    }

    if (error && typeof error.status === "number") {
      if (error.status === 400) {
        return "The server rejected these coordinates. Please choose a different point.";
      }

      if (error.status === 404) {
        return "No satellite imagery was found for this location.";
      }

      if (error.status === 429) {
        return "Sentinel Hub processing quota has been exhausted. Please try again later.";
      }

      if (error.status >= 500) {
        return "The satellite service is temporarily unavailable. Please try again shortly.";
      }

      return "The request failed (status " + error.status + "). Please try again.";
    }

    return "Unable to reach the server. Please check your connection and try again.";
  }
  /**
   * Send a coordinate pair to POST /api/v1/satellite-predict/ and reflect the
   * outcome in the sidebar.
   *
   * @param {number} latitude
   * @param {number} longitude
   */
  function requestPrediction(latitude, longitude) {
    setAnalyzeEnabled(false);
    clearPredictionResults();
    startLoadingMessages();

    fetchWithTimeout(
      PREDICT_ENDPOINT,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ latitude: latitude, longitude: longitude }),
      },
      PREDICT_REQUEST_TIMEOUT_MS
    )
      .then(function (response) {
        return response.json().then(function (data) {
          if (!response.ok) {
            throw createPredictionHttpError(response.status, data);
          }

          return data;
        });
      })
      .then(function (data) {
        renderPredictionResults(data);
        els.sidebarHint.textContent = "Analysis complete.";
      })
      .catch(function (error) {
        els.sidebarHint.textContent = getFriendlyPredictionErrorMessage(error);
      })
      .finally(function () {
        stopLoadingMessages();
        setAnalyzeEnabled(true);
      });
  }

  function startLoadingMessages() {
    loadingMessageIndex = 0;
    els.sidebarHint.textContent = LOADING_MESSAGES[loadingMessageIndex];

    loadingMessageTimer = window.setInterval(function () {
      loadingMessageIndex = (loadingMessageIndex + 1) % LOADING_MESSAGES.length;
      els.sidebarHint.textContent = LOADING_MESSAGES[loadingMessageIndex];
    }, LOADING_MESSAGE_INTERVAL_MS);
  }

  function stopLoadingMessages() {
    if (loadingMessageTimer) {
      window.clearInterval(loadingMessageTimer);
      loadingMessageTimer = null;
    }
  }

  function renderPredictionResults(data) {
    clearPredictionResults();

    if (!els.predictionResults) {
      return;
    }

    var card = document.createElement("div");
    card.className = "card";

    var eyebrow = document.createElement("p");
    eyebrow.className = "eyebrow";
    eyebrow.textContent = "Analysis Result";
    card.appendChild(eyebrow);

    var heading = document.createElement("h3");
    heading.textContent = data.prediction || "—";
    heading.style.marginBottom = "var(--space-xs)";
    card.appendChild(heading);

    var detailList = document.createElement("dl");
    detailList.className = "map-detail-list";
    detailList.appendChild(buildDetailRow("Confidence", formatPercent(data.confidence)));
    detailList.appendChild(buildDetailRow("Confidence Level", buildConfidenceBadge(data.confidence_level)));
    detailList.appendChild(buildDetailRow("Acquisition Date", formatAcquisitionDate(data.acquisition_date)));
    detailList.appendChild(buildDetailRow("Provider", data.provider || "—"));
    card.appendChild(detailList);

    if (Array.isArray(data.top3) && data.top3.length > 0) {
      var top3Heading = document.createElement("p");
      top3Heading.className = "eyebrow";
      top3Heading.textContent = "Top 3 Predictions";
      top3Heading.style.marginTop = "var(--space-md)";
      card.appendChild(top3Heading);

      var top3List = document.createElement("dl");
      top3List.className = "map-detail-list";

      data.top3.forEach(function (entry, index) {
        top3List.appendChild(
          buildDetailRow(index + 1 + ". " + entry.class, formatPercent(entry.confidence))
        );
      });

      card.appendChild(top3List);
    }

    els.predictionResults.appendChild(card);
    els.predictionResults.hidden = false;
  }

  function clearPredictionResults() {
    if (els.predictionResults) {
      els.predictionResults.innerHTML = "";
      els.predictionResults.hidden = true;
    }
  }

  function buildDetailRow(label, value) {
    var row = document.createElement("div");
    row.className = "map-detail-row";

    var term = document.createElement("dt");
    term.textContent = label;

    var description = document.createElement("dd");
    if (value instanceof Node) {
      description.appendChild(value);
    } else {
      description.textContent = value;
    }

    row.appendChild(term);
    row.appendChild(description);
    return row;
  }

  function buildConfidenceBadge(level) {
    var badge = document.createElement("span");
    badge.className = "badge badge-accent";
    badge.textContent = level || "—";
    return badge;
  }

  function formatPercent(value) {
    var numeric = Number(value);
    var formatted = isNaN(numeric) ? String(value) : numeric.toFixed(2);
    return formatted + "%";
  }

  function formatAcquisitionDate(value) {
    if (!value) {
      return "—";
    }

    var date = new Date(value);

    if (isNaN(date.getTime())) {
      return value;
    }

    return date.toLocaleDateString(undefined, { year: "numeric", month: "long", day: "numeric" });
  }

  /* -----------------------------------------------------
     Search (Nominatim)
     ----------------------------------------------------- */

  /**
   * Debounce helper local to this module, so map.js does not depend
   * on scripts/ui.js being present.
   *
   * @param {Function} fn
   * @param {number} wait
   * @returns {Function}
   */
  function debounce(fn, wait) {
    var timeoutId;
    return function debounced() {
      var args = arguments;
      var context = this;
      window.clearTimeout(timeoutId);
      timeoutId = window.setTimeout(function () {
        fn.apply(context, args);
      }, wait);
    };
  }

  /**
   * Query the Nominatim search API for a free-text location string.
   *
   * @param {string} query
   * @returns {Promise<Array<Object>>}
   */
  function searchLocations(query) {
    var url =
      NOMINATIM_SEARCH_URL +
      "?format=jsonv2&limit=" +
      SEARCH_RESULT_LIMIT +
      "&q=" +
      encodeURIComponent(query);

    return fetch(url, {
      headers: { Accept: "application/json" },
    }).then(function (response) {
      if (!response.ok) {
        throw new Error("Search request failed with status " + response.status);
      }
      return response.json();
    });
  }

  /**
   * Handle input into the search box: debounced live search once the
   * query is long enough, otherwise clear any existing results.
   */
  function handleSearchInput() {
    var query = els.searchInput.value.trim();

    if (query.length < SEARCH_MIN_CHARS) {
      clearSearchResults();
      return;
    }

    debouncedSearch(query);
  }

  var debouncedSearch = debounce(function (query) {
    runSearch(query);
  }, SEARCH_DEBOUNCE_MS);

  /**
   * Handle the search form being submitted (Enter key or button click):
   * runs the search immediately, bypassing the debounce.
   *
   * @param {Event} event
   */
  function handleSearchSubmit(event) {
    event.preventDefault();

    var query = els.searchInput.value.trim();

    if (query.length === 0) {
      return;
    }

    window.clearTimeout(searchDebounceTimer);
    runSearch(query);
  }

  /**
   * Execute a search and render the results (or a friendly status
   * message on empty results or failure).
   *
   * @param {string} query
   */
  function runSearch(query) {
    setSearchStatus("Searching…");

    searchLocations(query)
      .then(function (results) {
        renderSearchResults(results);

        if (results.length === 0) {
          setSearchStatus('No results for "' + query + '".');
        } else {
          setSearchStatus(results.length + " result" + (results.length === 1 ? "" : "s") + " found.");
        }
      })
      .catch(function () {
        clearSearchResults();
        setSearchStatus("Search failed. Please check your connection and try again.");
      });
  }

  /**
   * Render a list of Nominatim results into the results dropdown.
   *
   * @param {Array<Object>} results
   */
  function renderSearchResults(results) {
    searchResults = results;
    activeResultIndex = -1;

    els.searchResultsList.innerHTML = "";

    if (results.length === 0) {
      els.searchResultsList.hidden = true;
      els.searchInput.setAttribute("aria-expanded", "false");
      return;
    }

    results.forEach(function (result, index) {
      var item = document.createElement("li");
      item.className = "map-search-result";
      item.id = "search-result-" + index;
      item.setAttribute("role", "option");
      item.setAttribute("tabindex", "-1");
      item.textContent = result.display_name;

      item.addEventListener("click", function () {
        selectSearchResult(result);
      });

      els.searchResultsList.appendChild(item);
    });

    els.searchResultsList.hidden = false;
    els.searchInput.setAttribute("aria-expanded", "true");
  }

  /**
   * Clear the results dropdown and reset related ARIA state.
   */
  function clearSearchResults() {
    searchResults = [];
    activeResultIndex = -1;
    els.searchResultsList.innerHTML = "";
    els.searchResultsList.hidden = true;
    els.searchInput.setAttribute("aria-expanded", "false");
    els.searchInput.setAttribute("aria-activedescendant", "");
  }

  /**
   * @param {string} message
   */
  function setSearchStatus(message) {
    els.searchStatus.textContent = message;
  }

  /**
   * Center (and zoom) the map on a chosen search result, then close
   * the results dropdown. Does not place a marker — only clicking the
   * map places a marker, per the page's design.
   *
   * @param {Object} result - A single Nominatim search result.
   */
  function selectSearchResult(result) {
    var lat = parseFloat(result.lat);
    var lon = parseFloat(result.lon);

    if (isNaN(lat) || isNaN(lon)) {
      return;
    }

    if (result.boundingbox && result.boundingbox.length === 4) {
      var bounds = [
        [parseFloat(result.boundingbox[0]), parseFloat(result.boundingbox[2])],
        [parseFloat(result.boundingbox[1]), parseFloat(result.boundingbox[3])],
      ];
      map.fitBounds(bounds, { maxZoom: SEARCH_RESULT_ZOOM + 3 });
    } else {
      map.setView([lat, lon], SEARCH_RESULT_ZOOM);
    }

    els.searchInput.value = result.display_name;
    clearSearchResults();
    setSearchStatus("Centered on " + result.display_name + ".");
    els.searchInput.focus();
  }

  /**
   * Basic keyboard navigation for the results dropdown: Arrow keys
   * move the highlighted option, Enter selects it, Escape closes it.
   *
   * @param {KeyboardEvent} event
   */
  function handleSearchKeydown(event) {
    if (els.searchResultsList.hidden || searchResults.length === 0) {
      return;
    }

    if (event.key === "ArrowDown") {
      event.preventDefault();
      moveActiveResult(1);
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      moveActiveResult(-1);
    } else if (event.key === "Enter" && activeResultIndex >= 0) {
      event.preventDefault();
      selectSearchResult(searchResults[activeResultIndex]);
    } else if (event.key === "Escape") {
      clearSearchResults();
    }
  }

  /**
   * @param {number} delta - +1 to move down the list, -1 to move up.
   */
  function moveActiveResult(delta) {
    var items = els.searchResultsList.querySelectorAll(".map-search-result");

    if (items.length === 0) {
      return;
    }

    if (activeResultIndex >= 0 && items[activeResultIndex]) {
      items[activeResultIndex].classList.remove("is-active");
    }

    activeResultIndex = (activeResultIndex + delta + items.length) % items.length;

    var activeItem = items[activeResultIndex];
    activeItem.classList.add("is-active");
    activeItem.scrollIntoView({ block: "nearest" });

    els.searchInput.setAttribute("aria-activedescendant", activeItem.id);
  }

  /**
   * Close the results dropdown when focus leaves the search area
   * entirely (accounts for the click-to-select handler above still
   * needing to fire first).
   *
   * @param {FocusEvent} event
   */
  function handleSearchBlur(event) {
    var nextFocusTarget = event.relatedTarget;

    if (!els.searchForm.contains(nextFocusTarget) && !els.searchResultsList.contains(nextFocusTarget)) {
      window.setTimeout(clearSearchResults, 150);
    }
  }

  /* -----------------------------------------------------
     Event wiring
     ----------------------------------------------------- */

  function initSearch() {
    els.searchForm.addEventListener("submit", handleSearchSubmit);
    els.searchInput.addEventListener("input", handleSearchInput);
    els.searchInput.addEventListener("keydown", handleSearchKeydown);
    els.searchInput.addEventListener("blur", handleSearchBlur);
  }

  function initSidebarActions() {
    els.analyzeBtn.addEventListener("click", handleAnalyzeClick);
    els.resetBtn.addEventListener("click", resetMarker);
  }

  /* -----------------------------------------------------
     Init
     ----------------------------------------------------- */
  function init() {
    cacheElements();
    initMap();
    initSearch();
    initSidebarActions();
    setAnalyzeEnabled(false);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})(window, document, window.L);