/**
 * Main application logic.
 *
 * Responsibilities:
 *   - Tab switching (input method, analytics)
 *   - Live character counter with colour feedback
 *   - Single file drag-and-drop upload → /api/upload
 *   - Multi-file upload → /api/upload-multiple
 *   - Summarize form → /api/summarize
 *   - Batch summarize → /api/summarize-batch
 *   - Render results (stats, language badge, summary text, keywords, chart, scores)
 *   - Individual batch results with per-doc tabs
 *   - Export buttons → /api/export
 *   - Copy to clipboard
 *   - Toast notifications
 */

(function () {
  "use strict";

  // ── State ────────────────────────────────────────────────────────────────

  var uploadedText    = "";
  var lastSummary     = "";
  var multiDocFiles   = [];   // [{name, text, charCount}]
  var multiDocMode    = "combined";
  var batchResults    = [];   // individual mode: array of result objects
  var activeBatchDoc  = 0;

  // ── DOM refs ─────────────────────────────────────────────────────────────

  var textInput       = document.getElementById("textInput");
  var charCount       = document.getElementById("charCount");
  var textError       = document.getElementById("textError");
  var fileInput       = document.getElementById("fileInput");
  var uploadZone      = document.getElementById("uploadZone");
  var uploadStatus    = document.getElementById("uploadStatus");
  var multiFileInput  = document.getElementById("multiFileInput");
  var multiUploadZone = document.getElementById("multiUploadZone");
  var multiUploadStatus = document.getElementById("multiUploadStatus");
  var multiFileList   = document.getElementById("multiFileList");
  var methodSelect    = document.getElementById("methodSelect");
  var ratioSlider     = document.getElementById("ratioSlider");
  var ratioValue      = document.getElementById("ratioValue");
  var summarizeBtn    = document.getElementById("summarizeBtn");
  var btnText         = summarizeBtn.querySelector(".btn-text");
  var btnSpinner      = summarizeBtn.querySelector(".btn-spinner");

  var emptyState      = document.getElementById("emptyState");
  var results         = document.getElementById("results");
  var statOriginal    = document.getElementById("statOriginal");
  var statSummary     = document.getElementById("statSummary");
  var statReduced     = document.getElementById("statReduced");
  var statLangChip    = document.getElementById("statLangChip");
  var statLang        = document.getElementById("statLang");
  var docTabsRow         = document.getElementById("docTabsRow");
  var summaryTypeBadge   = document.getElementById("summaryTypeBadge");
  var summaryText        = document.getElementById("summaryText");
  var copyBtn         = document.getElementById("copyBtn");
  var keywordCloud    = document.getElementById("keywordCloud");
  var scoreList       = document.getElementById("scoreList");
  var exportTxt       = document.getElementById("exportTxt");
  var exportPdf       = document.getElementById("exportPdf");
  var toast           = document.getElementById("toast");

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
      document.getElementById("tab-multidoc").classList.toggle("tab-content--hidden", tab !== "multidoc");
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

  // ── Single file upload ────────────────────────────────────────────────────

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
      showUploadStatus(uploadStatus, "File exceeds the " + MAX_MB + " MB limit.", "error");
      return;
    }
    var ext = file.name.split(".").pop().toLowerCase();
    if (ext !== "txt" && ext !== "pdf") {
      showUploadStatus(uploadStatus, "Only .txt and .pdf files are supported.", "error");
      return;
    }

    showUploadStatus(uploadStatus, "Uploading " + file.name + "…", "loading");

    var formData = new FormData();
    formData.append("file", file);

    fetch("/api/upload", { method: "POST", body: formData })
      .then(function (res) { return res.json(); })
      .then(function (data) {
        if (!data.success) {
          showUploadStatus(uploadStatus, data.error || "Upload failed.", "error");
          return;
        }
        uploadedText = data.text;
        showUploadStatus(
          uploadStatus,
          "✓ " + file.name + " loaded (" + data.char_count.toLocaleString() + " chars)",
          "success"
        );
      })
      .catch(function () {
        showUploadStatus(uploadStatus, "Network error during upload.", "error");
      });
  }

  function showUploadStatus(el, msg, type) {
    el.textContent = msg;
    el.style.color = type === "error"
      ? "var(--danger)"
      : type === "success"
        ? "var(--success)"
        : "var(--text-muted)";
  }

  // ── Multi-file upload ─────────────────────────────────────────────────────

  ["dragenter", "dragover"].forEach(function (evt) {
    multiUploadZone.addEventListener(evt, function (e) {
      e.preventDefault();
      multiUploadZone.classList.add("drag-over");
    });
  });

  ["dragleave", "drop"].forEach(function (evt) {
    multiUploadZone.addEventListener(evt, function (e) {
      e.preventDefault();
      multiUploadZone.classList.remove("drag-over");
    });
  });

  multiUploadZone.addEventListener("drop", function (e) {
    if (e.dataTransfer.files.length) handleMultiUpload(e.dataTransfer.files);
  });

  multiFileInput.addEventListener("change", function () {
    if (this.files.length) handleMultiUpload(this.files);
    this.value = "";
  });

  function handleMultiUpload(fileList) {
    var MAX_FILES = 10;
    var MAX_MB    = 5;
    var files     = Array.from(fileList);

    if (multiDocFiles.length + files.length > MAX_FILES) {
      showToast("Maximum 10 files allowed.", "warning");
      return;
    }

    var valid = [];
    for (var i = 0; i < files.length; i++) {
      var f = files[i];
      var ext = f.name.split(".").pop().toLowerCase();
      if (ext !== "txt" && ext !== "pdf") {
        showToast(f.name + " — only .txt and .pdf supported.", "error");
        continue;
      }
      if (f.size > MAX_MB * 1024 * 1024) {
        showToast(f.name + " exceeds 5 MB limit.", "error");
        continue;
      }
      valid.push(f);
    }

    if (valid.length === 0) return;

    showUploadStatus(multiUploadStatus, "Uploading " + valid.length + " file(s)…", "loading");

    var formData = new FormData();
    valid.forEach(function (f) { formData.append("files", f); });

    fetch("/api/upload-multiple", { method: "POST", body: formData })
      .then(function (res) { return res.json(); })
      .then(function (data) {
        if (!data.success) {
          showUploadStatus(multiUploadStatus, data.error || "Upload failed.", "error");
          return;
        }
        for (var j = 0; j < data.texts.length; j++) {
          multiDocFiles.push({
            name: data.names[j],
            text: data.texts[j],
            charCount: data.char_counts[j],
          });
        }
        renderFileList();
        showUploadStatus(
          multiUploadStatus,
          "✓ " + data.texts.length + " file(s) loaded." +
            (data.errors.length ? " " + data.errors.length + " skipped." : ""),
          "success"
        );
      })
      .catch(function () {
        showUploadStatus(multiUploadStatus, "Network error during upload.", "error");
      });
  }

  function renderFileList() {
    multiFileList.innerHTML = "";
    multiDocFiles.forEach(function (doc, idx) {
      var item = document.createElement("div");
      item.className = "file-list-item";

      var info = document.createElement("span");
      info.className = "file-list-name";
      info.textContent = doc.name + " (" + doc.charCount.toLocaleString() + " chars)";

      var remove = document.createElement("button");
      remove.className = "file-list-remove";
      remove.type = "button";
      remove.textContent = "×";
      remove.setAttribute("aria-label", "Remove " + doc.name);
      remove.addEventListener("click", function () {
        multiDocFiles.splice(idx, 1);
        renderFileList();
        if (multiDocFiles.length === 0) {
          showUploadStatus(multiUploadStatus, "", "loading");
        }
      });

      item.appendChild(info);
      item.appendChild(remove);
      multiFileList.appendChild(item);
    });
  }

  // ── Mode toggle (multi-doc) ───────────────────────────────────────────────

  document.querySelectorAll("[data-mode]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      multiDocMode = this.dataset.mode;
      document.querySelectorAll("[data-mode]").forEach(function (b) {
        b.classList.toggle("mode-btn--active", b.dataset.mode === multiDocMode);
      });
    });
  });

  // ── Summarize dispatch ────────────────────────────────────────────────────

  summarizeBtn.addEventListener("click", function () {
    if (activeInputTab === "multidoc") {
      runBatchSummarize();
    } else {
      runSingleSummarize();
    }
  });

  function runSingleSummarize() {
    var text   = activeInputTab === "file" ? uploadedText : textInput.value;
    var method = methodSelect.value;
    var ratio  = parseFloat(ratioSlider.value) / 100;

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
  }

  function runBatchSummarize() {
    if (multiDocFiles.length === 0) {
      showToast("Upload at least one file first.", "warning");
      return;
    }
    if (multiDocFiles.length === 1 && multiDocMode === "individual") {
      showToast("Use single-document mode for one file.", "warning");
      return;
    }

    setLoading(true);
    clearResults();

    fetch("/api/summarize-batch", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        documents: multiDocFiles.map(function (f) { return f.text; }),
        names: multiDocFiles.map(function (f) { return f.name; }),
        method: methodSelect.value,
        ratio: parseFloat(ratioSlider.value) / 100,
        mode: multiDocMode,
      }),
    })
      .then(function (res) { return res.json(); })
      .then(function (data) {
        setLoading(false);
        if (!data.success) {
          showToast(data.error || "Batch summarization failed.", "error");
          return;
        }
        renderBatchResults(data);
      })
      .catch(function () {
        setLoading(false);
        showToast("Network error. Is the server running?", "error");
      });
  }

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
    batchResults = [];
    docTabsRow.hidden = true;
    docTabsRow.innerHTML = "";
    statLangChip.hidden = true;
    summaryTypeBadge.hidden = true;
  }

  // ── Render single result ──────────────────────────────────────────────────

  function renderResults(data) {
    emptyState.hidden = true;
    results.hidden = false;
    lastSummary = data.summary;

    statOriginal.textContent = data.original_word_count.toLocaleString() + " words";
    statSummary.textContent  = data.summary_word_count.toLocaleString() + " words";
    statReduced.textContent  = data.compression_ratio;

    if (data.detected_language_name) {
      statLang.textContent = data.detected_language_name;
      statLangChip.hidden  = false;
    }

    docTabsRow.hidden    = true;
    docTabsRow.innerHTML = "";

    summaryTypeBadge.hidden = data.summary_type !== "abstractive";

    summaryText.textContent = data.summary;

    renderKeywords(data.analytics.top_words, data.analytics.keywords);
    renderFreqChart(data.analytics.top_words);
    renderScores(data.analytics.sentence_scores);
    resetAnalyticsTabs();
  }

  // ── Render batch results ──────────────────────────────────────────────────

  function renderBatchResults(data) {
    if (data.mode === "combined") {
      renderResults(data);
      statOriginal.textContent = data.original_word_count.toLocaleString() + " words";
      var countNote = document.createElement("span");
      countNote.style.fontSize = "0.72rem";
      countNote.style.color    = "var(--text-muted)";
      countNote.style.display  = "block";
      countNote.textContent    = data.document_count + " docs merged";
      statOriginal.appendChild(countNote);
      return;
    }

    // Individual mode
    batchResults    = data.results;
    activeBatchDoc  = 0;

    var successful = batchResults.filter(function (r) { return r.success; });
    if (successful.length === 0) {
      showToast("All documents failed to summarize.", "error");
      return;
    }

    emptyState.hidden = true;
    results.hidden    = false;

    buildDocTabs();
    showBatchDoc(0);
  }

  function buildDocTabs() {
    docTabsRow.innerHTML = "";
    docTabsRow.hidden    = false;

    batchResults.forEach(function (r, idx) {
      var btn = document.createElement("button");
      btn.className  = "doc-tab-btn" + (idx === 0 ? " doc-tab-btn--active" : "");
      btn.type       = "button";
      btn.textContent = r.doc_name
        ? truncate(r.doc_name, 18)
        : "Doc " + (idx + 1);
      if (!r.success) btn.classList.add("doc-tab-btn--error");

      btn.addEventListener("click", function () {
        activeBatchDoc = idx;
        document.querySelectorAll(".doc-tab-btn").forEach(function (b) {
          b.classList.remove("doc-tab-btn--active");
        });
        btn.classList.add("doc-tab-btn--active");
        showBatchDoc(idx);
      });

      docTabsRow.appendChild(btn);
    });
  }

  function showBatchDoc(idx) {
    var doc = batchResults[idx];
    if (!doc) return;

    if (!doc.success) {
      summaryText.textContent = "⚠ " + (doc.error || "This document could not be summarized.");
      statOriginal.textContent = "—";
      statSummary.textContent  = "—";
      statReduced.textContent  = "—";
      statLangChip.hidden      = true;
      lastSummary              = "";
      return;
    }

    lastSummary = doc.summary;

    statOriginal.textContent = doc.original_word_count.toLocaleString() + " words";
    statSummary.textContent  = doc.summary_word_count.toLocaleString() + " words";
    statReduced.textContent  = doc.compression_ratio;

    if (doc.detected_language_name) {
      statLang.textContent = doc.detected_language_name;
      statLangChip.hidden  = false;
    }

    summaryText.textContent = doc.summary;
    renderKeywords(doc.analytics.top_words, doc.analytics.keywords);
    renderFreqChart(doc.analytics.top_words);
    renderScores(doc.analytics.sentence_scores);
    resetAnalyticsTabs();
  }

  // ── Analytics helpers ─────────────────────────────────────────────────────

  function renderKeywords(topWords, keywords) {
    keywordCloud.innerHTML = "";

    var items = keywords.length > 0
      ? keywords
      : topWords.slice(0, 10).map(function (w) { return w.word; });

    items.forEach(function (kw) {
      var tag = document.createElement("span");
      tag.className   = "keyword-tag";
      tag.textContent = kw;
      keywordCloud.appendChild(tag);
    });
  }

  function renderScores(sentenceScores) {
    scoreList.innerHTML = "";

    sentenceScores.slice(0, 20).forEach(function (item) {
      var el = document.createElement("div");
      el.className = "score-item score-item--" + item.label;

      var badge = document.createElement("span");
      badge.className   = "score-badge score-badge--" + item.label;
      badge.textContent = item.score.toFixed(2);

      var sentence = document.createElement("span");
      sentence.className   = "score-sentence";
      sentence.textContent = item.sentence.length > 120
        ? item.sentence.slice(0, 120) + "…"
        : item.sentence;

      el.appendChild(badge);
      el.appendChild(sentence);
      scoreList.appendChild(el);
    });
  }

  function resetAnalyticsTabs() {
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
        var a   = document.createElement("a");
        a.href     = url;
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

  // ── Utility ───────────────────────────────────────────────────────────────

  function truncate(str, max) {
    return str.length > max ? str.slice(0, max - 1) + "…" : str;
  }

})();
