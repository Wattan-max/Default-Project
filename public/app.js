/* Vaani — client */
const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

const LANGS = {
  "hi-IN": { name: "Hindi", native: "हिंदी", glyph: "अ" },
  "ta-IN": { name: "Tamil", native: "தமிழ்", glyph: "த" },
  "te-IN": { name: "Telugu", native: "తెలుగు", glyph: "త" },
  "ml-IN": { name: "Malayalam", native: "മലയാളം", glyph: "മ" },
  "bn-IN": { name: "Bengali", native: "বাংলা", glyph: "ব" },
  "mr-IN": { name: "Marathi", native: "मराठी", glyph: "म" },
  "kn-IN": { name: "Kannada", native: "ಕನ್ನಡ", glyph: "ಕ" },
  "gu-IN": { name: "Gujarati", native: "ગુજરાતી", glyph: "ગ" },
  "pa-IN": { name: "Punjabi", native: "ਪੰਜਾਬੀ", glyph: "ਪ" },
  "od-IN": { name: "Odia", native: "ଓଡ଼ିଆ", glyph: "ଓ" },
  "ur-IN": { name: "Urdu", native: "اردو", glyph: "ا" },
  "en-IN": { name: "English", native: "English", glyph: "A" },
};
const LANG_ORDER = ["hi-IN", "ta-IN", "te-IN", "ml-IN", "bn-IN", "mr-IN", "kn-IN", "gu-IN", "pa-IN", "od-IN", "ur-IN", "en-IN"];

const SAMPLES = [
  {
    label: "Hinglish", glyph: "अ", lang: "hi-IN",
    text: "Kal electrician ko call karna hai aur Monday tak rent pay karna hai.",
  },
  {
    label: "हिंदी", glyph: "अ", lang: "hi-IN",
    text: "डॉक्टर से कल सुबह मिलना है और शाम को दवाई लेनी है। बिजली का बिल आज ही जमा करना है।",
  },
  {
    label: "தமிழ்", glyph: "த", lang: "ta-IN",
    text: "நாளைக்கு காலையில் எலக்ட்ரீஷியனுக்கு கால் செய்ய வேண்டும். திங்கட்கிழமைக்குள் வீட்டு வாடகை கட்ட வேண்டும்.",
  },
  {
    label: "తెలుగు", glyph: "త", lang: "te-IN",
    text: "రేపు ఉదయం ఎలక్ట్రిషియన్‌కు కాల్ చేయాలి. సోమవారం లోపు అద్దె కట్టాలి.",
  },
  {
    label: "മലയാളം", glyph: "മ", lang: "ml-IN",
    text: "നാളെ രാവിലെ ഡോക്ടറെ കാണണം. തിങ്കളാഴ്ചയ്ക്ക് മുൻപ് വാടക അടയ്ക്കണം.",
  },
  {
    label: "বাংলা", glyph: "ব", lang: "bn-IN",
    text: "কাল সকালে ইলেকট্রিশিয়ানকে ফোন করতে হবে। সোমবারের মধ্যে বাড়িভাড়া দিতে হবে।",
  },
  {
    label: "YouTube", glyph: "▶", lang: "en-IN",
    text: "YouTube pe AR Rahman ke best songs search karo.",
  },
];

const ICONS = {
  call: '<path d="M6.6 3.6l2.2 3.4-1.6 1.6a13.2 13.2 0 0 0 6.2 6.2l1.6-1.6 3.4 2.2-.9 2.5a2 2 0 0 1-2 1.4C9.6 19 5 14.4 3.1 6.5a2 2 0 0 1 1.4-2l2.1-.9z"/>',
  payment: '<rect x="2.5" y="6" width="19" height="12" rx="2.5"/><circle cx="12" cy="12" r="2.6"/><path d="M6.2 12h.01M17.8 12h.01"/>',
  health: '<path d="M12 20.5S4.8 16.1 4.8 10.4A4.2 4.2 0 0 1 12 7.5a4.2 4.2 0 0 1 7.2 2.9c0 5.7-7.2 10.1-7.2 10.1z"/><path d="M9 11.5h6M12 8.5v6"/>',
  meeting: '<circle cx="9" cy="8" r="3"/><path d="M3.5 20a5.5 5.5 0 0 1 11 0"/><path d="M16 5.6a3 3 0 0 1 0 5.8M17.2 14.4A5 5 0 0 1 20.5 20"/>',
  travel: '<circle cx="12" cy="12" r="9"/><path d="M15.5 8.5l-2 5-5 2 2-5 5-2z"/>',
  shopping: '<path d="M5 8h14l-1.1 11.2a2 2 0 0 1-2 1.8H8.1a2 2 0 0 1-2-1.8L5 8z"/><path d="M9 8V6.5a3 3 0 0 1 6 0V8"/>',
  home: '<path d="M4 10.5L12 4l8 6.5V20a1 1 0 0 1-1 1h-4v-6H9v6H5a1 1 0 0 1-1-1v-9.5z"/>',
  work: '<rect x="3" y="7.5" width="18" height="12" rx="2"/><path d="M9 7.5V6a1.5 1.5 0 0 1 1.5-1.5h3A1.5 1.5 0 0 1 15 6v1.5M3 12.5h18M10 12.5v2h4v-2"/>',
  other: '<path d="M5 12h14"/><path d="M12 5v14"/>',
};

