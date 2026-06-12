/**
 * Main application logic.
 *
 * Responsibilities:
 *   - Tab switching (input method, analytics)
 *   - Live character counter with colour feedback
 *   - File drag-and-drop upload → /api/upload
 *   - Summarize form → /api/summarize
 *   - Render results (stats, summary text, keywords, chart, score list)
 *   - Export buttons → /api/export
 *   - Copy to clipboard
 *   - Toast notifications
 */

(function () {
  "use strict";

  // ── State ────────────────────────────────────────────────────────────────

  let uploadedText = "";     // text extracted from uploaded file
  let lastSummary  = "";     // most recent summary for export

  // ── DOM refs ─────────────────────────────────────────────────────────────

  const textInput       = document.getElementById("textInput");
  const charCount       = document.getElementById("charCount");
  const textError       = document.getElementById("textError");
  const fileInput       = document.getElementById("fileInput");
  const uploadZone      = document.getElementById("uploadZone");
  const uploadStatus    = document.getElementById("uploadStatus");
  const methodSelect    = document.getElementById("methodSelect");
  const ratioSlider     = document.getElementById("ratioSlider");
  const ratioValue      = document.getElementById("ratioValue");
  const summarizeBtn    = document.getElementById("summarizeBtn");
  const btnText         = summarizeBtn.querySelector(".btn-text");
  const btnSpinner      = summarizeBtn.querySelector(".btn-spinner");

  const emptyState      = document.getElementById("emptyState");
  const results         = document.getElementById("results");
  const statOriginal    = document.getElementById("statOriginal");
  const statSummary     = document.getElementById("statSummary");
  const statReduced     = document.getElementById("statReduced");
  const summaryText     = document.getElementById("summaryText");
  const copyBtn         = document.getElementById("copyBtn");
  const keywordCloud    = document.getElementById("keywordCloud");
  const scoreList       = document.getElementById("scoreList");
  const exportTxt       = document.getElementById("exportTxt");
  const exportPdf       = document.getElementById("exportPdf");
  const toast           = document.getElementById("toast");

  // ── Input tabs ────────────────────────────────────────────────────────────

  var activeInputTab = "text";

  document.querySelectorAll("[data-tab]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var tab = this.dataset.tab;
      activeInputTab = tab;

      document.querySelectorAll("[data-tab]").forEach(function (b) {
        b.classList.remove("tab-btn--active");
        b.setAttribute("aria-selected", "false");
      });
      this.classList.add("tab-btn--active");
      this.setAttribute("aria-selected", "true");

      document.getElementById("tab-text").classList.toggle("tab-content--hidden", tab !== "text");
      document.getElementById("tab-file").classList.toggle("tab-content--hidden", tab !== "file");
    });
  });

  // ── Analytics tabs ────────────────────────────────────────────────────────

  document.querySelectorAll("[data-analytics-tab]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var tab = this.dataset.analyticsTab;

      document.querySelectorAll("[data-analytics-tab]").forEach(function (b) {
        b.classList.remove("tab-btn--active");
        b.setAttribute("aria-selected", "false");
      });
      this.classList.add("tab-btn--active");
      this.setAttribute("aria-selected", "true");

      document.querySelectorAll(".analytics-content").forEach(function (el) {
        el.classList.add("analytics-content--hidden");
      });
      var target = document.getElementById("analytics-" + tab);
      if (target) target.classList.remove("analytics-content--hidden");
    });
  });

  // ── Character counter ─────────────────────────────────────────────────────

  textInput.addEventListener("input", function () {
    var len = this.value.length;
    charCount.textContent = len.toLocaleString() + " / 50,000";

    if (len > 0 && len < 100) {
      charCount.style.color = "var(--warning)";
    } else if (len === 50000) {
      charCount.style.color = "var(--danger)";
    } else {
      charCount.style.color = "";
    }

    if (textError.textContent) {
      textError.textContent = "";
      textInput.classList.remove("field-error-state");
    }
  });

  // ── Ratio slider ──────────────────────────────────────────────────────────

  ratioSlider.addEventListener("input", function () {
    ratioValue.textContent = this.value + "%";
    ratioSlider.setAttribute("aria-valuenow", this.value);
  });

  // ── File upload ────────────────────────────────────────────────────────────

  ["dragenter", "dragover"].forEach(function (evt) {
    uploadZone.addEventListener(evt, function (e) {
      e.preventDefault();
      uploadZone.classList.add("drag-over");
    });
  });

  ["dragleave", "drop"].forEach(function (evt) {
    uploadZone.addEventListener(evt, function (e) {
      e.preventDefault();
      uploadZone.classList.remove("drag-over");
    });
  });

  uploadZone.addEventListener("drop", function (e) {
    var file = e.dataTransfer.files[0];
    if (file) handleFileUpload(file);
  });

  fileInput.addEventListener("change", function () {
    if (this.files[0]) handleFileUpload(this.files[0]);
  });

  function handleFileUpload(file) {
    var MAX_MB = 5;
    if (file.size > MAX_MB * 1024 * 1024) {
      showUploadStatus("File exceeds the " + MAX_MB + " MB limit.", "error");
      return;
    }

    var ext = file.name.split(".").pop().toLowerCase();
    if (ext !== "txt" && ext !== "pdf") {
      showUploadStatus("Only .txt and .pdf files are supported.", "error");
      return;
    }

    showUploadStatus("Uploading " + file.name + "…", "loading");

    var formData = new FormData();
    formData.append("file", file);

    fetch("/api/upload", { method: "POST", body: formData })
      .then(function (res) { return res.json(); })
      .then(function (data) {
        if (!data.success) {
          showUploadStatus(data.error || "Upload failed.", "error");
          return;
        }
        uploadedText = data.text;
        showUploadStatus(
          "✓ " + file.name + " loaded (" + data.char_count.toLocaleString() + " chars)",
          "success"
        );
      })
      .catch(function () {
        showUploadStatus("Network error during upload.", "error");
      });
  }

  function showUploadStatus(msg, type) {
    uploadStatus.textContent = msg;
    uploadStatus.style.color = type === "error"
      ? "var(--danger)"
      : type === "success"
        ? "var(--success)"
        : "var(--text-muted)";
  }

  // ── Summarize ─────────────────────────────────────────────────────────────

  summarizeBtn.addEventListener("click", function () {
    var text = activeInputTab === "file" ? uploadedText : textInput.value;
    var method = methodSelect.value;
    var ratio = parseFloat(ratioSlider.value) / 100;

    // Client-side validation
    if (!text || !text.trim()) {
      if (activeInputTab === "file") {
        showToast("Please upload a file first.", "warning");
      } else {
        setTextError("Please enter some text.");
      }
      return;
    }

    if (activeInputTab !== "file" && text.trim().length < 100) {
      setTextError("Text must be at least 100 characters.");
      return;
    }

    setLoading(true);
    clearResults();

    fetch("/api/summarize", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: text, method: method, ratio: ratio }),
    })
      .then(function (res) { return res.json(); })
      .then(function (data) {
        setLoading(false);
        if (!data.success) {
          showToast(data.error || "Summarization failed.", "error");
          return;
        }
        renderResults(data);
      })
      .catch(function () {
        setLoading(false);
        showToast("Network error. Is the server running?", "error");
      });
  });

  function setLoading(loading) {
    summarizeBtn.disabled = loading;
    btnText.hidden = loading;
    btnSpinner.hidden = !loading;
  }

  function setTextError(msg) {
    textError.textContent = msg;
    textInput.classList.add("field-error-state");
    textInput.focus();
  }

  function clearResults() {
    emptyState.hidden = false;
    results.hidden = true;
    lastSummary = "";
  }

  // ── Render results ────────────────────────────────────────────────────────

  function renderResults(data) {
    emptyState.hidden = true;
    results.hidden = false;
    lastSummary = data.summary;

    statOriginal.textContent = data.original_word_count.toLocaleString() + " words";
    statSummary.textContent  = data.summary_word_count.toLocaleString() + " words";
    statReduced.textContent  = data.compression_ratio;

    summaryText.textContent = data.summary;

    renderKeywords(data.analytics.top_words, data.analytics.keywords);
    renderFreqChart(data.analytics.top_words);
    renderScores(data.analytics.sentence_scores);

    // Reset analytics tabs to keywords
    document.querySelectorAll("[data-analytics-tab]").forEach(function (b) {
      var isKeywords = b.dataset.analyticsTab === "keywords";
      b.classList.toggle("tab-btn--active", isKeywords);
      b.setAttribute("aria-selected", isKeywords ? "true" : "false");
    });
    document.querySelectorAll(".analytics-content").forEach(function (el) {
      el.classList.add("analytics-content--hidden");
    });
    var kw = document.getElementById("analytics-keywords");
    if (kw) kw.classList.remove("analytics-content--hidden");
  }

  function renderKeywords(topWords, keywords) {
    keywordCloud.innerHTML = "";

    var items = keywords.length > 0
      ? keywords
      : topWords.slice(0, 10).map(function (w) { return w.word; });

    items.forEach(function (kw) {
      var tag = document.createElement("span");
      tag.className = "keyword-tag";
      tag.textContent = kw;
      keywordCloud.appendChild(tag);
    });
  }

  function renderScores(sentenceScores) {
    scoreList.innerHTML = "";
    var topTen = sentenceScores.slice(0, 20);

    topTen.forEach(function (item) {
      var el = document.createElement("div");
      el.className = "score-item score-item--" + item.label;

      var badge = document.createElement("span");
      badge.className = "score-badge score-badge--" + item.label;
      badge.textContent = item.score.toFixed(2);

      var sentence = document.createElement("span");
      sentence.className = "score-sentence";
      sentence.textContent = item.sentence.length > 120
        ? item.sentence.slice(0, 120) + "…"
        : item.sentence;

      el.appendChild(badge);
      el.appendChild(sentence);
      scoreList.appendChild(el);
    });
  }

  // ── Copy ──────────────────────────────────────────────────────────────────

  copyBtn.addEventListener("click", function () {
    if (!lastSummary) return;
    navigator.clipboard.writeText(lastSummary)
      .then(function () { showToast("Summary copied to clipboard."); })
      .catch(function () {
        var ta = document.createElement("textarea");
        ta.value = lastSummary;
        document.body.appendChild(ta);
        ta.select();
        document.execCommand("copy");
        document.body.removeChild(ta);
        showToast("Summary copied to clipboard.");
      });
  });

  // ── Export ────────────────────────────────────────────────────────────────

  exportTxt.addEventListener("click", function () { triggerExport("txt"); });
  exportPdf.addEventListener("click", function () { triggerExport("pdf"); });

  function triggerExport(fmt) {
    if (!lastSummary) {
      showToast("Nothing to export yet.", "warning");
      return;
    }

    fetch("/api/export", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ summary: lastSummary, format: fmt }),
    })
      .then(function (res) {
        if (!res.ok) return res.json().then(function (d) { throw new Error(d.error); });
        return res.blob();
      })
      .then(function (blob) {
        var url = URL.createObjectURL(blob);
        var a = document.createElement("a");
        a.href = url;
        a.download = "summary." + fmt;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        showToast("Download started.");
      })
      .catch(function (err) {
        showToast(err.message || "Export failed.", "error");
      });
  }

  // ── Toast ─────────────────────────────────────────────────────────────────

  var _toastTimer = null;

  function showToast(msg) {
    toast.textContent = msg;
    toast.classList.add("toast--visible");

    if (_toastTimer) clearTimeout(_toastTimer);
    _toastTimer = setTimeout(function () {
      toast.classList.remove("toast--visible");
    }, 3000);
  }

})();
