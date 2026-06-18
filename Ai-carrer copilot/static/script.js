/**
 * AI Career Copilot — script.js
 * Frontend logic for the Gemini AI-powered career platform.
 */

// ── App State ──────────────────────────────────────────────────────────────
const state = {
  parsed:        null,   // parsed resume object from Gemini
  ats:           null,   // ATS score object
  skillGap:      null,   // skill gap result
  questions:     null,   // interview questions
  roadmap:       null,   // learning roadmap
  activeLevel:   'beginner',
  resumeContext: ''      // plain-text summary sent to chat
};

// ── DOM Refs ───────────────────────────────────────────────────────────────
const dropZone      = document.getElementById('drop-zone');
const resumeInput   = document.getElementById('resume-input');
const uploadSuccess = document.getElementById('upload-success');
const uploadLoader  = document.getElementById('upload-loader');
const hamburger     = document.getElementById('hamburger');
const navLinks      = document.getElementById('nav-links');
const analyseGapBtn = document.getElementById('analyse-gap-btn');
const roleSelect    = document.getElementById('role-select');
const downloadBtn   = document.getElementById('download-btn');
const chatInput     = document.getElementById('chat-input');
const chatSend      = document.getElementById('chat-send');
const chatMessages  = document.getElementById('chat-messages');

// ── Navbar hamburger ───────────────────────────────────────────────────────
hamburger.addEventListener('click', () => navLinks.classList.toggle('open'));
document.querySelectorAll('.nav-links a').forEach(a =>
  a.addEventListener('click', () => navLinks.classList.remove('open'))
);

// ── Scroll: darken navbar ──────────────────────────────────────────────────
window.addEventListener('scroll', () => {
  document.getElementById('navbar').style.borderBottomColor =
    window.scrollY > 10 ? 'rgba(99,179,255,0.22)' : 'rgba(99,179,255,0.12)';
});

// ── Drag & Drop ────────────────────────────────────────────────────────────
dropZone.addEventListener('dragover',  e => { e.preventDefault(); dropZone.classList.add('dragover'); });
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
dropZone.addEventListener('drop', e => {
  e.preventDefault();
  dropZone.classList.remove('dragover');
  const file = e.dataTransfer.files[0];
  if (file) handleFileUpload(file);
});
dropZone.addEventListener('click', e => {
  if (!e.target.classList.contains('upload-btn')) resumeInput.click();
});
resumeInput.addEventListener('change', e => {
  if (e.target.files[0]) handleFileUpload(e.target.files[0]);
});

// ── Upload & Full Analysis Pipeline ───────────────────────────────────────
async function handleFileUpload(file) {
  if (!file.name.toLowerCase().endsWith('.pdf')) {
    showToast('Only PDF files are supported.', 'error');
    return;
  }

  uploadLoader.classList.remove('hidden');
  uploadSuccess.classList.add('hidden');
  setLoaderText('Gemini AI is reading your resume…');

  const formData = new FormData();
  formData.append('resume', file);

  try {
    const res  = await fetch('/upload', { method: 'POST', body: formData });
    const data = await res.json();

    if (!res.ok || data.error) throw new Error(data.error || 'Upload failed');

    state.parsed = data.parsed;
    state.ats    = data.ats;

    // Build resume context string for the chatbot
    state.resumeContext = buildResumeContext(data.parsed, data.ats);

    uploadSuccess.classList.remove('hidden');
    

    // Render all static sections immediately
    renderParsedSection();
    renderDashboard();

    // Reveal sections
    ['parsed-section', 'dashboard', 'skill-gap-section',
     'interview-section', 'roadmap-section', 'download-section']
      .forEach(showSection);

    // Run AI-powered async features
    setLoaderText('Analysing skill gap…');
    await runSkillGap();

    setLoaderText('Generating interview questions with AI…');
    await runInterviewQuestions();

    setLoaderText('Building your personalised roadmap…');
    await runRoadmap();

  } catch (err) {
    showToast('Error: ' + err.message, 'error');
  } finally {
    uploadLoader.classList.add('hidden');
  }
}

