const $ = (id) => document.getElementById(id);
let book = null;
let currentChapter = 0;
let pollTimer = null;
let isDemo = false;
let libraryItems = [];
const pdfInput = $("pdfInput");
const dropzone = $("dropzone");
const audio = $("audio");

function setMessage(message) { $("playerMessage").textContent = message; }
function setStatus(message, kind = "") {
  const el = $("status");
  el.innerHTML = `<span></span>${escapeHtml(message)}`;
  el.className = `status-pill ${kind}`.trim();
}
function setProgress(percent, message) {
  const value = Math.max(0, Math.min(100, Number(percent) || 0));
  $("progressWrap").hidden = false;
  $("progressBar").style.width = `${value}%`;
  $("progressPercent").textContent = `${Math.round(value)}%`;
  $("progressMessage").textContent = message || "Working…";
}
function stopPolling() { if (pollTimer) clearInterval(pollTimer); pollTimer = null; }

function renderLibrary(books = libraryItems) {
  libraryItems = books;
  const box = $("libraryFiles");
  box.innerHTML = "";
  if (!books.length) {
    box.innerHTML = '<div class="library-empty">Your uploaded books will appear here.</div>';
    return;
  }
  books.forEach(item => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "file-chip" + (book && !isDemo && book.id === item.id ? " active" : "");
    const pdf = document.createElement("span"); pdf.textContent = "PDF";
    const title = document.createElement("span"); title.textContent = item.title;
    const count = document.createElement("small"); count.textContent = `${item.chapter_count} ch`;
    button.append(pdf, title, count);
    button.title = `Open ${item.title}`;
    button.addEventListener("click", () => loadBook(item.id));
    box.appendChild(button);
  });
}

async function loadLibrary(autoOpen = false) {
  try {
    const response = await fetch("/api/library");
    if (!response.ok) throw new Error("Library could not be loaded.");
    const data = await response.json();
    renderLibrary(data.books || []);
    if (autoOpen && !book && data.books?.length) await loadBook(data.books[0].id, false);
  } catch (error) {
    setMessage(`Library connection issue: ${error.message}`);
  }
}

