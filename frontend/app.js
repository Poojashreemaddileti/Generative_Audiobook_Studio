const $ = (id) => document.getElementById(id);
let book = null;
let currentChapter = 0;
let pollTimer = null;

const pdfInput = $("pdfInput");
const dropzone = $("dropzone");
const audio = $("audio");

function setStatus(text) { $("status").textContent = text; }
function setMessage(text) { $("playerMessage").textContent = text; }

function renderLibrary(books) {
  const box = $("libraryFiles");
  box.innerHTML = "";
  if (!books.length) return;
  books.forEach(item => {
    const el = document.createElement("button");
    el.className = "file-chip" + (book && book.id === item.id ? " active" : "");
    el.innerHTML = `<span>PDF</span><span>${escapeHtml(item.title)}</span><small>${item.chapter_count} ch</small>`;
    el.onclick = () => loadBook(item.id);
    box.appendChild(el);
  });
}

async function loadLibrary() {
  try {
    const res = await fetch("/api/library");
    const data = await res.json();
    renderLibrary(data.books || []);
  } catch (_) {}
}

async function loadBook(id) {
  const res = await fetch(`/api/books/${id}`);
  const data = await res.json();
  if (!res.ok) { setMessage(data.error || "Could not open the book."); return; }
  currentChapter = 0;
  renderBook(data);
  document.querySelector("#library").scrollIntoView({behavior:"smooth"});
}

function renderBook(data) {
  book = data;
  $("bookTitle").textContent = data.title;
  $("wordCount").textContent = Number(data.word_count || 0).toLocaleString();
  $("chapterCount").textContent = data.chapter_count || 0;
  $("chapterHint").textContent = `${data.chapter_count || 0} total`;
  $("deviceName").textContent = data.tts?.device || "CPU / on demand";
  $("modelName").textContent = data.tts?.model?.includes("female") ? "Female MMS" : "MMS VITS";
  setStatus(data.status === "generated" ? "Audio available" : "PDF processed · ready");
  renderLibraryCurrent();

  const list = $("chapterList");
  list.innerHTML = "";
  data.chapters.forEach((ch, i) => {
    const el = document.createElement("div");
    el.className = "chapter" + (i === currentChapter ? " active" : "");
    const ready = !!ch.audio;
    const state = ready ? " · ready" : ch.status === "generating" ? " · generating" : "";
    el.innerHTML = `<div class="chapter-row"><button class="chapter-play" title="${ready ? "Play chapter" : "Generate chapter"}"><span>${ready ? "▶" : "＋"}</span></button><div class="chapter-title">${escapeHtml(ch.title)}</div></div><div class="chapter-meta">${Number(ch.characters || 0).toLocaleString()} characters${ch.duration ? " · " + formatTime(ch.duration) : ""}${state}</div>`;
    el.onclick = () => selectChapter(i);
    el.querySelector(".chapter-play").onclick = (e) => { e.stopPropagation(); if (ready) playChapter(i); else { selectChapter(i); generate(); } };
    list.appendChild(el);
  });
  if (data.chapters.length) selectChapter(Math.min(currentChapter, data.chapters.length - 1));
}

function renderLibraryCurrent() {
  document.querySelectorAll(".file-chip").forEach((x) => x.classList.remove("active"));
}

function selectChapter(index) {
  if (!book || !book.chapters[index]) return;
  currentChapter = index;
  const ch = book.chapters[index];
  $("nowTitle").textContent = ch.title;
  $("nowPreview").textContent = ch.preview || "Ready to generate.";
  $("generateBtn").textContent = ch.audio ? "Regenerate chapter" : "Generate this chapter";
  $("generateBtn").disabled = false;
  document.querySelectorAll(".chapter").forEach((x, i) => x.classList.toggle("active", i === index));
  if (ch.audio) {
    audio.src = ch.audio + `?t=${Date.now()}`;
    $("downloadBtn").href = ch.audio;
    $("downloadBtn").classList.remove("disabled");
    setMessage("Chapter audio is ready. Click the chapter card or press play.");
  } else {
    audio.removeAttribute("src"); audio.load();
    $("downloadBtn").classList.add("disabled");
    setMessage("Generate this chapter to create the female neural narration, then play it from this card.");
  }
}

function playChapter(index) {
  selectChapter(index);
  if (book.chapters[index]?.audio) audio.play().catch(() => setMessage("Press play in the audio player to start playback."));
}

async function upload(file) {
  if (!file) return;
  if (!file.name.toLowerCase().endsWith(".pdf")) { setMessage("Please choose a PDF file."); return; }
  setStatus("Reading PDF…"); $("uploadStatus").textContent = "Extracting text and saving to database…";
  const fd = new FormData(); fd.append("pdf", file);
  try {
    const res = await fetch("/api/books", {method:"POST", body:fd});
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Upload failed");
    currentChapter = 0; renderBook(data); await loadLibrary();
    setStatus("PDF stored · chapters ready"); $("uploadStatus").textContent = `${data.chapter_count} chapter${data.chapter_count === 1 ? "" : "s"} found · saved`;
    document.querySelector("#library").scrollIntoView({behavior:"smooth"});
  } catch (e) {
    setStatus("Upload error"); $("uploadStatus").textContent = "Could not read PDF"; setMessage(e.message);
  }
}