function showSection(id) {
  document.getElementById(id)?.classList.remove('hidden');
}

function setLoaderText(text) {
  const p = uploadLoader.querySelector('p');
  if (p) p.textContent = text;
}

function buildResumeContext(parsed, ats) {
  return `
Name: ${parsed.name || 'Unknown'}
Skills: ${(parsed.skills || []).join(', ') || 'None listed'}
Education: ${(parsed.education || []).join(' | ') || 'Not found'}
Experience: ${(parsed.experience || []).join(' | ') || 'Not found'}
ATS Score: ${ats?.score ?? 'N/A'}/100
ATS Summary: ${ats?.summary ?? ''}
  `.trim();
}

// ── Render: Parsed Resume Cards ────────────────────────────────────────────
function renderParsedSection() {
  const { parsed } = state;
  const grid = document.getElementById('parsed-cards');
  grid.innerHTML = '';

  // Basic info cards
  [
    { label: 'Name',     value: parsed.name     || 'Not found', mono: false },
    { label: 'Email',    value: parsed.email    || 'Not found', mono: true  },
    { label: 'Phone',    value: parsed.phone    || 'Not found', mono: true  },
    { label: 'GitHub',   value: parsed.github   || 'Not found', mono: true  },
    { label: 'LinkedIn', value: parsed.linkedin || 'Not found', mono: true  },
  ].forEach(f => {
    const card = document.createElement('div');
    card.className = 'info-card';
    card.innerHTML = `
      <div class="info-card-label">${f.label}</div>
      <div class="info-card-value ${f.mono ? 'mono' : ''}">${esc(f.value)}</div>`;
    grid.appendChild(card);
  });

  // Skills tags (spans 2 columns)
  if (parsed.skills?.length) {
    const card = document.createElement('div');
    card.className = 'info-card';
    card.style.gridColumn = 'span 2';
    card.innerHTML = `
      <div class="info-card-label">Skills Detected by AI (${parsed.skills.length})</div>
      <div class="info-card-value">
        ${parsed.skills.map(s => `<span class="info-tag">${esc(s)}</span>`).join('')}
      </div>`;
    grid.appendChild(card);
  }

  // List cards
  [
    { label: 'Education',       items: parsed.education      },
    { label: 'Work Experience', items: parsed.experience     },
    { label: 'Projects',        items: parsed.projects       },
    { label: 'Certifications',  items: parsed.certifications },
  ].forEach(({ label, items }) => {
    if (!items?.length) return;
    const card = document.createElement('div');
    card.className = 'info-card';
    card.innerHTML = `
      <div class="info-card-label">${label}</div>
      <div class="info-card-value">
        ${items.map(s => `<div class="list-item">• ${esc(s)}</div>`).join('')}
      </div>`;
    grid.appendChild(card);
  });
}

// ── Render: Dashboard ──────────────────────────────────────────────────────
function renderDashboard() {
  const { ats } = state;
  const score = ats.score;

  // SVG gradient
  const svg = document.querySelector('.ats-ring');
  if (!svg.querySelector('defs')) {
    const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
    defs.innerHTML = `
      <linearGradient id="ring-gradient" x1="0%" y1="0%" x2="100%" y2="0%">
        <stop offset="0%" stop-color="#5b8fff"/>
        <stop offset="100%" stop-color="#a78bfa"/>
      </linearGradient>`;
    svg.prepend(defs);
  }

  // Animate ring
  const circumference = 2 * Math.PI * 52;
  const ringFill = document.getElementById('ring-fill');
  ringFill.style.strokeDasharray  = circumference;
  ringFill.style.strokeDashoffset = circumference;
  ringFill.setAttribute('stroke', 'url(#ring-gradient)');
  requestAnimationFrame(() => setTimeout(() => {
    ringFill.style.strokeDashoffset = circumference * (1 - score / 100);
  }, 100));

  // Animate number counter
  const numEl = document.getElementById('ats-number');
  let cur = 0;
  const step = score / 60;
  const iv = setInterval(() => {
    cur = Math.min(cur + step, score);
    numEl.textContent = Math.round(cur);
    if (cur >= score) clearInterval(iv);
  }, 16);

  // ATS list
  document.getElementById('ats-lists').innerHTML = [
    ...ats.strengths.map(s    => `<div class="ats-item pass">✓ ${esc(s)}</div>`),
    ...ats.improvements.map(s => `<div class="ats-item fail">✗ ${esc(s)}</div>`)
  ].join('');

  // ATS summary box
  if (ats.summary) {
    const summaryEl = document.getElementById('ats-summary');
    if (summaryEl) summaryEl.textContent = ats.summary;
  }

  // Strength label
  const label = score >= 80 ? 'Strong 💪' : score >= 60 ? 'Good ✅' :
                score >= 40 ? 'Fair 🔶'   : 'Needs Work ⚠️';
  document.getElementById('metric-strength').textContent = label;
  document.getElementById('metric-role').textContent     = roleSelect.value;
  document.getElementById('metric-missing').textContent  = '…';
  document.getElementById('metric-skill').textContent    = '…';
}