const ICON_COPY = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="9" y="9" width="11" height="12" rx="2"/><path d="M15 5.5A2.5 2.5 0 0 0 12.5 3H6a2 2 0 0 0-2 2v10"/></svg>';
const ICON_PLAY = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 9v6h4l5 4V5L8 9H4z"/><path d="M16.5 8.5a5 5 0 0 1 0 7"/></svg>';
const ICON_CHECK = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12.5l5 5L20 6.5"/></svg>';
const ICON_CAL = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><rect x="3" y="5" width="18" height="16" rx="3"/><path d="M8 3v4M16 3v4M3 10h18"/></svg>';
const ICON_CLOCK = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3.5 2"/></svg>';
const ICON_EXTERNAL = '<svg class="ext" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M14 4h6v6M20 4l-9 9"/><path d="M18 14v5a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h5"/></svg>';

const SERVICE_NAMES = {
  youtube: "YouTube", google: "Google", maps: "Google Maps", amazon: "Amazon", flipkart: "Flipkart",
};
const ACTION_KICKERS = { call: "Call", message: "WhatsApp", email: "Email" };
const ACTION_PATHS = {
  youtube: '<path d="M4 9v6h4l5 4V5L8 9H4z"/><path d="M16.5 8.5a5 5 0 0 1 0 7"/>',
  google: '<circle cx="11" cy="11" r="7"/><path d="M20 20l-3.6-3.6"/>',
  maps: '<path d="M12 21s7-5.5 7-11a7 7 0 1 0-14 0c0 5.5 7 11 7 11z"/><circle cx="12" cy="10" r="2.5"/>',
  amazon: ICONS.shopping,
  flipkart: ICONS.shopping,
  call: ICONS.call,
  message: '<path d="M21 11.5a8.5 8.5 0 0 1-12.3 7.6L3 21l1.9-5.7A8.5 8.5 0 1 1 21 11.5z"/>',
  email: '<rect x="3" y="5" width="18" height="14" rx="2.5"/><path d="M3.5 7l8.5 6 8.5-6"/>',
};

const STORAGE = { key: "vaani.key", last: "vaani.last" };

const state = {
  key: safeGet(STORAGE.key) || "",
  serverKey: false,
  result: null,
  done: new Set(),
  translation: null,
  translationShown: false,
  busy: false,
  stream: null,
  recorder: null,
  chunks: [],
  recording: false,
  startedAt: 0,
  timerId: null,
  meterId: null,
  audioCtx: null,
  analyser: null,
  audio: null,
  audioUrl: null,
  playingBtn: null,
  step: 0,
  stepTimer: null,
  pipelineDone: false,
  pipelineMeta: "",
};

/* ---------- tiny utilities ---------- */

function safeGet(key) {
  try { return localStorage.getItem(key); } catch { return null; }
}
function safeSet(key, value) {
  try { localStorage.setItem(key, value); } catch { /* private mode */ }
}
function safeRemove(key) {
  try { localStorage.removeItem(key); } catch { /* ignore */ }
}
function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (ch) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[ch]));
}
function langInfo(code) {
  return LANGS[code] || { name: "Unknown", native: "", glyph: "?" };
}

/* Action links arrive already built by the server. This is a last-line check
   so a tampered localStorage entry can never become a javascript: link. */