async function generate() {
  if (!book) { setMessage("Upload a PDF first."); return; }
  const chapter = book.chapters[currentChapter];
  if (!chapter) return;
  $("generateBtn").disabled = true;
  $("progressWrap").hidden = false;
  $("progressBar").style.width = "2%";
  $("progressPercent").textContent = "0%";
  $("progressMessage").textContent = "Starting…";
  setStatus("Generating female voice…");
  setMessage("The first neural generation can take a few minutes on CPU. Keep this window open.");
  try {
    const res = await fetch(`/api/books/${book.id}/generate`, {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({chapter: currentChapter})});
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Generation failed");
    if (data.status === "already_generated") { renderBook(data.book); return; }
    pollJob(data.job_id);
  } catch (e) {
    setStatus("Generation error"); setMessage(e.message); $("generateBtn").disabled = false; $("progressWrap").hidden = true;
  }
}

function pollJob(jobId) {
  clearInterval(pollTimer);
  pollTimer = setInterval(async () => {
    try {
      const res = await fetch(`/api/jobs/${jobId}`); const job = await res.json();
      if (!res.ok) throw new Error(job.error || "Could not read generation status");
      const pct = Math.max(0, Math.min(100, Number(job.progress || 0)));
      $("progressBar").style.width = `${pct}%`; $("progressPercent").textContent = `${pct}%`; $("progressMessage").textContent = job.message || "Working…";
      if (job.status === "done") {
        clearInterval(pollTimer); renderBook(job.book); $("progressWrap").hidden = true; setStatus("Chapter audio ready"); setMessage("Generated successfully. Click the chapter card or press play."); await loadLibrary();
      } else if (job.status === "error") {
        clearInterval(pollTimer); $("progressWrap").hidden = true; $("generateBtn").disabled = false; setStatus("Generation error"); setMessage(job.message || "The voice model failed.");
      }
    } catch (e) {
      clearInterval(pollTimer); $("progressWrap").hidden = true; $("generateBtn").disabled = false; setStatus("Connection error"); setMessage(e.message);
    }
  }, 1200);
}

function browserPreview() {
  if (!book) { setMessage("Upload a PDF first."); return; }
  const text = book.chapters[currentChapter]?.preview || "This is your audiobook preview.";
  if (!("speechSynthesis" in window)) { setMessage("Your browser does not support built-in speech preview."); return; }
  const speak = () => {
    const voices = speechSynthesis.getVoices();
    const preferred = voices.find(v => /female|samantha|aria|zira|jenny|susan|hazel|libby/i.test(v.name)) || voices.find(v => /^en(-|_)/i.test(v.lang));
    speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    if (preferred) { utterance.voice = preferred; utterance.lang = preferred.lang; }
    utterance.rate = 0.91; utterance.pitch = 1.05;
    speechSynthesis.speak(utterance);
    setMessage(`Browser preview is using ${preferred ? preferred.name : "the browser's English voice"}. Neural generation uses the selected female-speaker model.`);
  };
  if (speechSynthesis.getVoices().length) speak(); else { speechSynthesis.onvoiceschanged = speak; speechSynthesis.getVoices(); }
}

function formatTime(sec) { sec = Math.round(sec || 0); return `${Math.floor(sec/60)}:${String(sec%60).padStart(2,"0")}`; }
function escapeHtml(s) { return String(s).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c])); }

$("chooseBtn").onclick = () => pdfInput.click(); $("heroUploadBtn").onclick = () => pdfInput.click(); $("topUploadBtn").onclick = () => pdfInput.click(); pdfInput.onchange = () => upload(pdfInput.files[0]);
$("generateBtn").onclick = generate; $("previewBtn").onclick = browserPreview;
$("nextBtn").onclick = () => { if (book && currentChapter < book.chapters.length - 1) selectChapter(currentChapter + 1); };
$("backBtn").onclick = () => { if (book && currentChapter > 0) selectChapter(currentChapter - 1); };

$("demoBtn").onclick = () => {
  book = {id:"demo", title:"The Quiet Machine", status:"ready", word_count:128, chapter_count:1, chapters:[{index:0,title:"Chapter 1 · A Quiet Beginning",characters:720,preview:"A short browser demo. The real project uses the female neural voice model when you generate audio.",audio:null,status:"ready"}]};
  currentChapter = 0; renderBook(book); setStatus("Demo loaded · no server generation needed"); $("uploadStatus").textContent = "Demo ready"; document.querySelector("#library").scrollIntoView({behavior:"smooth"});
};

["dragenter","dragover"].forEach(ev => dropzone.addEventListener(ev, e => { e.preventDefault(); dropzone.classList.add("dragging"); }));
["dragleave","drop"].forEach(ev => dropzone.addEventListener(ev, e => { e.preventDefault(); dropzone.classList.remove("dragging"); }));
dropzone.addEventListener("drop", e => upload(e.dataTransfer.files[0]));
loadLibrary();