// ── Skill Gap ──────────────────────────────────────────────────────────────
async function runSkillGap(role) {
  role = role || roleSelect.value;
  const skills = state.parsed?.skills || [];

  const res  = await fetch('/skill-gap', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ skills, role })
  });
  state.skillGap = await res.json();
  renderSkillGap(state.skillGap);

  document.getElementById('metric-skill').textContent   = state.skillGap.match_percentage + '%';
  document.getElementById('metric-missing').textContent = state.skillGap.missing.length;
  document.getElementById('metric-role').textContent    = role;
}

function renderSkillGap(data) {
  document.getElementById('skill-gap-results').classList.remove('hidden');

  const fill = document.getElementById('match-fill');
  const pct  = document.getElementById('match-pct');
  fill.style.width    = data.match_percentage + '%';
  pct.textContent     = data.match_percentage + '%';

  document.getElementById('skills-found').innerHTML =
    data.found.length
      ? data.found.map(s => `<span class="skill-tag">${esc(s)}</span>`).join('')
      : '<span class="empty-note">No matching skills found yet.</span>';

  document.getElementById('skills-missing').innerHTML =
    data.missing.length
      ? data.missing.map(s => `<span class="skill-tag">${esc(s)}</span>`).join('')
      : '<span class="empty-note" style="color:var(--green)">You have all required skills! 🎉</span>';

  // Show Gemini verdict
  const verdictEl = document.getElementById('gap-verdict');
  if (verdictEl && data.verdict) verdictEl.textContent = '🤖 ' + data.verdict;
}

analyseGapBtn.addEventListener('click', async () => {
  if (!state.parsed) { showToast('Please upload your resume first.', 'error'); return; }
  analyseGapBtn.textContent = 'Analysing…';
  analyseGapBtn.disabled = true;
  await runSkillGap(roleSelect.value);
  await runRoadmap(roleSelect.value);
  analyseGapBtn.textContent = 'Analyse Gap';
  analyseGapBtn.disabled = false;
});

// ── Interview Questions ────────────────────────────────────────────────────
async function runInterviewQuestions() {
  const res = await fetch('/interview-questions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ skills: state.parsed?.skills || [], role: roleSelect.value })
  });
  state.questions = await res.json();
  renderQuestions(state.activeLevel);
}

function renderQuestions(level) {
  state.activeLevel = level;
  const qs   = state.questions?.[level] || [];
  const list = document.getElementById('questions-list');
  list.innerHTML = qs.length
    ? qs.map((q, i) => `
        <div class="question-card" style="animation-delay:${i * 0.05}s">
          <div class="q-num">Q${String(i + 1).padStart(2, '0')}</div>
          <div class="q-text">${esc(q)}</div>
        </div>`).join('')
    : '<p class="empty-note">No questions available.</p>';
}

document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    renderQuestions(btn.dataset.level);
  });
});

