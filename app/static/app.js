/* ===== TEYZIX app — UI wiring ===== */
(function () {
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];

  /* ---------- LIGHTWEIGHT CLIENT UTILS (countWords, detectLanguage) ---------- */
  const _LANG = {
    English: ["the","and","of","to","in","is","that","for","with","as","are","this"],
    Spanish: ["el","la","de","que","y","los","las","en","un","una","por","con","para","es"],
    French: ["le","la","de","et","les","des","un","une","que","dans","pour","est","sur"],
    German: ["der","die","das","und","den","von","mit","ist","ein","eine","auf","für","nicht"],
    Portuguese: ["de","que","os","as","um","uma","com","para","não","por","mais","como","dos"],
    Italian: ["di","che","la","il","un","una","per","con","non","sono","come","più","gli"],
  };
  const _CODES = { English:"EN", Spanish:"ES", French:"FR", German:"DE", Portuguese:"PT", Italian:"IT" };

  const TEYZIX = {
    countWords: t => (t.match(/[\p{L}\d']+/gu) || []).length,
    detectLanguage(text) {
      const words = (text.toLowerCase().match(/[\p{L}]+/gu) || []).slice(0, 400);
      if (words.length < 8) return { name: "English", code: "EN", conf: 0 };
      let best = "English", bestScore = -1;
      for (const [lang, markers] of Object.entries(_LANG)) {
        const mset = new Set(markers);
        let hits = 0;
        for (const w of words) if (mset.has(w)) hits++;
        const score = hits / words.length;
        if (score > bestScore) { bestScore = score; best = lang; }
      }
      return { name: best, code: _CODES[best], conf: Math.min(99, Math.round(bestScore * 600)) };
    },
  };

  const SAMPLE = `Artificial intelligence has rapidly moved from research laboratories into the everyday tools that professionals rely on. Where summarization once required hours of careful reading, modern extractive systems can distill a dense report into its essential claims within seconds. This shift matters because the volume of text knowledge workers must process continues to grow far faster than the time available to read it.

Extractive summarization works by scoring each sentence in a document and selecting only the most informative ones. Frequency-based methods reward sentences that contain words appearing often across the text, on the assumption that repeated terms signal central themes. TF-IDF refines this idea by discounting words that are common everywhere and amplifying terms that are distinctive to a particular document. A combined approach blends both signals to balance breadth and specificity.

The practical benefits are clear for analysts, students, and researchers alike. A legal team can compress a two-hundred-page filing into a readable brief. A product manager can scan customer interviews without losing the critical objections buried in the middle. Crucially, because extractive methods quote the original text verbatim, they avoid the fabrication risks that sometimes accompany generative systems.

Yet summarization is not without limits. A short summary inevitably discards nuance, and a poorly chosen compression ratio can either bury the signal or strip away necessary context. The most effective tools therefore give users direct control over length, method, and the ability to inspect why each sentence was kept. Transparency turns a black box into a trustworthy assistant.

Looking ahead, the line between extracting and understanding will continue to blur. The goal is not merely shorter text, but faster comprehension. When a reader can grasp the core of a long document in a single glance and then drill into the evidence behind it, the technology has done its job. That is the promise of a well-designed summarization tool.`;

  const METHOD_DESC = {
    frequency: "Scores sentences by how often their key terms recur across the text. Fast, great for general documents.",
    tfidf: "Weights distinctive terms higher and common ones lower. Best for surfacing what makes a document unique.",
    combined: "Blends frequency and TF-IDF signals for a balanced summary. Recommended default.",
    abstractive: "Generates new summary text using a BERT-based model. Requires model download on first run. ✦",
  };

  const state = {
    method: "combined",
    ratio: 0.4,
    files: [],          // {name, size, text}
    activeTab: "paste",
    lastResult: null,
  };

  /* ---------- THEME ---------- */
  const THEME_KEY = "teyzix-theme";
  function applyTheme(t) {
    document.documentElement.setAttribute("data-theme", t);
    try { localStorage.setItem(THEME_KEY, t); } catch (e) {}
  }
  (function initTheme() {
    let t = "dark";
    try { t = localStorage.getItem(THEME_KEY) || "dark"; } catch (e) {}
    applyTheme(t);
  })();
  $("#themeToggle").addEventListener("click", () => {
    const cur = document.documentElement.getAttribute("data-theme");
    applyTheme(cur === "dark" ? "light" : "dark");
  });

  /* ---------- TOASTS ---------- */
  const ICONS = {
    success: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>',
    info: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><line x1="12" y1="11" x2="12" y2="16"/><circle cx="12" cy="8" r=".6" fill="currentColor" stroke="none"/></svg>',
    warn: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z"/><line x1="12" y1="9" x2="12" y2="13"/><circle cx="12" cy="17" r=".6" fill="currentColor" stroke="none"/></svg>',
  };
  function toast(title, sub, type = "success", ms = 3200) {
    const stack = $("#toastStack");
    const el = document.createElement("div");
    el.className = `toast ${type}`;
    el.innerHTML = `<div class="ti">${ICONS[type]}</div><div class="tbody"><div class="tt">${title}</div>${sub ? `<div class="ts">${sub}</div>` : ""}</div>`;
    stack.appendChild(el);
    setTimeout(() => {
      el.classList.add("out");
      el.addEventListener("animationend", () => el.remove());
    }, ms);
  }

  /* ---------- INPUT TABS ---------- */
  function moveIndicator(tablist) {
    const sel = tablist.querySelector('[aria-selected="true"]');
    const ind = tablist.querySelector(".tab-ind");
    if (!sel || !ind) return;
    ind.style.width = sel.offsetWidth + "px";
    ind.style.transform = `translateX(${sel.offsetLeft - 4}px)`;
  }
  const inputTabs = $("#inputTabs");
  $$(".tab", inputTabs).forEach(tab => {
    tab.addEventListener("click", () => {
      $$(".tab", inputTabs).forEach(t => t.setAttribute("aria-selected", "false"));
      tab.setAttribute("aria-selected", "true");
      moveIndicator(inputTabs);
      const target = tab.dataset.tab;
      state.activeTab = target;
      $$(".method-panel").forEach(p => p.classList.toggle("active", p.dataset.panel === target));
    });
  });

  /* ---------- LIVE STATS (paste) ---------- */
  const editor = $("#editor");
  function updateLive() {
    const t = editor.value;
    const w = TEYZIX.countWords(t);
    $("#liveChars").textContent = t.length.toLocaleString();
    $("#liveWords").textContent = w.toLocaleString();
    const lang = w >= 8 ? TEYZIX.detectLanguage(t) : null;
    $("#liveLang").textContent = lang ? lang.name : "—";
  }
  editor.addEventListener("input", updateLive);
  $("#loadSample").addEventListener("click", () => {
    editor.value = SAMPLE;
    updateLive();
    toast("Sample loaded", "A 5-paragraph article is ready to summarize.", "info");
  });
  $("#clearText").addEventListener("click", () => {
    editor.value = ""; updateLive();
  });

  /* ---------- FILE READING ---------- */
  function readFile(file) {
    return new Promise((resolve) => {
      const r = new FileReader();
      r.onload = () => resolve({ name: file.name, size: file.size, text: String(r.result || "") });
      r.onerror = () => resolve({ name: file.name, size: file.size, text: "" });
      r.readAsText(file);
    });
  }
  function fmtSize(b) {
    if (b < 1024) return b + " B";
    if (b < 1024 * 1024) return (b / 1024).toFixed(1) + " KB";
    return (b / 1024 / 1024).toFixed(1) + " MB";
  }
  function fileTypeOk(name) {
    return /\.(txt|md|csv|json|log|rtf|html?|xml|tex)$/i.test(name);
  }

  async function addFiles(list, multi) {
    const incoming = [...list].filter(f => {
      if (!fileTypeOk(f.name)) { toast("Unsupported file", `${f.name} — use a plain-text format.`, "warn"); return false; }
      return true;
    });
    if (!incoming.length) return;
    const read = await Promise.all(incoming.map(readFile));
    if (multi) {
      state.files.push(...read);
    } else {
      state.files = read.slice(0, 1);
    }
    renderFiles();
    const total = read.reduce((a, b) => a + TEYZIX.countWords(b.text), 0);
    toast(multi ? `${read.length} file${read.length > 1 ? "s" : ""} added` : "File ready",
      `${total.toLocaleString()} words loaded.`, "success");
  }

  function renderFiles() {
    const sList = $("#singleList");
    const mList = $("#multiList");
    sList.innerHTML = ""; mList.innerHTML = "";
    const single = state.activeTab === "file";
    state.files.forEach((f, i) => {
      const node = document.createElement("div");
      node.className = "fileitem";
      node.innerHTML = `
        <div class="ficon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg></div>
        <div class="finfo"><div class="fname">${f.name}</div><div class="fmeta">${fmtSize(f.size)} · ${TEYZIX.countWords(f.text).toLocaleString()} words</div></div>
        <button class="fremove" data-i="${i}" aria-label="Remove"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>`;
      (single ? sList : mList).appendChild(node);
    });
    $$(".fremove").forEach(b => b.addEventListener("click", () => {
      state.files.splice(+b.dataset.i, 1); renderFiles();
    }));
    $("#multiCount").textContent = state.files.length;
    $("#multiCount").style.display = (state.files.length && state.activeTab === "multi") ? "inline-flex" : "none";
  }

  function wireDrop(zoneId, inputId, multi) {
    const zone = $(zoneId), input = $(inputId);
    zone.addEventListener("click", () => input.click());
    input.addEventListener("change", () => { if (input.files.length) addFiles(input.files, multi); input.value = ""; });
    ["dragover", "dragenter"].forEach(ev => zone.addEventListener(ev, e => { e.preventDefault(); zone.classList.add("drag"); }));
    ["dragleave", "drop"].forEach(ev => zone.addEventListener(ev, e => { e.preventDefault(); zone.classList.remove("drag"); }));
    zone.addEventListener("drop", e => { if (e.dataTransfer.files.length) addFiles(e.dataTransfer.files, multi); });
  }
  wireDrop("#singleDrop", "#singleInput", false);
  wireDrop("#multiDrop", "#multiInput", true);

  /* ---------- METHOD + SLIDER ---------- */
  const methodSel = $("#methodSelect");
  methodSel.addEventListener("change", () => {
    state.method = methodSel.value;
    $("#methodDesc").textContent = METHOD_DESC[state.method] || "";
  });
  $("#methodDesc").textContent = METHOD_DESC[state.method] || "";

  const slider = $("#lengthSlider");
  function updateSlider() {
    const v = +slider.value;
    state.ratio = v / 100;
    const norm = (v - +slider.min) / (+slider.max - +slider.min);
    slider.style.setProperty("--norm", norm.toFixed(4));
    $("#sliderVal").textContent = v + "%";
  }
  slider.addEventListener("input", updateSlider);
  updateSlider();

  /* ---------- GATHER INPUT ---------- */
  function gatherDocs() {
    if (state.activeTab === "paste") {
      const t = editor.value.trim();
      return t ? [{ name: "Pasted text", text: t }] : [];
    }
    if (state.activeTab === "file") {
      return state.files.slice(0, 1).filter(f => f.text.trim());
    }
    return state.files.filter(f => f.text.trim());
  }

  /* ---------- GENERATE (fetch → /summarize) ---------- */
  const genBtn = $("#generateBtn");
  genBtn.addEventListener("click", async () => {
    const docs = gatherDocs();
    if (!docs.length) {
      toast("Nothing to summarize", "Paste text or upload a document first.", "warn");
      return;
    }
    const totalWords = docs.reduce((a, d) => a + TEYZIX.countWords(d.text), 0);
    if (totalWords < 40) {
      toast("Text too short", "Add at least a few sentences for a meaningful summary.", "warn");
      return;
    }

    genBtn.classList.add("loading");
    genBtn.disabled = true;

    try {
      const res = await fetch("/summarize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ docs, method: state.method, ratio: state.ratio }),
      });
      const result = await res.json();
      if (result.error) {
        toast("Could not summarize", result.error || "No complete sentences detected.", "warn");
      } else {
        state.lastResult = result;
        renderResult(result, docs.length);
        toast("Summary ready", `${result.stats.compression}% shorter · ${result.stats.sumSentences} sentences kept.`, "success");
      }
    } catch (e) {
      toast("Network error", "Could not reach the server.", "warn");
    } finally {
      genBtn.classList.remove("loading");
      genBtn.disabled = false;
    }
  });

  /* ---------- RENDER RESULT ---------- */
  function renderResult(r, docCount) {
    $("#emptyState").style.display = "none";
    const res = $("#result");
    res.classList.add("show");

    // language badge
    $("#langBadge").innerHTML = `<span class="bdot"></span>${r.language.name} · ${r.language.code}`;
    $("#summaryHead").style.display = "flex";

    // stats
    $("#statOrig").textContent = r.stats.origWords.toLocaleString();
    $("#statSum").textContent = r.stats.sumWords.toLocaleString();
    $("#statComp").textContent = r.stats.compression + "%";
    $("#statSentMeta").textContent = `${r.stats.origSentences} → ${r.stats.sumSentences} sentences`;
    $("#statReadMeta").textContent = `~${r.stats.readingTime} min read`;

    // summary with keyword highlight
    const kw = r.keywordWords.slice(0, 8);
    let html = r.summaryText;
    if (kw.length) {
      const re = new RegExp("\\b(" + kw.map(escapeRe).join("|") + ")\\b", "gi");
      html = html.replace(re, "<mark>$1</mark>");
    }
    $("#summaryText").innerHTML = html;

    // keyword cloud
    const cloud = $("#cloud");
    cloud.innerHTML = "";
    r.keywords.forEach(k => {
      const el = document.createElement("span");
      el.className = "kw";
      el.innerHTML = `${k.word}<span class="kct">${k.count}</span>`;
      cloud.appendChild(el);
    });

    // bar chart
    const chart = $("#chart");
    chart.innerHTML = "";
    const maxC = Math.max(...r.chart.map(c => c.count), 1);
    r.chart.forEach((c) => {
      const row = document.createElement("div");
      row.className = "bar-row";
      const pct = (c.count / maxC * 100);
      row.innerHTML = `<div class="bar-label">${c.word}</div><div class="bar-track"><div class="bar-fill" style="width:${pct}%"></div></div><div class="bar-val">${c.count}</div>`;
      chart.appendChild(row);
    });

    // sentence scores
    const sl = $("#sentList");
    sl.innerHTML = "";
    r.sentenceScores.forEach(s => {
      const item = document.createElement("div");
      item.className = `sentitem ${s.label}`;
      item.innerHTML = `
        <div class="sent-rank">#${s.rank}</div>
        <div class="sent-text">${s.text}</div>
        <div class="sent-meta">
          <span class="score-tag ${s.label}">${s.label}</span>
          <span class="score-num">${s.score}</span>
        </div>`;
      sl.appendChild(item);
    });

    $("#anaEmpty").style.display = "none";
    $("#anaContent").style.display = "block";
    moveIndicator($("#anaTabs"));

    if (window.innerWidth < 940) {
      window.scrollTo({ top: res.getBoundingClientRect().top + window.scrollY - 80, behavior: "smooth" });
    }
  }

  function escapeRe(s) { return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"); }

  /* ---------- ANALYTICS TABS ---------- */
  const anaTabs = $("#anaTabs");
  $$(".tab", anaTabs).forEach(tab => {
    tab.addEventListener("click", () => {
      $$(".tab", anaTabs).forEach(t => t.setAttribute("aria-selected", "false"));
      tab.setAttribute("aria-selected", "true");
      moveIndicator(anaTabs);
      const v = tab.dataset.view;
      $$(".ana-view").forEach(p => p.classList.toggle("active", p.dataset.view === v));
    });
  });

  /* ---------- COPY + EXPORT ---------- */
  $("#copyBtn").addEventListener("click", async () => {
    if (!state.lastResult) return;
    try {
      await navigator.clipboard.writeText(state.lastResult.summaryText);
      toast("Copied to clipboard", "Summary text is ready to paste.", "success");
    } catch (e) {
      const ta = document.createElement("textarea");
      ta.value = state.lastResult.summaryText; document.body.appendChild(ta); ta.select();
      try { document.execCommand("copy"); toast("Copied to clipboard", "", "success"); } catch (_) { toast("Copy failed", "Select the text manually.", "warn"); }
      ta.remove();
    }
  });

  function downloadBlob(content, filename, type) {
    const blob = new Blob([content], { type });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = filename; document.body.appendChild(a); a.click();
    a.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  $("#exportTxt").addEventListener("click", () => {
    if (!state.lastResult) return;
    const r = state.lastResult;
    const out = [
      "TEYZIX — Document Summary",
      "=========================",
      `Language: ${r.language.name} (${r.language.code})`,
      `Method: ${state.method}   ·   Length: ${Math.round(state.ratio * 100)}%`,
      `Original: ${r.stats.origWords} words   ·   Summary: ${r.stats.sumWords} words   ·   Compression: ${r.stats.compression}%`,
      "",
      "SUMMARY",
      "-------",
      r.summaryText,
      "",
      "KEYWORDS",
      "--------",
      r.keywordWords.join(", "),
    ].join("\n");
    downloadBlob(out, "teyzix-summary.txt", "text/plain");
    toast("Exported .txt", "Download started.", "success");
  });

  $("#exportPdf").addEventListener("click", () => {
    if (!state.lastResult) return;
    const r = state.lastResult;
    const win = window.open("", "_blank");
    if (!win) { toast("Pop-up blocked", "Allow pop-ups to export PDF.", "warn"); return; }
    const kwHtml = r.keywords.map(k => `<span class="k">${k.word}</span>`).join(" ");
    win.document.write(`<!doctype html><html><head><meta charset="utf-8"><title>TEYZIX Summary</title>
      <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
        body{font-family:Inter,sans-serif;color:#1a1a26;max-width:720px;margin:48px auto;padding:0 32px;line-height:1.65}
        h1{font-size:24px;letter-spacing:.12em;color:#0284c7;margin:0 0 4px}
        .tag{color:#71748a;font-size:13px;margin-bottom:26px}
        .meta{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:28px}
        .chip{font-size:12px;background:#e0f2fe;color:#0369a1;padding:6px 12px;border-radius:999px;font-weight:600}
        h2{font-size:13px;text-transform:uppercase;letter-spacing:.08em;color:#71748a;margin:32px 0 10px;border-bottom:1px solid #eee;padding-bottom:8px}
        p{font-size:15px}
        .k{display:inline-block;background:#e0f2fe;color:#0369a1;padding:5px 12px;border-radius:999px;font-size:13px;font-weight:600;margin:0 4px 6px 0}
        @media print{body{margin:0}}
      </style></head><body>
      <h1>TEYZIX</h1><div class="tag">Document Summary</div>
      <div class="meta"><span class="chip">${r.language.name}</span><span class="chip">${state.method}</span><span class="chip">${r.stats.compression}% shorter</span><span class="chip">${r.stats.sumWords} words</span></div>
      <h2>Summary</h2><p>${r.summaryText}</p>
      <h2>Keywords</h2><div>${kwHtml}</div>
      <script>window.onload=()=>setTimeout(()=>window.print(),400)<\/script>
      </body></html>`);
    win.document.close();
    toast("Preparing PDF", "Use your browser's Save as PDF.", "info");
  });

  /* ---------- INIT ---------- */
  window.addEventListener("load", () => {
    moveIndicator(inputTabs);
    updateLive();
    updateSlider();
  });
  window.addEventListener("resize", () => {
    moveIndicator(inputTabs);
    if ($("#anaContent").style.display !== "none") moveIndicator(anaTabs);
    updateSlider();
  });
})();
