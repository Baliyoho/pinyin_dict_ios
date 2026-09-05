/* 拼音字典 — 輸入漢字，查出在 iOS 拼音鍵盤上要打的字母。整份資料離線存在裝置上。 */
(() => {
  "use strict";

  const CACHE_PREFIX = "pinyin-dict-";
  const HISTORY_KEY = "pinyin-dict.history";
  const HISTORY_MAX = 12;
  const INPUT_MAX = 200;

  const HAN = /\p{Script=Han}/u;

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
    keys: document.getElementById("out-keys"),
    note: document.getElementById("out-note"),
    cards: document.getElementById("cards"),
    historyBox: document.getElementById("history-box"),
    history: document.getElementById("history"),
    clearHistory: document.getElementById("clear-history"),
    toast: document.getElementById("toast"),
  };

  /* ---------------- 讀音 -> 鍵盤字母 ---------------- */

  // 字典存的是帶調號碼的拼音（zhong1、lv4）。鍵盤上打的就是去掉聲調的部分，
  // ü 本來就存成 v，正好是 iOS 拼音鍵盤要打的鍵。
  const keystrokes = (numbered) => numbered.slice(0, -1);

  // 字典裡以 "~" 開頭的是罕見／異讀，平常不該拿來當預設讀音。
  function readingsFor(ch) {
    const raw = chars.get(ch);
    if (!raw) return [];
    return raw.map((r) =>
      r.startsWith("~") ? { py: r.slice(1), rare: true } : { py: r, rare: false }
    );
  }

  const primaryOf = (list) => (list.find((r) => !r.rare) || list[0] || null);

  // 只差聲調的讀音（好 hǎo/hào）打起來一樣，對輸入來說是同一種拼法，合併掉。
  function spellingsOf(readings) {
    const out = [];
    for (const reading of readings) {
      const key = keystrokes(reading.py);
      const seen = out.find((s) => s.key === key);
      if (seen) {
        if (!reading.rare) seen.rare = false;
      } else {
        out.push({ key, rare: reading.rare });
      }
    }
    return out;
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

  // 以最長詞優先切分，讓多音字依詞組決定打法（銀行 打 hang，不是 xing）。
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

  // 攤平成逐字資料，附上該字的其他拼法。
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
        const reading = token.syllables[n];
        const chosen = reading ? keystrokes(reading) : null;
        const spellings = spellingsOf(readingsFor(ch));
        if (chosen && !spellings.some((s) => s.key === chosen)) {
          spellings.unshift({ key: chosen, rare: false });
        }
        const multi = spellings.filter((s) => !s.rare).length > 1;
        return { char: ch, chosen, spellings, multi };
      });
      items.push({ kind: "word", text: token.text, cells, isWord: cps.length > 1 });
    }
    return items;
  }

  /* ---------------- 畫面 ---------------- */

  function render(text) {
    const items = analyse(text);
    el.cards.textContent = "";
    el.keys.textContent = "";

    let usesV = false;
    let unknown = 0;
    let multi = 0;

    for (const item of items) {
      if (item.kind === "other") {
        const plain = item.text.trim();
        if (plain) {
          const span = document.createElement("span");
          span.className = "w plain";
          span.textContent = plain;
          el.keys.appendChild(span);
        }
        continue;
      }

      const keySpan = document.createElement("span");
      keySpan.className = "w";

      for (const cell of item.cells) {
        if (!cell.chosen) {
          unknown++;
          keySpan.textContent += "?";
        } else {
          if (cell.chosen.includes("v")) usesV = true;
          if (cell.multi) multi++;
          keySpan.textContent += cell.chosen;
        }
        el.cards.appendChild(cardFor(cell, item));
      }

      el.keys.appendChild(keySpan);
    }

    const notes = [];
    if (usesV) notes.push("ü 在拼音鍵盤上要打 v（綠 → 打 lv）。");
    if (multi) notes.push(`有 ${multi} 個字不只一種打法，這裡已依詞組挑好，點字卡可看其他拼法。`);
    if (unknown) notes.push(`有 ${unknown} 個字查不到打法。`);
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

    const key = document.createElement("span");
    key.className = "key";
    key.textContent = cell.chosen || "—";

    button.append(glyph, key);
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
      ? `「${item.text}」的${cell.char}打 ${cell.chosen || "—"}`
      : `「${cell.char}」的打法`;

    const list = document.createElement("ul");
    const ordered = [...cell.spellings].sort((a, b) => Number(a.rare) - Number(b.rare));
    for (const spelling of ordered) {
      const li = document.createElement("li");
      li.className = [spelling.key === cell.chosen ? "on" : "", spelling.rare ? "rare" : ""]
        .filter(Boolean)
        .join(" ");
      li.textContent = spelling.key;
      if (spelling.rare) {
        const tag = document.createElement("code");
        tag.textContent = "罕用";
        li.appendChild(tag);
      }
      list.appendChild(li);
    }
    if (!cell.spellings.length) {
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
      button.addEventListener("click", () =>
        copy(Array.from(el.keys.children).map((n) => n.textContent).join(" ").trim())
      );
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
