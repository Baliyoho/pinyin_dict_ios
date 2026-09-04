/* 拼音字典 — 輸入漢字，查出對應的拼音輸入。整份資料離線存在裝置上。 */
(() => {
  "use strict";

  const CACHE_PREFIX = "pinyin-dict-";
  const HISTORY_KEY = "pinyin-dict.history";
  const HISTORY_MAX = 12;
  const INPUT_MAX = 200;

  const HAN = /\p{Script=Han}/u;

  // index 0 是無聲調（輕聲）的寫法，1–4 依序是四聲。
  const TONE_TABLE = {
    a: "aāáǎà", o: "oōóǒò", e: "eēéěè",
    i: "iīíǐì", u: "uūúǔù", "ü": "üǖǘǚǜ",
    n: "nnńňǹ", m: "mmḿm̌m̀",
  };

  const chars = new Map();   // 字 -> ["zhong1", "zhong4"]
  const words = new Map();   // 詞 -> ["yin2 hang2"]
  let maxWordLength = 8;

  const el = {
    form: document.getElementById("search-form"),
    query: document.getElementById("query"),
    clear: document.getElementById("clear"),
    status: document.getElementById("status"),
    results: document.getElementById("results"),
    empty: document.getElementById("empty"),
    tones: document.getElementById("out-tones"),
    keys: document.getElementById("out-keys"),
    note: document.getElementById("out-note"),
    cards: document.getElementById("cards"),
    historyBox: document.getElementById("history-box"),
    history: document.getElementById("history"),
    clearHistory: document.getElementById("clear-history"),
    toast: document.getElementById("toast"),
  };

  /* ---------------- 拼音表示法 ---------------- */

  // "zhong1" -> "zhōng"，"lv4" -> "lǜ"，"de5" -> "de"
  function toneMarked(numbered) {
    const tone = Number(numbered.slice(-1));
    const base = numbered.slice(0, -1).replace(/v/g, "ü");
    if (!tone || tone === 5) return base;

    let idx = base.indexOf("a");
    if (idx < 0) idx = base.indexOf("o");
    if (idx < 0) idx = base.indexOf("e");
    if (idx < 0) {
      for (let i = base.length - 1; i >= 0; i--) {
        if ("iuü".includes(base[i])) { idx = i; break; }
      }
    }
    if (idx < 0) idx = base.length - 1;

    const row = TONE_TABLE[base[idx]];
    if (!row) return base;
    return base.slice(0, idx) + row[tone] + base.slice(idx + 1);
  }

  // 鍵盤上實際要打的字母：去掉聲調，ü 打成 v。
  const keystrokes = (numbered) => numbered.slice(0, -1);

  const toneNumber = (numbered) => Number(numbered.slice(-1)) || 5;

  // 字典裡以 "~" 開頭的是罕見／異讀，平常不該拿來當預設讀音。
  function readingsFor(ch) {
    const raw = chars.get(ch);
    if (!raw) return [];
    return raw.map((r) =>
      r.startsWith("~") ? { py: r.slice(1), rare: true } : { py: r, rare: false }
    );
  }

  const primaryOf = (list) => (list.find((r) => !r.rare) || list[0] || null);

  // 只有常用讀音才算數；輕聲（頭 tou2/tou5）視為同一個音的變體。
  function isPolyphonic(list) {
    const common = list.filter((r) => !r.rare);
    const distinct = new Set();
    for (const reading of common) {
      const base = reading.py.slice(0, -1);
      const neutral = reading.py.slice(-1) === "5";
      if (neutral && common.some((o) => o !== reading && o.py.slice(0, -1) === base)) continue;
      distinct.add(reading.py);
    }
    return distinct.size > 1;
  }

  /* ---------------- 資料 ---------------- */

  function parseInto(map, text) {
    let start = 0;
    while (start < text.length) {
      let end = text.indexOf("\n", start);
      if (end < 0) end = text.length;
      const tab = text.indexOf("\t", start);
      if (tab > start && tab < end) {
        map.set(text.slice(start, tab), text.slice(tab + 1, end).split("|"));
      }
      start = end + 1;
    }
  }

  async function loadData() {
    const [meta, charText, wordText] = await Promise.all([
      fetch("./data/meta.json").then((r) => r.json()),
      fetch("./data/chars.txt").then((r) => r.text()),
      fetch("./data/words.txt").then((r) => r.text()),
    ]);
    parseInto(chars, charText);
    parseInto(words, wordText);
    maxWordLength = meta.maxWordLength || maxWordLength;
  }

  /* ---------------- 斷詞 ---------------- */

  // 以最長詞優先切分，讓多音字依詞組決定讀音（銀行 háng、不是 xíng）。
  function segment(text) {
    const cps = Array.from(text);
    const tokens = [];
    let i = 0;

    while (i < cps.length) {
      if (!HAN.test(cps[i])) {
        let j = i;
        while (j < cps.length && !HAN.test(cps[j])) j++;
        tokens.push({ type: "other", text: cps.slice(i, j).join("") });
        i = j;
        continue;
      }

      let matched = null;
      const window = Math.min(maxWordLength, cps.length - i);
      for (let len = window; len >= 2; len--) {
        const candidate = cps.slice(i, i + len).join("");
        const readings = words.get(candidate);
        if (readings) {
          matched = { type: "word", text: candidate, syllables: readings[0].split(" ") };
          break;
        }
      }

      if (matched) {
        tokens.push(matched);
        i += Array.from(matched.text).length;
      } else {
        const ch = cps[i];
        const best = primaryOf(readingsFor(ch));
        tokens.push({ type: "word", text: ch, syllables: [best ? best.py : null] });
        i += 1;
      }
    }
    return tokens;
  }

  // 攤平成逐字資料，附上該字的其他可能讀音。
  function analyse(text) {
    const tokens = segment(text.slice(0, INPUT_MAX));
    const items = [];

    for (const token of tokens) {
      if (token.type === "other") {
        items.push({ kind: "other", text: token.text });
        continue;
      }
      const cps = Array.from(token.text);
      const cells = cps.map((ch, n) => {
        const chosen = token.syllables[n] || null;
        const all = readingsFor(ch);
        if (chosen && !all.some((r) => r.py === chosen)) all.unshift({ py: chosen, rare: false });
        return { char: ch, chosen, all, multi: isPolyphonic(all) };
      });
      items.push({ kind: "word", text: token.text, cells, isWord: cps.length > 1 });
    }
    return items;
  }

  /* ---------------- 畫面 ---------------- */

  function render(text) {
    const items = analyse(text);
    el.cards.textContent = "";
    el.tones.textContent = "";
    el.keys.textContent = "";

    let usesV = false;
    let unknown = 0;
    let multi = 0;

    for (const item of items) {
      if (item.kind === "other") {
        const plain = item.text.trim();
        if (plain) {
          for (const target of [el.tones, el.keys]) {
            const span = document.createElement("span");
            span.className = "w plain";
            span.textContent = plain;
            target.appendChild(span);
          }
        }
        continue;
      }

      const toneSpan = document.createElement("span");
      const keySpan = document.createElement("span");
      toneSpan.className = keySpan.className = "w";

      for (const cell of item.cells) {
        if (!cell.chosen) {
          unknown++;
          toneSpan.textContent += cell.char;
          keySpan.textContent += "?";
          el.cards.appendChild(cardFor(cell, item));
          continue;
        }
        if (cell.chosen.includes("v")) usesV = true;
        if (cell.multi) multi++;
        toneSpan.textContent += toneMarked(cell.chosen);
        keySpan.textContent += keystrokes(cell.chosen);
        el.cards.appendChild(cardFor(cell, item));
      }

      el.tones.appendChild(toneSpan);
      el.keys.appendChild(keySpan);
    }

    const notes = [];
    if (usesV) notes.push("ü 在拼音鍵盤上要打 v（綠 lǜ → 打 lv）。");
    if (multi) notes.push(`有 ${multi} 個多音字，讀音已依詞組判斷，點字卡可看其他讀音。`);
    if (unknown) notes.push(`有 ${unknown} 個字查不到讀音。`);
    el.note.textContent = notes.join(" ");
    el.note.hidden = notes.length === 0;

    el.results.hidden = false;
    el.empty.hidden = true;
  }

  function cardFor(cell, item) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "hz" + (cell.multi ? " multi" : "");
    button.setAttribute("aria-expanded", "false");

    const glyph = document.createElement("span");
    glyph.className = "glyph";
    glyph.textContent = cell.char;

    const py = document.createElement("span");
    py.className = "py";
    py.textContent = cell.chosen ? toneMarked(cell.chosen) : "—";

    const key = document.createElement("span");
    key.className = "key";
    key.textContent = cell.chosen ? keystrokes(cell.chosen) : "";

    const tone = document.createElement("span");
    tone.className = "tone";
    tone.textContent = cell.chosen ? (toneNumber(cell.chosen) === 5 ? "輕" : String(toneNumber(cell.chosen))) : "";

    button.append(glyph, py, key, tone);
    button.addEventListener("click", () => toggleAlts(button, cell, item));
    return button;
  }

  function toggleAlts(button, cell, item) {
    const open = button.getAttribute("aria-expanded") === "true";
    el.cards.querySelectorAll(".alts").forEach((n) => n.remove());
    el.cards.querySelectorAll('.hz[aria-expanded="true"]').forEach((n) =>
      n.setAttribute("aria-expanded", "false")
    );
    if (open) return;

    button.setAttribute("aria-expanded", "true");
    const panel = document.createElement("div");
    panel.className = "alts";

    const title = document.createElement("h3");
    title.textContent = item.isWord
      ? `「${item.text}」的${cell.char}讀 ${cell.chosen ? toneMarked(cell.chosen) : "—"}`
      : `「${cell.char}」的讀音`;

    const list = document.createElement("ul");
    const ordered = [...cell.all].sort((a, b) => Number(a.rare) - Number(b.rare));
    for (const reading of ordered) {
      const li = document.createElement("li");
      li.className = [reading.py === cell.chosen ? "on" : "", reading.rare ? "rare" : ""]
        .filter(Boolean)
        .join(" ");
      li.textContent = toneMarked(reading.py);
      const code = document.createElement("code");
      code.textContent = keystrokes(reading.py) + (reading.rare ? " 罕用" : "");
      li.appendChild(code);
      list.appendChild(li);
    }
    if (!cell.all.length) {
      const li = document.createElement("li");
      li.textContent = "查無資料";
      list.appendChild(li);
    }

    panel.append(title, list);
    button.after(panel);
  }

  function showEmpty() {
    el.results.hidden = true;
    el.empty.hidden = false;
    el.cards.textContent = "";
  }

  /* ---------------- 最近查詢 ---------------- */

  const readHistory = () => {
    try {
      const raw = JSON.parse(localStorage.getItem(HISTORY_KEY) || "[]");
      return Array.isArray(raw) ? raw.filter((s) => typeof s === "string") : [];
    } catch { return []; }
  };

  function saveHistory(list) {
    try { localStorage.setItem(HISTORY_KEY, JSON.stringify(list)); } catch { /* 私密瀏覽模式 */ }
  }

  function rememberQuery(text) {
    const trimmed = text.trim();
    if (!trimmed || !HAN.test(trimmed)) return;
    const list = [trimmed, ...readHistory().filter((s) => s !== trimmed)].slice(0, HISTORY_MAX);
    saveHistory(list);
    renderHistory();
  }

  function renderHistory() {
    const list = readHistory();
    el.history.textContent = "";
    el.historyBox.hidden = list.length === 0;
    for (const text of list) {
      const chip = document.createElement("button");
      chip.type = "button";
      chip.className = "chip";
      chip.textContent = text;
      chip.addEventListener("click", () => search(text, { remember: false }));
      el.history.appendChild(chip);
    }
  }

  /* ---------------- 互動 ---------------- */

  let toastTimer;
  function toast(message) {
    el.toast.textContent = message;
    el.toast.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => el.toast.classList.remove("show"), 1800);
  }

  async function copy(text) {
    if (!text) return;
    try {
      await navigator.clipboard.writeText(text);
      toast("已複製");
    } catch {
      const scratch = document.createElement("textarea");
      scratch.value = text;
      scratch.setAttribute("readonly", "");
      scratch.style.cssText = "position:fixed;opacity:0";
      document.body.appendChild(scratch);
      scratch.select();
      scratch.setSelectionRange(0, text.length);
      const ok = document.execCommand("copy");
      scratch.remove();
      toast(ok ? "已複製" : "複製失敗");
    }
  }

  function search(text, { remember = true } = {}) {
    el.query.value = text;
    el.clear.hidden = !text;
    if (!text.trim()) { showEmpty(); return; }
    render(text);
    if (remember) rememberQuery(text);
  }

  let typingTimer;
  function onInput() {
    const text = el.query.value;
    el.clear.hidden = !text;
    clearTimeout(typingTimer);
    if (!text.trim()) { showEmpty(); return; }
    typingTimer = setTimeout(() => render(text), 80);
  }

  function wireUp() {
    el.query.addEventListener("input", onInput);

    el.form.addEventListener("submit", (event) => {
      event.preventDefault();
      el.query.blur();                       // 收起 iOS 鍵盤
      const text = el.query.value;
      if (text.trim()) { render(text); rememberQuery(text); }
    });

    el.clear.addEventListener("click", () => {
      search("", { remember: false });
      el.query.focus();
    });

    for (const button of document.querySelectorAll(".copy")) {
      button.addEventListener("click", () => {
        const target = button.dataset.copy === "keys" ? el.keys : el.tones;
        copy(Array.from(target.children).map((n) => n.textContent).join(" ").trim());
      });
    }

    for (const button of document.querySelectorAll(".example")) {
      button.addEventListener("click", () => search(button.textContent));
    }

    el.clearHistory.addEventListener("click", () => {
      saveHistory([]);
      renderHistory();
    });
  }

  /* ---------------- 離線狀態 ---------------- */

  async function offlineReady() {
    if (!("caches" in window)) return false;
    for (const name of await caches.keys()) {
      if (!name.startsWith(CACHE_PREFIX)) continue;
      const cache = await caches.open(name);
      if (await cache.match("./data/words.txt")) return true;
    }
    return false;
  }

  function setStatus(text, state) {
    el.status.textContent = text;
    el.status.dataset.state = state || "";
  }

  async function watchOfflineStatus() {
    for (let attempt = 0; attempt < 40; attempt++) {
      if (await offlineReady()) {
        setStatus("已可離線使用", "ready");
        return;
      }
      await new Promise((resolve) => setTimeout(resolve, 1500));
    }
    setStatus("離線資料下載中", "");
  }

  function registerWorker() {
    if (!("serviceWorker" in navigator)) {
      setStatus("此瀏覽器不支援離線", "error");
      return;
    }
    navigator.serviceWorker.register("./sw.js").then(watchOfflineStatus).catch(() => {
      setStatus("離線功能無法啟用", "error");
    });
  }

  /* ---------------- 啟動 ---------------- */

  async function start() {
    wireUp();
    renderHistory();
    el.status.addEventListener("click", () => {
      toast(
        el.status.dataset.state === "ready"
          ? "字典已存在這台裝置上，關掉網路也能查。"
          : "正在把字典存到這台裝置，請保持連線幾秒。"
      );
    });

    try {
      await loadData();
      setStatus("字典已載入", "");
    } catch {
      setStatus("字典載入失敗", "error");
      return;
    }

    registerWorker();

    const shared = new URLSearchParams(location.search).get("q");
    if (shared) search(shared);
  }

  start();
})();