function actionHref(url) {
  return typeof url === "string" && /^(https:\/\/|tel:|mailto:)/i.test(url) ? url : "";
}
function actionIcon(action) {
  const key = action.type === "search" ? action.service : action.type;
  const paths = ACTION_PATHS[key] || ICONS.other;
  return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths}</svg>`;
}
function actionKicker(action) {
  if (action.type === "search") return `Search · ${SERVICE_NAMES[action.service] || "Web"}`;
  return ACTION_KICKERS[action.type] || "Action";
}
function actionLink(action, className) {
  const href = actionHref(action?.url);
  if (!action || !href) return "";
  const external = /^https:/.test(href);
  const attrs = external ? ' target="_blank" rel="noopener noreferrer"' : "";
  return `<a class="${className}" href="${escapeHtml(href)}"${attrs}>${actionIcon(action)}<span>${escapeHtml(action.label)}</span>${ICON_EXTERNAL}</a>`;
}

let toastTimer = null;
function toast(message, type = "", duration = 4600) {
  const el = $("#toast");
  el.textContent = message;
  el.className = `toast ${type}`.trim();
  el.hidden = false;
  requestAnimationFrame(() => el.classList.add("show"));
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    el.classList.remove("show");
    setTimeout(() => { el.hidden = true; }, 240);
  }, duration);
}

function hasLiveKey() {
  return Boolean(state.key || state.serverKey);
}

/* ---------- setup ---------- */

function populateLanguages() {
  const speak = $("#speakLang");
  const target = $("#targetLang");
  speak.innerHTML = '<option value="unknown">Detect automatically</option>';
  target.innerHTML = '<option value="match">Match what I speak</option>';
  for (const code of LANG_ORDER) {
    const info = langInfo(code);
    const label = info.native && info.native !== info.name ? `${info.name} · ${info.native}` : info.name;
    speak.insertAdjacentHTML("beforeend", `<option value="${code}">${escapeHtml(label)}</option>`);
    target.insertAdjacentHTML("beforeend", `<option value="${code}">${escapeHtml(label)}</option>`);
  }
  target.value = "match";
}

function buildSamples() {
  const wrap = $("#sampleChips");
  SAMPLES.forEach((sample, index) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "chip";
    button.dataset.sample = String(index);
    button.innerHTML = `<span class="chip-glyph" aria-hidden="true">${escapeHtml(sample.glyph)}</span>${escapeHtml(sample.label)}`;
    wrap.appendChild(button);
  });
}

function buildLevels() {
  const wrap = $("#levels");
  wrap.innerHTML = "";
  for (let i = 0; i < 26; i += 1) {
    const bar = document.createElement("i");
    bar.style.height = "4px";
    wrap.appendChild(bar);
  }
}

function setMode() {
  const pill = $("#modePill");
  const text = $("#modeText");
  const live = hasLiveKey();
  pill.classList.toggle("live", live);
  pill.classList.toggle("demo", !live);
  if (state.key) text.textContent = "Live · your key";
  else if (state.serverKey) text.textContent = "Live · Sarvam";
  else text.textContent = "Demo mode";
}

async function checkHealth() {
  try {
    const response = await fetch("/api/health", { cache: "no-store" });
    if (!response.ok) throw new Error("offline");
    const health = await response.json();
    state.serverKey = Boolean(health.key_configured);
    if (health.languages && typeof health.languages === "object") {
      Object.assign(LANGS, health.languages);
    }
    setMode();
  } catch {
    state.serverKey = false;
    $("#modeText").textContent = "Server offline";
    $("#modePill").classList.remove("live");
    $("#modePill").classList.add("demo");
  }
}

/* ---------- views ---------- */

function showView(view) {
  $("#emptyState").hidden = view !== "empty";
  $("#loadingState").hidden = view !== "loading";
  $("#resultState").hidden = view !== "result";
  $("#resultTools").hidden = view !== "result";
}

function renderResult(result, doneIds = []) {
  stopAudio();
  state.result = result;
  state.done = new Set(doneIds);
  state.translation = null;
  state.translationShown = false;

  const lang = langInfo(result.language_code);
  $("#langGlyph").textContent = lang.glyph || "?";
  $("#langName").textContent = lang.native && lang.native !== lang.name
    ? `${lang.name} · ${lang.native}`
    : lang.name;

  let confidence = "";
  if (typeof result.language_probability === "number") {
    confidence = `${Math.round(result.language_probability * 100)}% confidence`;
  } else if (result.source === "audio") {
    confidence = "auto-detected";
  } else {
    confidence = "typed note";
  }
  $("#confidence").textContent = confidence;

  $("#transcriptText").textContent = result.transcript;
  $("#summaryText").textContent = result.summary;
  $("#translationBox").hidden = true;
  $("#translationText").textContent = "";
  $("#translateBtn").disabled = false;
  $("#translateBtn").textContent = result.language_code === "en-IN" ? "Translate to Hindi" : "Translate to English";

  const target = result.target_language_name || langInfo(result.target_language).name;
  const count = result.tasks.length;
  const seconds = result.timings?.total_ms >= 200 ? (result.timings.total_ms / 1000).toFixed(1) : "";
  if (!count && result.command) {
    $("#resultMeta").textContent = `${target} · ready to open${seconds ? ` · ${seconds}s` : ""}`;
  } else {
    $("#resultMeta").textContent = `Plan in ${target} · ${count} task${count === 1 ? "" : "s"}${seconds ? ` · ${seconds}s` : ""}`;
  }

  const notice = $("#demoNotice");
  if (result.notice) {
    notice.textContent = result.notice;
    notice.hidden = false;
  } else {
    notice.hidden = true;
  }

  renderCommand(result.command);
  renderTasks();
  showView("result");
}

function renderCommand(command) {
  const box = $("#commandCard");
  const href = actionHref(command?.url);
  if (!command || !href) {
    box.hidden = true;
    box.innerHTML = "";
    return;
  }
  box.innerHTML = `
    <span class="command-icon" aria-hidden="true">${actionIcon(command)}</span>
    <div class="command-copy">
      <span class="command-kicker">${escapeHtml(actionKicker(command))}</span>
      <h3>${escapeHtml(command.detail || command.label)}</h3>
    </div>
    ${actionLink(command, "command-go")}`;
  box.hidden = false;
}

function renderTasks() {
  if (!state.result) return;
  const list = $("#taskList");
  list.innerHTML = "";
  if (!state.result.tasks.length && !state.result.command) {
    list.innerHTML = '<p class="notice">No clear action found in this note. Try adding what needs to be done and by when.</p>';
  }

  state.result.tasks.forEach((task) => {
    const done = state.done.has(task.id);
    const due = dueInfo(task, state.result.target_language || state.result.language_code);
    const priorityLabel = { high: "High", medium: "Medium", low: "Low" }[task.priority] || "Medium";
    const category = task.category || "other";
    const icon = ICONS[category] || ICONS.other;
    const showEnglish = task.title_en && task.title_en !== task.title;
    const reminderText = task.reminder || "";
    const canSpeak = Boolean(reminderText);
    const action = task.action ? actionLink(task.action, "task-action") : "";

    const article = document.createElement("article");
    article.className = `task${done ? " done" : ""}`;
    article.dataset.priority = task.priority || "medium";
    article.dataset.id = task.id;
    article.innerHTML = `
      <button class="tick" type="button" aria-label="${done ? "Mark as not done" : "Mark as done"}" aria-pressed="${done}" data-action="toggle">
        ${ICON_CHECK}
      </button>
      <div class="task-main">
        <div class="task-head">
          <h3 class="task-title">${escapeHtml(task.title)}
            ${showEnglish ? `<span class="task-title-en">${escapeHtml(task.title_en)}</span>` : ""}
          </h3>
          <span class="prio ${escapeHtml(task.priority || "medium")}">${priorityLabel}</span>
        </div>
        <div class="task-meta">
          ${due.label ? `<span class="meta-chip due${due.overdue ? " overdue" : ""}" title="${escapeHtml(due.title)}">${ICON_CAL}${escapeHtml(due.label)}</span>` : ""}
          ${task.due_time && !due.hasTime ? `<span class="meta-chip">${ICON_CLOCK}${escapeHtml(task.due_time)}</span>` : ""}
          <span class="meta-chip cat">${escapeHtml(category)}</span>
          ${task.why ? `<span class="meta-chip">${escapeHtml(task.why)}</span>` : ""}
        </div>
        ${action}
        ${reminderText ? `
          <div class="reminder">
            <div class="reminder-head">
              <span>Draft reminder</span>
              <div class="reminder-actions">
                <button class="mini-btn" type="button" data-action="copy" title="Copy reminder" aria-label="Copy reminder">${ICON_COPY}</button>
                ${canSpeak ? `<button class="mini-btn" type="button" data-action="play" title="Play reminder" aria-label="Play reminder">${ICON_PLAY}</button>` : ""}
              </div>
            </div>
            <p>${escapeHtml(reminderText)}</p>
          </div>` : ""}
      </div>`;
    list.appendChild(article);
  });

  updateCount();
}

function updateCount() {
  if (!state.result) return;
  const total = state.result.tasks.length;
  const done = state.done.size;
  $("#taskCount").textContent = total ? `${total - done} open · ${done} done` : "";
}

function dueInfo(task, language = "en-IN") {
  const locale = LANGS[language] ? language : "en-IN";
  if (!task.due_iso) {
    return { label: task.due_label || "", overdue: false, title: task.due_label || "", hasTime: false };
  }
  const date = new Date(`${task.due_iso}T00:00:00`);
  if (Number.isNaN(date.getTime())) {
    return { label: task.due_label || "", overdue: false, title: task.due_label || "", hasTime: false };
  }
  // Deadlines are resolved in IST on the server, so compare against IST today
  // rather than the browser's local date.
  const todayParts = new Intl.DateTimeFormat("en-GB", {
    timeZone: "Asia/Kolkata", year: "numeric", month: "2-digit", day: "2-digit",
  }).formatToParts(new Date());
  const part = (type) => todayParts.find((item) => item.type === type)?.value;
  const today = new Date(`${part("year")}-${part("month")}-${part("day")}T00:00:00`);
  const diff = Math.round((date - today) / 86_400_000);
  const relative = diff === 0 ? "Today" : diff === 1 ? "Tomorrow" : diff < 0 ? "Overdue" : "";
  const short = date.toLocaleDateString(locale, { day: "numeric", month: "short" });
  let label = task.due_label || relative || short;
  if (task.due_label && !task.due_label.includes(short) && task.due_label.toLowerCase() !== relative.toLowerCase()) {
    label += ` · ${short}`;
  }
  if (task.due_time) label += `, ${task.due_time}`;
  const title = date.toLocaleDateString(locale, { weekday: "long", day: "numeric", month: "long", year: "numeric" });
  return { label, overdue: diff < 0, title, hasTime: Boolean(task.due_time) };
}

/* ---------- submit ---------- */

function setBusy(busy) {
  state.busy = busy;
  $("#processText").disabled = busy;
  $("#micBtn").disabled = busy;
  $$("#sampleChips .chip").forEach((chip) => { chip.disabled = busy; });
}

async function submit({ body, headers }) {
  if (state.busy) return;
  setBusy(true);
  showView("loading");
  startPipeline();

  const started = performance.now();
  try {
    const response = await fetch("/api/process", {
      method: "POST",
      headers: { "X-Sarvam-Key": state.key, ...headers },
      body,
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      const error = new Error(data.error || "Could not build your plan.");
      error.hint = data.hint || "";
      throw error;
    }
    renderResult(data, []);
    persist();
    finishPipeline(data.timings, performance.now() - started);
    if (data.demo) {
      toast(
        data.command && !data.tasks.length
          ? "Demo command ready. Add a Sarvam key for live understanding."
          : "Demo plan ready. Add a Sarvam key for live voice and reasoning.",
        "info",
        5200,
      );
    } else if (data.command && !data.tasks.length) {
      toast("Command ready — one tap to open.", "", 3200);
    } else {
      toast("Your plan is ready.", "", 3200);
    }
  } catch (error) {
    hidePipeline();
    if (state.result) showView("result");
    else showView("empty");
    const message = error.message || "Something went wrong.";
    toast(error.hint ? `${message} ${error.hint}` : message, "error", 7000);
    if ((error.hint || message).toLowerCase().includes("key")) openKeyDialog();
  } finally {
    setBusy(false);
  }
}

function processText(text) {
  const note = (text ?? $("#noteText").value).trim();
  if (!note) {
    toast("Type or record something first.", "info");
    $("#noteText").focus();
    return;
  }
  submit({
    body: new TextEncoder().encode(note),
    headers: {
      "Content-Type": "text/plain; charset=utf-8",
      "X-Source": "text",
      "X-Target": $("#targetLang").value,
    },
  });
}

function processAudio(blob, filename) {
  if (!blob || blob.size < 900) {
    toast("That recording was too short — try again.", "info");
    return;
  }
  if (blob.size > 25 * 1024 * 1024) {
    toast("That file is too large. Keep audio under 25 MB.", "error");
    return;
  }
  submit({
    body: blob,
    headers: {
      "Content-Type": blob.type || "audio/webm",
      "X-Source": "audio",
      "X-Filename": filename || (blob.type.includes("mp4") ? "note.m4a" : "note.webm"),
      "X-Speak-Lang": $("#speakLang").value,
      "X-Target": $("#targetLang").value,
    },
  });
}

/* ---------- pipeline ---------- */

function startPipeline() {
  const pipeline = $("#pipeline");
  pipeline.hidden = false;
  clearInterval(state.stepTimer);
  state.step = 0;
  state.pipelineDone = false;
  state.pipelineMeta = "";
  paintPipeline();
  state.stepTimer = setInterval(() => {
    if (state.step < 3) {
      state.step += 1;
      paintPipeline();
    }
  }, 1250);
}

function paintPipeline() {
  $$(".pipe-step").forEach((el) => {
    const index = Number(el.dataset.step);
    el.classList.toggle("active", !state.pipelineDone && index === state.step);
    el.classList.toggle("done", state.pipelineDone || index < state.step);
  });
  $("#pipelineMeta").textContent = state.pipelineDone ? state.pipelineMeta : "";
}

function finishPipeline(timings, elapsedMs) {
  clearInterval(state.stepTimer);
  state.pipelineDone = true;
  const time = (ms) => (ms >= 1000 ? `${(ms / 1000).toFixed(1)}s` : `${Math.round(ms)}ms`);
  const parts = [];
  if (timings?.transcribe_ms) parts.push(`heard in ${time(timings.transcribe_ms)}`);
  if (timings?.plan_ms) parts.push(`planned in ${time(timings.plan_ms)}`);
  state.pipelineMeta = parts.length ? parts.join(" · ") : `${(elapsedMs / 1000).toFixed(1)}s`;
  paintPipeline();
}

function hidePipeline() {
  clearInterval(state.stepTimer);
  $("#pipeline").hidden = true;
  $("#pipelineMeta").textContent = "";
  state.step = 0;
  state.pipelineDone = false;
  $$(".pipe-step").forEach((el) => el.classList.remove("active", "done"));
}

/* ---------- recording ---------- */

function pickMimeType() {
  const candidates = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4"];
  return candidates.find((type) => window.MediaRecorder?.isTypeSupported?.(type)) || "";
}

async function startRecording() {
  if (state.busy) return;
  if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
    toast("Recording isn't available in this browser. Upload an audio file instead.", "error");
    return;
  }
  try {
    state.stream = await navigator.mediaDevices.getUserMedia({
      audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true },
    });
  } catch {
    toast("Microphone access was blocked. Allow it in your browser, or upload a file.", "error", 6000);
    return;
  }

  const mimeType = pickMimeType();
  try {
    state.recorder = new MediaRecorder(state.stream, mimeType ? { mimeType, audioBitsPerSecond: 128000 } : undefined);
  } catch {
    try {
      state.recorder = new MediaRecorder(state.stream);
    } catch {
      cleanupRecorder();
      toast("This browser can't record audio. Upload a file instead.", "error");
      return;
    }
  }

  state.chunks = [];
  state.recorder.ondataavailable = (event) => {
    if (event.data && event.data.size > 0) state.chunks.push(event.data);
  };
  state.recorder.onstop = () => {
    const type = state.recorder?.mimeType?.split(";")[0] || "audio/webm";
    const blob = new Blob(state.chunks, { type });
    cleanupRecorder();
    if (blob.size > 900) processAudio(blob, type.includes("mp4") ? "note.m4a" : "note.webm");
    else toast("That was too short — hold on and speak a full sentence.", "info");
  };

  state.recorder.start(250);
  state.recording = true;
  state.startedAt = Date.now();
  $("#recorder").classList.add("recording");
  $("#micBtn").setAttribute("aria-pressed", "true");
  $("#micBtn").setAttribute("aria-label", "Stop recording");
  $("#recTitle").textContent = "Listening…";
  $("#recSub").textContent = "Tap the mic again when you're done";
  $("#timer").hidden = false;
  $("#timer").textContent = "0:00";
  $("#inputTag").textContent = "Recording";

  state.timerId = setInterval(() => {
    const seconds = Math.floor((Date.now() - state.startedAt) / 1000);
    $("#timer").textContent = `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}`;
    if (seconds >= 120) stopRecording();
  }, 200);

  startMeter(state.stream);
}

function stopRecording() {
  if (!state.recording) return;
  state.recording = false;
  $("#recorder").classList.remove("recording");
  $("#micBtn").setAttribute("aria-pressed", "false");
  $("#micBtn").setAttribute("aria-label", "Start recording");
  $("#recTitle").textContent = "Got it — building your plan…";
  $("#recSub").textContent = "This usually takes a few seconds";
  try {
    if (state.recorder && state.recorder.state !== "inactive") state.recorder.stop();
  } catch {
    cleanupRecorder();
  }
}

function cleanupRecorder() {
  clearInterval(state.timerId);
  state.timerId = null;
  cancelAnimationFrame(state.meterId);
  state.meterId = null;
  if (state.audioCtx) {
    state.audioCtx.close().catch(() => {});
    state.audioCtx = null;
  }
  state.analyser = null;
  $$("#levels i").forEach((bar) => { bar.style.height = "4px"; });
  if (state.stream) {
    state.stream.getTracks().forEach((track) => track.stop());
    state.stream = null;
  }
  state.recording = false;
  state.recorder = null;
  $("#recorder").classList.remove("recording");
  $("#timer").hidden = true;
  $("#inputTag").textContent = "Mic · upload · text";
  if (!state.busy) {
    $("#recTitle").textContent = "Tap to speak";
    $("#recSub").textContent = "Hindi, Tamil, Telugu, Malayalam + 8 more";
  }
}

function startMeter(stream) {
  try {
    const AudioCtx = window.AudioContext || window.webkitAudioContext;
    state.audioCtx = new AudioCtx();
    if (state.audioCtx.state === "suspended") state.audioCtx.resume();
    const source = state.audioCtx.createMediaStreamSource(stream);
    const analyser = state.audioCtx.createAnalyser();
    analyser.fftSize = 128;
    analyser.smoothingTimeConstant = 0.75;
    source.connect(analyser);
    state.analyser = analyser;

    const bars = $$("#levels i");
    const data = new Uint8Array(analyser.frequencyBinCount);
    const draw = () => {
      if (!state.analyser) return;
      analyser.getByteFrequencyData(data);
      bars.forEach((bar, index) => {
        const value = data[Math.floor((index * data.length) / bars.length)] / 255;
        bar.style.height = `${4 + value * 22}px`;
      });
      state.meterId = requestAnimationFrame(draw);
    };
    draw();
  } catch {
    /* a silent meter is fine */
  }
}

/* ---------- translate ---------- */

async function toggleTranslation() {
  if (!state.result) return;
  const box = $("#translationBox");
  const button = $("#translateBtn");

  if (state.translation) {
    state.translationShown = !state.translationShown;
    box.hidden = !state.translationShown;
    button.textContent = state.translationShown ? "Hide translation" : "Show translation";
    return;
  }

  if (!hasLiveKey()) {
    toast("Translation runs on Sarvam. Add a key to try it.", "info");
    openKeyDialog();
    return;
  }

  const target = state.result.language_code === "en-IN" ? "hi-IN" : "en-IN";
  const targetLabel = langInfo(target).name;
  button.disabled = true;
  button.textContent = "Translating…";
  try {
    const response = await fetch("/api/translate", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Sarvam-Key": state.key },
      body: JSON.stringify({
        text: state.result.transcript,
        source: state.result.language_code,
        target,
      }),
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.error || "Translation failed.");
    const text = (data.translated_text || "").trim();
    if (!text) throw new Error("No translation came back.");
    state.translation = { text, target };
    state.translationShown = true;
    $("#translationLabel").textContent = targetLabel;
    $("#translationText").textContent = text;
    box.hidden = false;
    button.textContent = "Hide translation";
  } catch (error) {
    button.textContent = `Translate to ${targetLabel}`;
    toast(error.message, "error", 6000);
  } finally {
    button.disabled = false;
  }
}

/* ---------- voice ---------- */

function stopAudio() {
  if (state.audio) {
    state.audio.onended = null;
    state.audio.onerror = null;
    state.audio.pause();
    state.audio.removeAttribute("src");
    state.audio = null;
  }
  if (state.audioUrl) {
    URL.revokeObjectURL(state.audioUrl);
    state.audioUrl = null;
  }
  if (state.playingBtn) {
    state.playingBtn.classList.remove("playing");
    state.playingBtn = null;
  }
}

async function playText(text, language, button) {
  if (!text.trim()) return;
  if (state.playingBtn === button && state.audio && !state.audio.paused) {
    stopAudio();
    return;
  }
  stopAudio();

  if (!hasLiveKey()) {
    toast("Voice playback runs on Sarvam. Add a key to hear it.", "info");
    openKeyDialog();
    return;
  }

  button.disabled = true;
  try {
    const response = await fetch("/api/tts", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Sarvam-Key": state.key },
      body: JSON.stringify({ text, language }),
    });
    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      const error = new Error(data.error || "Voice playback failed.");
      error.hint = data.hint || "";
      throw error;
    }
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const audio = new Audio(url);
    state.audio = audio;
    state.audioUrl = url;
    state.playingBtn = button;
    button.classList.add("playing");
    audio.onended = () => stopAudio();
    audio.onerror = () => {
      stopAudio();
      toast("That audio could not be played.", "error");
    };
    await audio.play();
  } catch (error) {
    stopAudio();
    toast(error.hint ? `${error.message} ${error.hint}` : error.message, "error", 6000);
  } finally {
    button.disabled = false;
  }
}

/* ---------- copy / calendar ---------- */

async function copyText(text) {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    const area = document.createElement("textarea");
    area.value = text;
    area.style.position = "fixed";
    area.style.opacity = "0";
    document.body.appendChild(area);
    area.select();
    let ok = false;
    try { ok = document.execCommand("copy"); } catch { ok = false; }
    area.remove();
    return ok;
  }
}

function planAsText() {
  if (!state.result) return "";
  const lines = [`Vaani plan · ${state.result.target_language_name || ""}`.trim(), state.result.summary, ""];
  if (state.result.command) {
    lines.push(`Command: ${state.result.command.label}`);
    if (state.result.command.detail) lines.push(`  ${state.result.command.detail}`);
    lines.push(`  ${state.result.command.url}`);
    lines.push("");
  }
  state.result.tasks.forEach((task, index) => {
    const due = task.due_label || (task.due_iso ? task.due_iso : "No deadline");
    const mark = state.done.has(task.id) ? "[x]" : "[ ]";
    lines.push(`${mark} ${index + 1}. ${task.title}`);
    if (task.title_en && task.title_en !== task.title) lines.push(`    ${task.title_en}`);
    lines.push(`    ${due} · ${task.priority} priority`);
    if (task.reminder) lines.push(`    Reminder: ${task.reminder}`);
    lines.push("");
  });
  return lines.join("\n").trim();
}

function downloadIcs() {
  if (!state.result) return;
  const dated = state.result.tasks.filter((task) => task.due_iso);
  if (!dated.length) {
    toast("None of these tasks have a resolved date yet.", "info");
    return;
  }
  const stamp = new Date().toISOString().replace(/[-:]/g, "").split(".")[0] + "Z";
  const lines = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//Vaani//Voice to Action//EN",
    "CALSCALE:GREGORIAN",
  ];
  dated.forEach((task, index) => {
    const start = task.due_iso.replaceAll("-", "");
    const endDate = new Date(`${task.due_iso}T00:00:00Z`);
    endDate.setUTCDate(endDate.getUTCDate() + 1);
    const end = endDate.toISOString().slice(0, 10).replaceAll("-", "");
    const summary = (task.title_en || task.title).replace(/[,;\\]/g, " ").replace(/\n/g, " ");
    const description = (task.reminder_en || task.reminder || task.title).replace(/[,;\\]/g, " ").replace(/\n/g, "\\n");
    lines.push(
      "BEGIN:VEVENT",
      `UID:vaani-${Date.now()}-${index}@localhost`,
      `DTSTAMP:${stamp}`,
      `DTSTART;VALUE=DATE:${start}`,
      `DTEND;VALUE=DATE:${end}`,
      `SUMMARY:${summary}`,
      `DESCRIPTION:${description}`,
      `PRIORITY:${task.priority === "high" ? 1 : task.priority === "low" ? 9 : 5}`,
      "END:VEVENT",
    );
  });
  lines.push("END:VCALENDAR");
  const blob = new Blob([lines.join("\r\n")], { type: "text/calendar;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "vaani-plan.ics";
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
  toast(`Added ${dated.length} dated task${dated.length === 1 ? "" : "s"} to your calendar.`, "", 3600);
}

/* ---------- persistence ---------- */

function persist() {
  if (!state.result) return;
  safeSet(STORAGE.last, JSON.stringify({ result: state.result, done: [...state.done], at: Date.now() }));
}

function restore() {
  const raw = safeGet(STORAGE.last);
  if (!raw) return false;
  try {
    const saved = JSON.parse(raw);
    if (!saved?.result?.tasks) return false;
    renderResult(saved.result, saved.done || []);
    return true;
  } catch {
    return false;
  }
}

function resetPlan() {
  state.result = null;
  state.done = new Set();
  state.translation = null;
  safeRemove(STORAGE.last);
  hidePipeline();
  showView("empty");
  $("#commandCard").hidden = true;
  $("#commandCard").innerHTML = "";
  $("#resultMeta").textContent = "Clean tasks, real deadlines, a message you can send.";
  stopAudio();
  toast("Cleared. Ready for the next note.", "info", 2800);
  $("#noteText").value = "";
  $("#charCount").textContent = "0 / 4000";
}

/* ---------- key dialog ---------- */

function openKeyDialog() {
  $("#keyInput").value = state.key;
  const hint = $("#demoHint");
  if (state.serverKey) {
    hint.textContent = "This server already has a key configured. Saving one here overrides it for this browser.";
    hint.classList.remove("warn");
  } else if (state.key) {
    hint.textContent = "A key is saved in this browser. Use demo mode to remove it.";
    hint.classList.remove("warn");
  } else {
    hint.textContent = "No key yet — everything except live audio still works in demo mode.";
    hint.classList.add("warn");
  }
  const dialog = $("#keyDialog");
  if (!dialog.open) dialog.showModal();
  setTimeout(() => $("#keyInput").focus(), 60);
}

function saveKey() {
  const value = $("#keyInput").value.trim();
  if (!value) {
    toast("Paste a key first, or choose demo mode.", "info");
    return;
  }
  state.key = value;
  safeSet(STORAGE.key, value);
  setMode();
  $("#keyDialog").close();
  toast("Sarvam key saved. Live transcription is on.", "", 3800);
}

function clearKey() {
  state.key = "";
  safeRemove(STORAGE.key);
  setMode();
  $("#keyDialog").close();
  toast("Switched to demo mode.", "info", 3000);
}

/* ---------- events ---------- */

function bindEvents() {
  $("#micBtn").addEventListener("click", () => {
    if (state.recording) stopRecording();
    else startRecording();
  });

  $("#textToggle").addEventListener("click", () => {
    const composer = $("#textComposer");
    const open = composer.hidden;
    composer.hidden = !open;
    $("#textToggle").setAttribute("aria-expanded", String(open));
    $("#textToggleLabel").textContent = open ? "Hide keyboard" : "Type instead";
    if (open) $("#noteText").focus();
  });

  $("#noteText").addEventListener("input", (event) => {
    $("#charCount").textContent = `${event.target.value.length} / 4000`;
  });

  $("#noteText").addEventListener("keydown", (event) => {
    if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
      event.preventDefault();
      processText();
    }
  });

  $("#processText").addEventListener("click", () => processText());

  $("#sampleChips").addEventListener("click", (event) => {
    const chip = event.target.closest("[data-sample]");
    if (!chip || state.busy) return;
    const sample = SAMPLES[Number(chip.dataset.sample)];
    if (!sample) return;
    $("#textComposer").hidden = false;
    $("#textToggle").setAttribute("aria-expanded", "true");
    $("#noteText").value = sample.text;
    $("#charCount").textContent = `${sample.text.length} / 4000`;
    $("#speakLang").value = sample.lang;
    $("#targetLang").value = "match";
    processText(sample.text);
  });

  $("#fileInput").addEventListener("change", (event) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file || state.busy) return;
    processAudio(file, file.name);
  });

  $("#taskList").addEventListener("click", async (event) => {
    const button = event.target.closest("[data-action]");
    if (!button || !state.result) return;
    const card = button.closest(".task");
    const task = state.result.tasks.find((item) => item.id === card?.dataset.id);
    if (!task) return;

    if (button.dataset.action === "toggle") {
      if (state.done.has(task.id)) state.done.delete(task.id);
      else state.done.add(task.id);
      card.classList.toggle("done", state.done.has(task.id));
      button.setAttribute("aria-pressed", String(state.done.has(task.id)));
      button.setAttribute("aria-label", state.done.has(task.id) ? "Mark as not done" : "Mark as done");
      updateCount();
      persist();
      return;
    }

    if (button.dataset.action === "copy") {
      const ok = await copyText(task.reminder || "");
      if (ok) {
        button.classList.add("copied");
        toast("Reminder copied — paste it wherever you need.", "", 2600);
        setTimeout(() => button.classList.remove("copied"), 1600);
      } else {
        toast("Couldn't copy. Select the text manually.", "error");
      }
      return;
    }

    if (button.dataset.action === "play") {
      // The reminder is written in the plan language, not the detected language.
      playText(task.reminder, state.result.target_language || state.result.language_code, button);
    }
  });

  $("#translateBtn").addEventListener("click", toggleTranslation);

  $("#speakBriefing").addEventListener("click", () => {
    if (!state.result) return;
    playText(state.result.briefing || state.result.summary, state.result.target_language || state.result.language_code, $("#speakBriefing"));
  });

  $("#copyAll").addEventListener("click", async () => {
    const ok = await copyText(planAsText());
    toast(ok ? "Full plan copied." : "Couldn't copy the plan.", ok ? "" : "error", 2600);
  });

  $("#downloadIcs").addEventListener("click", downloadIcs);
  $("#resetBtn").addEventListener("click", resetPlan);

  $("#keyBtn").addEventListener("click", openKeyDialog);
  $("#modePill").addEventListener("click", openKeyDialog);
  $("#saveKey").addEventListener("click", saveKey);
  $("#clearKey").addEventListener("click", clearKey);
  $("#keyForm").addEventListener("submit", (event) => {
    event.preventDefault();
    if (event.submitter?.id === "closeKey") $("#keyDialog").close();
    else saveKey();
  });
  $("#keyInput").addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      saveKey();
    }
  });
  $("#keyDialog").addEventListener("click", (event) => {
    if (event.target === $("#keyDialog")) $("#keyDialog").close();
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && state.recording) stopRecording();
  });
  window.addEventListener("beforeunload", stopAudio);
}

/* ---------- boot ---------- */

function init() {
  populateLanguages();
  buildSamples();
  buildLevels();
  bindEvents();
  checkHealth();
  if (!restore()) showView("empty");
}

init();