// ── Roadmap ────────────────────────────────────────────────────────────────
async function runRoadmap(role) {
  role = role || roleSelect.value;
  const res = await fetch('/roadmap', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      role,
      missing_skills: state.skillGap?.missing  || [],
      current_skills: state.parsed?.skills     || []
    })
  });
  state.roadmap = await res.json();
  renderRoadmap(state.roadmap);
}

function renderRoadmap(steps) {
  document.getElementById('roadmap-timeline').innerHTML = steps.map((step, i) => `
    <div class="roadmap-step" style="animation-delay:${i * 0.07}s">
      <div class="roadmap-dot">${step.week === 0 ? '★' : `W${step.week}`}</div>
      <div class="roadmap-content">
        <div class="roadmap-week">${step.week === 0 ? 'Priority' : `Week ${step.week}`}</div>
        <div class="roadmap-title">${esc(step.title)}</div>
        <div class="roadmap-tasks">
          ${(step.tasks || []).map(t => `<div class="roadmap-task">${esc(t)}</div>`).join('')}
        </div>
      </div>
    </div>`).join('');
}

// ── Download Report ────────────────────────────────────────────────────────
downloadBtn.addEventListener('click', async () => {
  if (!state.parsed) { showToast('Upload a resume first.', 'error'); return; }
  try {
    const res = await fetch('/download-report', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        parsed:    state.parsed,
        ats:       state.ats,
        skill_gap: state.skillGap  || {},
        questions: state.questions || {},
        roadmap:   state.roadmap   || []
      })
    });
    if (!res.ok) throw new Error('Download failed');
    const blob = await res.blob();
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href     = url;
    a.download = 'career_report.txt';
    a.click();
    URL.revokeObjectURL(url);
  } catch (err) {
    showToast('Download error: ' + err.message, 'error');
  }
});

// ── AI Chat ────────────────────────────────────────────────────────────────
async function sendChat(text) {
  text = text.trim();
  if (!text) return;
  appendMsg(text, 'user');
  chatInput.value = '';

  // Typing indicator
  const typingId = appendTyping();

  try {
    const res  = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text, resume_context: state.resumeContext })
    });
    const data = await res.json();
    removeTyping(typingId);
    appendMsg(data.response, 'bot');
  } catch {
    removeTyping(typingId);
    appendMsg('Sorry, something went wrong. Please try again.', 'bot');
  }
}

function appendMsg(text, role) {
  const div = document.createElement('div');
  div.className = `chat-msg ${role}`;
  div.innerHTML = `
    <div class="chat-avatar">${role === 'bot' ? '◈' : 'ME'}</div>
    <div class="chat-bubble">${esc(text)}</div>`;
  chatMessages.appendChild(div);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function appendTyping() {
  const id  = 'typing-' + Date.now();
  const div = document.createElement('div');
  div.id        = id;
  div.className = 'chat-msg bot';
  div.innerHTML = `
    <div class="chat-avatar">◈</div>
    <div class="chat-bubble typing-bubble">
      <span></span><span></span><span></span>
    </div>`;
  chatMessages.appendChild(div);
  chatMessages.scrollTop = chatMessages.scrollHeight;
  return id;
}

function removeTyping(id) {
  document.getElementById(id)?.remove();
}

chatSend.addEventListener('click', () => sendChat(chatInput.value));
chatInput.addEventListener('keydown', e => { if (e.key === 'Enter') sendChat(chatInput.value); });
document.querySelectorAll('.quick-prompt').forEach(btn => {
  btn.addEventListener('click', () => sendChat(btn.dataset.prompt));
});

// ── Toast Notifications ────────────────────────────────────────────────────
function showToast(message, type = 'info') {
  const t = document.createElement('div');
  t.className = `toast toast-${type}`;
  t.textContent = message;
  document.body.appendChild(t);
  setTimeout(() => t.classList.add('toast-show'), 10);
  setTimeout(() => { t.classList.remove('toast-show'); setTimeout(() => t.remove(), 400); }, 3500);
}

// ── Helpers ────────────────────────────────────────────────────────────────
function esc(str) {
  return String(str)
    .replace(/&/g,'&amp;').replace(/</g,'&lt;')
    .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}