async function loadBook(id, scroll = true) {
  stopPolling();
  try {
    const response = await fetch(`/api/books/${encodeURIComponent(id)}`);
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Could not open the book.");
    isDemo = false;
    currentChapter = 0;
    renderBook(data);
    if (scroll) $("library").scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (error) { setMessage(error.message); setStatus("Could not open book", "error"); }
}

function renderBook(data) {
  book = data;
  $("bookTitle").textContent = data.title || "Untitled book";
  $("wordCount").textContent = Number(data.word_count || 0).toLocaleString();
  $("chapterCount").textContent = data.chapter_count || data.chapters?.length || 0;
  $("chapterHint").textContent = `${data.chapter_count || data.chapters?.length || 0} total`;
  $("deviceName").textContent = data.tts?.device || "On demand";
  $("modelName").textContent = data.tts?.model?.includes("female") ? "Female MMS VITS" : "Female MMS VITS";
  setStatus(data.status === "generated" ? "Audio available" : "PDF processed · ready", data.status === "generated" ? "success" : "");
  const list = $("chapterList");
  list.innerHTML = "";
  (data.chapters || []).forEach((chapter, index) => {
    const card = document.createElement("div");
    card.className = `chapter${index === currentChapter ? " active" : ""}`;
    const row = document.createElement("div"); row.className = "chapter-row";
    const play = document.createElement("button"); play.type = "button"; play.className = "chapter-play";
    play.title = chapter.audio ? "Play chapter" : "Select chapter";
    play.textContent = chapter.audio ? "▶" : "♫";
    const title = document.createElement("div"); title.className = "chapter-title"; title.textContent = chapter.title || `Chapter ${index + 1}`;
    row.append(play, title);
    const meta = document.createElement("div"); meta.className = "chapter-meta";
    const pieces = [`${Number(chapter.characters || 0).toLocaleString()} characters`];
    if (chapter.duration) pieces.push(formatTime(chapter.duration));
    if (chapter.audio) pieces.push("audio ready");
    else if (chapter.status === "generating") pieces.push("generating");
    meta.textContent = pieces.join(" · ");
    card.append(row, meta);
    card.addEventListener("click", () => selectChapter(index));
    play.addEventListener("click", event => {
      event.stopPropagation();
      if (chapter.audio) playChapter(index);
      else { selectChapter(index); if (!isDemo) generate(); }
    });
    list.appendChild(card);
  });
  renderLibrary();
  if (data.chapters?.length) selectChapter(Math.min(currentChapter, data.chapters.length - 1));
  else resetPlayer("No readable chapters were found in this book.");
}

function resetPlayer(message) {
  $("nowTitle").textContent = "No chapter selected";
  $("nowPreview").textContent = message;
  $("generateBtn").disabled = true;
  $("previewBtn").disabled = true;
  $("backBtn").disabled = true;
  $("nextBtn").disabled = true;
  audio.removeAttribute("src"); audio.load();
  $("downloadBtn").classList.add("disabled");
  $("downloadBtn").setAttribute("aria-disabled", "true");
}

function selectChapter(index) {
  if (!book || !book.chapters?.[index]) return;
  currentChapter = index;
  const chapter = book.chapters[index];
  $("nowTitle").textContent = chapter.title || `Chapter ${index + 1}`;
  $("nowPreview").textContent = chapter.preview || "Ready to generate your narration.";
  $("generateBtn").textContent = chapter.audio ? "Regenerate chapter" : "✦ Generate this chapter";
  $("generateBtn").disabled = isDemo;
  $("previewBtn").disabled = false;
  $("backBtn").disabled = index === 0;
  $("nextBtn").disabled = index >= book.chapters.length - 1;
  document.querySelectorAll(".chapter").forEach((item, i) => item.classList.toggle("active", i === index));
  document.querySelectorAll(".file-chip").forEach(item => item.classList.toggle("active", !isDemo && item.textContent.includes(book.title)));
  if (chapter.audio) {
    audio.src = `${chapter.audio}?v=${Date.now()}`;
    $("downloadBtn").href = chapter.audio;
    $("downloadBtn").classList.remove("disabled");
    $("downloadBtn").setAttribute("aria-disabled", "false");
    setMessage("Your chapter audio is ready. Press play to listen or download the WAV file.");
  } else {
    audio.pause(); audio.removeAttribute("src"); audio.load();
    $("downloadBtn").classList.add("disabled");
    $("downloadBtn").setAttribute("aria-disabled", "true");
    setMessage(isDemo ? "This is a browser preview demo. Upload your own PDF to generate neural narration." : "Generate this chapter to create its female neural narration.");
  }
}

function playChapter(index) {
  selectChapter(index);
  if (book.chapters[index]?.audio) audio.play().catch(() => setMessage("Your browser blocked autoplay. Press play in the audio controls."));
}

async function upload(file) {
  if (!file) return;
  if (!file.name.toLowerCase().endsWith(".pdf") || (file.type && file.type !== "application/pdf")) {
    setMessage("Please choose a PDF file."); $("uploadStatus").textContent = "PDF files only"; return;
  }
  if (file.size > 50 * 1024 * 1024) {
    setMessage("This PDF is larger than 50 MB. Please choose a smaller file."); $("uploadStatus").textContent = "File too large"; return;
  }
  stopPolling();
  setStatus("Reading PDF…", "busy");
  $("uploadStatus").textContent = "Extracting text and saving your book…";
  const form = new FormData(); form.append("pdf", file);
  try {
    const response = await fetch("/api/books", { method: "POST", body: form });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Upload failed.");
    isDemo = false; currentChapter = 0; renderBook(data); await loadLibrary();
    setStatus("PDF stored · chapters ready", "success");
    $("uploadStatus").textContent = `${data.chapter_count} chapter${data.chapter_count === 1 ? "" : "s"} created · saved to your library`;
    $("library").scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (error) {
    setStatus("Upload error", "error"); $("uploadStatus").textContent = "Could not process this PDF"; setMessage(error.message);
  } finally { pdfInput.value = ""; }
}

async function generate() {
  if (!book) { setMessage("Upload a PDF first."); return; }
  if (isDemo) { setMessage("The demo is for browser preview only. Upload a real PDF to generate neural audio."); return; }
  const chapter = book.chapters[currentChapter];
  if (!chapter) return;
  $("generateBtn").disabled = true;
  $("progressWrap").hidden = false;
  setProgress(1, "Starting your audiobook job…");
  setStatus("Preparing female voice…", "busy");
  setMessage("The first run may take a few minutes while the voice model loads. Keep this window open.");
  try {
    const response = await fetch(`/api/books/${encodeURIComponent(book.id)}/generate`, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ chapter: currentChapter })
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Generation failed.");
    if (data.status === "already_generated") {
      renderBook(data.book); $("progressWrap").hidden = true; setStatus("Chapter audio ready", "success"); return;
    }
    pollJob(data.job_id);
  } catch (error) {
    $("generateBtn").disabled = false; $("progressWrap").hidden = true;
    setStatus("Generation error", "error"); setMessage(error.message);
  }
}

function pollJob(jobId) {
  stopPolling();
  let failures = 0;
  const poll = async () => {
    try {
      const response = await fetch(`/api/jobs/${encodeURIComponent(jobId)}`);
      const job = await response.json();
      if (!response.ok) throw new Error(job.error || "Could not read generation status.");
      failures = 0;
      setProgress(job.progress, job.message);
      if (job.status === "done") {
        stopPolling();
        const selected = currentChapter;
        renderBook(job.book); currentChapter = selected; selectChapter(Math.min(selected, book.chapters.length - 1));
        $("progressWrap").hidden = true; setStatus("Chapter audio ready", "success");
        setMessage("Your narration is ready. Press play to listen or download the WAV file.");
        await loadLibrary();
      } else if (job.status === "error") {
        stopPolling(); $("generateBtn").disabled = false; $("progressWrap").hidden = true;
        setStatus("Generation error", "error"); setMessage(job.message || "The voice model could not generate this chapter.");
      }
    } catch (error) {
      failures += 1;
      if (failures >= 4) {
        stopPolling(); $("generateBtn").disabled = false; $("progressWrap").hidden = true;
        setStatus("Connection issue", "error"); setMessage(error.message);
      }
    }
  };
  pollTimer = setInterval(poll, 1200); poll();
}

function browserPreview() {
  if (!book) { setMessage("Upload a PDF first."); return; }
  if (!("speechSynthesis" in window)) { setMessage("Your browser does not support built-in speech preview. You can still generate neural audio."); return; }
  const text = book.chapters[currentChapter]?.preview || "This is your audiobook preview.";
  const speak = () => {
    const voices = window.speechSynthesis.getVoices();
    const preferred = voices.find(v => /female|samantha|aria|zira|jenny|susan|hazel|libby/i.test(v.name)) || voices.find(v => /^en(-|_)/i.test(v.lang));
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    if (preferred) { utterance.voice = preferred; utterance.lang = preferred.lang; }
    utterance.rate = 0.92; utterance.pitch = 1.04;
    utterance.onend = () => setMessage("Browser preview finished. Generate the chapter for the saved neural narration.");
    window.speechSynthesis.speak(utterance);
    setMessage(`Playing browser preview using ${preferred ? preferred.name : "your browser's default voice"}. This is separate from the female neural model.`);
  };
  if (window.speechSynthesis.getVoices().length) speak();
  else { window.speechSynthesis.onvoiceschanged = speak; window.speechSynthesis.getVoices(); }
}

function showDemo() {
  stopPolling(); isDemo = true; currentChapter = 0;
  renderBook({ id: "demo", title: "The Quiet Machine · Demo", status: "ready", word_count: 128, chapter_count: 2,
    chapters: [
      { index: 0, title: "Chapter 1 · A Quiet Beginning", characters: 720, preview: "In a small town surrounded by green hills, a curious reader discovered a hidden library. Every book held a new possibility, and every page invited a new adventure." },
      { index: 1, title: "Chapter 2 · The First Discovery", characters: 860, preview: "The old library was more than a room full of books. It was a place where imagination could travel beyond the edges of the world." }
    ]
  });
  setStatus("Interactive browser demo"); setMessage("Explore the chapter list and try Preview voice. Upload your own PDF to use neural audio generation.");
  $("library").scrollIntoView({ behavior: "smooth", block: "start" });
}

function formatTime(seconds) { seconds = Math.round(seconds || 0); return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}`; }
function escapeHtml(value) { return String(value).replace(/[&<>"']/g, char => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[char])); }
function openPicker() { pdfInput.click(); }

$("chooseBtn").addEventListener("click", event => { event.stopPropagation(); openPicker(); });
$("heroUploadBtn").addEventListener("click", () => { $("upload").scrollIntoView({ behavior: "smooth" }); openPicker(); });
$("topUploadBtn").addEventListener("click", () => { $("upload").scrollIntoView({ behavior: "smooth" }); openPicker(); });
pdfInput.addEventListener("change", () => upload(pdfInput.files[0]));
$("generateBtn").addEventListener("click", generate);
$("previewBtn").addEventListener("click", browserPreview);
$("demoBtn").addEventListener("click", showDemo);
$("nextBtn").addEventListener("click", () => { if (book && currentChapter < book.chapters.length - 1) selectChapter(currentChapter + 1); });
$("backBtn").addEventListener("click", () => { if (book && currentChapter > 0) selectChapter(currentChapter - 1); });
$("downloadBtn").addEventListener("click", event => { if ($("downloadBtn").classList.contains("disabled")) event.preventDefault(); });
dropzone.addEventListener("click", event => { if (event.target !== $("chooseBtn")) openPicker(); });
dropzone.addEventListener("keydown", event => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); openPicker(); } });
["dragenter", "dragover"].forEach(name => dropzone.addEventListener(name, event => { event.preventDefault(); dropzone.classList.add("dragover"); }));
["dragleave", "drop"].forEach(name => dropzone.addEventListener(name, event => { event.preventDefault(); dropzone.classList.remove("dragover"); }));
dropzone.addEventListener("drop", event => upload(event.dataTransfer.files?.[0]));
audio.addEventListener("error", () => { if (audio.currentSrc) setMessage("Audio could not be loaded. Try generating this chapter again."); });
window.addEventListener("beforeunload", () => { stopPolling(); if ("speechSynthesis" in window) window.speechSynthesis.cancel(); });

loadLibrary(true);
