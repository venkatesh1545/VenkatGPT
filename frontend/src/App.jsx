import { useState, useRef, useEffect, useCallback } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
const THREADS_KEY = "vgpt_threads_v2";
const ACTIVE_KEY = "vgpt_active_v2";

/* ═══ UTILS ════════════════════════════════════════════════════════════ */
const genId = () => Date.now().toString(36) + Math.random().toString(36).slice(2);
const now = () => Date.now();
const fmtTime = (t) => {
  const d = new Date(t), today = new Date();
  if (d.toDateString() === today.toDateString())
    return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  const y = new Date(today); y.setDate(y.getDate() - 1);
  if (d.toDateString() === y.toDateString()) return "Yesterday";
  return d.toLocaleDateString([], { month: "short", day: "numeric" });
};

/* ═══ JOURNEY MAP ══════════════════════════════════════════════════════ */
const JOURNEY = [
  {
    icon: "👋", label: "Who is Venkat?",
    q: "Tell me about yourself — who are you, what do you build, and what makes you stand out as an engineer?"
  },
  {
    icon: "🚀", label: "Top Projects",
    q: "Walk me through your top 3 flagship projects — DroneX, XpressPrints, and VenkatGPT — with tech stack, impact, and links."
  },
  {
    icon: "🛠️", label: "Tech Stack",
    q: "What is your complete technical skill set, broken down by AI/ML, backend, frontend, cloud, and DevOps?"
  },
  {
    icon: "🏆", label: "Achievements",
    q: "What are your biggest achievements — Adobe Top 30 India, AP Government SEED project, Amdocs Top 50, and XpressPrints revenue?"
  },
  {
    icon: "📜", label: "Certifications",
    q: "List all your certifications — AWS, RHCSA, GitHub Admin, ServiceNow — with issuer, year, and verification links."
  },
  {
    icon: "💻", label: "Coding Profiles",
    q: "Share your competitive programming profiles — LeetCode, GeeksForGeeks, CodeChef, Codeforces — with usernames, ratings, and links."
  },
  {
    icon: "📄", label: "View Resume",
    q: "Share your resume — I'd like to view or download it."
  },
  {
    icon: "🤝", label: "Get in Touch",
    q: "How can I contact Venkat? Share all links — LinkedIn, GitHub, email, and portfolio website."
  },
];

/* ═══ SMART FOLLOW-UP ENGINE ═══════════════════════════════════════════
   Rules (in priority order):
   1. If a SPECIFIC project is mentioned → project-specific follow-ups WITH name
   2. If it's a general "about yourself" / intro question → rotate across ALL highlights
   3. Topic-based fallbacks (certs, skills, etc.)
════════════════════════════════════════════════════════════════════════ */
const PROJECTS = [
  { name: "DroneX", keys: ["dronex", "ravnresq", "disaster", "drone", "ap government", "rescue", "geolocation"] },
  { name: "XpressPrints", keys: ["xpressprints", "printing", "marketplace", "phonePe", "print store", "docx counting"] },
  { name: "VenkatGPT", keys: ["venkatgpt", "rag pipeline", "persona", "faiss", "identity engine", "this system", "this application"] },
  { name: "CURVETOPIA", keys: ["curvetopia", "adobe", "curve", "shape classification", "gensolve", "symmetry"] },
  { name: "ElevateEd", keys: ["elevateed", "amdocs", "learning platform", "elevate", "edtech", "huggingface"] },
  { name: "Expenses Tracker", keys: ["expenses", "tracker", "finance", "lambda finance", "dynamodb finance"] },
  { name: "Inventory AI Agents", keys: ["inventory", "ai agents", "stock", "reorder"] },
];

const INTRO_KEYWORDS = ["yourself", "who are you", "about you", "introduce", "overview", "tell me about", "what do you do", "what makes you"];

function detectProject(text) {
  const t = text.toLowerCase();
  for (const p of PROJECTS) {
    if (p.keys.some(k => t.includes(k))) return p.name;
  }
  return null;
}

function buildFollowUps(userQ = "", aiResp = "") {
  const combined = (userQ + " " + aiResp).toLowerCase();
  const q = userQ.toLowerCase();

  // 1. Specific project detected
  const project = detectProject(combined);
  if (project && !INTRO_KEYWORDS.some(k => q.includes(k))) {
    return [
      `Show me the complete architecture for ${project}`,
      `What was the hardest challenge building ${project}?`,
      `What tech stack powers ${project}?`,
      `Show me the GitHub or demo link for ${project}`,
      `What's next / future scope for ${project}?`,
    ];
  }

  // 2. Intro / "about yourself" → highlight ALL flagship projects
  if (INTRO_KEYWORDS.some(k => q.includes(k))) {
    return [
      "Tell me about DroneX — the AP Government disaster management project",
      "How does VenkatGPT work technically — architecture and RAG pipeline?",
      "Tell me about XpressPrints — the real printing marketplace you built",
      "What are your top achievements and hackathon rankings?",
      "Share all your links — GitHub, LinkedIn, portfolio",
    ];
  }

  // 3. Topic-based
  if (q.includes("certif")) return [
    "Which certification was hardest and why?",
    "How do certifications reflect in your real projects?",
    "What certification are you planning next?",
    "Share the AWS certification verification link",
  ];
  if (q.includes("leetcode") || q.includes("coding") || q.includes("geeks") || q.includes("codechef") || q.includes("compet")) return [
    "What DSA topics do you focus on most?",
    "What's your LeetCode problem count and ranking?",
    "How do you balance competitive coding with project work?",
    "Share your GeeksForGeeks and CodeChef profile links",
  ];
  if (q.includes("skill") || q.includes("stack") || q.includes("tech")) return [
    "How did you learn RAG and LLM engineering?",
    "Which cloud platform do you prefer — AWS vs GCP?",
    "What AI/ML tools do you use in production systems?",
    "What are you currently learning or exploring?",
  ];
  if (q.includes("achiev") || q.includes("hackathon") || q.includes("adobe") || q.includes("amdocs")) return [
    "Tell me more about the Adobe GenSolve Top 30 achievement",
    "What was it like building DroneX for the AP Government?",
    "How did the Amdocs hackathon ElevateEd project work?",
    "What other competitions have you entered?",
  ];
  if (q.includes("contact") || q.includes("reach") || q.includes("linkedin") || q.includes("github")) return [
    "What's the best way to contact for a job opportunity?",
    "Tell me about your Keywords Studios experience",
    "Are you open to remote work or relocation?",
  ];

  return [
    "Walk me through DroneX — your government SEED project",
    "What makes VenkatGPT technically impressive?",
    "Tell me about XpressPrints and its real-world validation",
    "What are you currently building or learning?",
    "Share your GitHub and LinkedIn links",
  ];
}

/* ═══ THREAD STORE ══════════════════════════════════════════════════════ */
function loadThreads() {
  try { const s = localStorage.getItem(THREADS_KEY); if (s) return JSON.parse(s); } catch { }
  return {};
}
function saveThreads(t) { try { localStorage.setItem(THREADS_KEY, JSON.stringify(t)); } catch { } }

function makeThread(title = "New conversation") {
  const id = genId();
  return {
    id, title, createdAt: now(), updatedAt: now(),
    messages: [{
      id: "init-" + id, role: "assistant", timestamp: now(),
      content: `**Hey! I'm VenkatGPT** 👋\n\nI'm the AI-powered version of **Golthi Venkatacharyulu** — a Full Stack AI Engineer.\n\nUse the journey map below to explore my work, or just ask me anything directly.`,
    }],
  };
}

/* ═══ TTS ════════════════════════════════════════════════════════════════ */
function useTTS() {
  const [speaking, setSpeaking] = useState(false);
  const ok = typeof window !== "undefined" && "speechSynthesis" in window;
  const speak = useCallback((text) => {
    if (!ok) return;
    window.speechSynthesis.cancel();
    const plain = text.replace(/#{1,6}\s/g, "").replace(/\*\*(.*?)\*\*/g, "$1")
      .replace(/\*(.*?)\*/g, "$1").replace(/`(.*?)`/g, "$1")
      .replace(/\[(.*?)\]\(.*?\)/g, "$1").replace(/\n+/g, " ").trim();
    const u = new SpeechSynthesisUtterance(plain);
    u.rate = 0.92; u.pitch = 1.05;
    u.onstart = () => setSpeaking(true);
    u.onend = u.onerror = () => setSpeaking(false);
    window.speechSynthesis.speak(u);
  }, [ok]);
  const stop = useCallback(() => { window.speechSynthesis.cancel(); setSpeaking(false); }, []);
  return { speak, stop, speaking, supported: ok };
}

/* ═══ PARTICLES ═════════════════════════════════════════════════════════ */
function ParticleField() {
  const dots = Array.from({ length: 32 }, (_, i) => ({ id: i, x: Math.random() * 100, y: Math.random() * 100, s: Math.random() * 1.3 + 0.4, d: Math.random() * 5, dur: Math.random() * 9 + 7 }));
  return (
    <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden" aria-hidden>
      <div className="absolute inset-0 opacity-[0.02]" style={{ backgroundImage: "linear-gradient(rgba(6,182,212,1) 1px,transparent 1px),linear-gradient(90deg,rgba(6,182,212,1) 1px,transparent 1px)", backgroundSize: "64px 64px" }} />
      <div className="absolute top-[-18%] left-[-8%] w-[480px] h-[480px] rounded-full" style={{ background: "radial-gradient(circle,rgba(6,182,212,0.07) 0%,transparent 70%)", animation: "orb1 23s ease-in-out infinite" }} />
      <div className="absolute bottom-[-12%] right-[-6%] w-[400px] h-[400px] rounded-full" style={{ background: "radial-gradient(circle,rgba(139,92,246,0.07) 0%,transparent 70%)", animation: "orb2 29s ease-in-out infinite" }} />
      <svg className="absolute inset-0 w-full h-full">
        {dots.map(d => (
          <circle key={d.id} cx={`${d.x}%`} cy={`${d.y}%`} r={d.s} fill="#06b6d4">
            <animate attributeName="opacity" values="0.03;0.2;0.03" dur={`${d.dur}s`} begin={`${d.d}s`} repeatCount="indefinite" />
            <animateTransform attributeName="transform" type="translate" values="0,0;3,-5;0,0" dur={`${d.dur}s`} begin={`${d.d}s`} repeatCount="indefinite" />
          </circle>
        ))}
      </svg>
    </div>
  );
}

/* ═══ SIDEBAR ═══════════════════════════════════════════════════════════ */
function Sidebar({ threads, activeId, onSelect, onNew, onDelete, onRename, isOpen, onClose, onResumeOpen }) {
  const [editId, setEditId] = useState(null);
  const [editVal, setEditVal] = useState("");
  const editRef = useRef(null);
  useEffect(() => { if (editId && editRef.current) editRef.current.focus(); }, [editId]);

  const sorted = Object.values(threads).sort((a, b) => b.updatedAt - a.updatedAt);
  const todayStr = new Date().toDateString();
  const yesterStr = new Date(Date.now() - 86400000).toDateString();
  const groups = { Today: [], Yesterday: [], Earlier: [] };
  for (const t of sorted) {
    const d = new Date(t.updatedAt).toDateString();
    if (d === todayStr) groups.Today.push(t);
    else if (d === yesterStr) groups.Yesterday.push(t);
    else groups.Earlier.push(t);
  }

  const confirmRename = (id) => { onRename(id, editVal.trim() || threads[id]?.title); setEditId(null); };

  return (
    <>
      {isOpen && <div className="fixed inset-0 z-20 lg:hidden" onClick={onClose} style={{ background: "rgba(0,0,0,0.7)", backdropFilter: "blur(4px)" }} />}
      <aside className={`fixed left-0 top-0 h-full z-30 flex flex-col transition-transform duration-300 ease-out ${isOpen ? "translate-x-0" : "-translate-x-full"}`}
        style={{ width: 268, background: "rgba(4,9,22,0.98)", borderRight: "1px solid rgba(6,182,212,0.09)", backdropFilter: "blur(24px)" }}>
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-4 flex-shrink-0" style={{ borderBottom: "1px solid rgba(6,182,212,0.08)" }}>
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl flex items-center justify-center text-xs font-bold text-black" style={{ background: "linear-gradient(135deg,#06b6d4,#8b5cf6)", boxShadow: "0 0 16px rgba(6,182,212,0.4)" }}>V</div>
            <div>
              <p className="text-sm font-semibold text-white" style={{ fontFamily: "'DM Mono',monospace" }}>VenkatGPT</p>
              <p className="text-xs text-gray-600">Conversations</p>
            </div>
          </div>
          <button onClick={onClose} className="w-7 h-7 flex items-center justify-center rounded-lg text-gray-500 hover:text-gray-200 transition-colors text-lg">×</button>
        </div>
        {/* New chat + Resume buttons */}
        <div className="px-3 py-3 flex-shrink-0 space-y-2">
          <button onClick={() => { onNew(); onClose(); }}
            className="w-full flex items-center gap-2 px-3 py-2.5 rounded-xl text-sm font-medium transition-all"
            style={{ background: "rgba(6,182,212,0.07)", border: "1px solid rgba(6,182,212,0.14)", color: "#67e8f9" }}
            onMouseEnter={e => e.currentTarget.style.background = "rgba(6,182,212,0.14)"}
            onMouseLeave={e => e.currentTarget.style.background = "rgba(6,182,212,0.07)"}>
            <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" /></svg>
            New conversation
          </button>
          <button onClick={() => { onResumeOpen(); onClose(); }}
            className="w-full flex items-center gap-2 px-3 py-2.5 rounded-xl text-sm font-medium transition-all"
            style={{ background: "rgba(139,92,246,0.07)", border: "1px solid rgba(139,92,246,0.14)", color: "#c4b5fd" }}
            onMouseEnter={e => e.currentTarget.style.background = "rgba(139,92,246,0.14)"}
            onMouseLeave={e => e.currentTarget.style.background = "rgba(139,92,246,0.07)"}>
            <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
            View Resume
          </button>
        </div>
        {/* Threads */}
        <div className="flex-1 overflow-y-auto px-2 pb-4">
          {sorted.length === 0 && <p className="text-xs text-gray-600 text-center mt-8 px-4 leading-relaxed">No conversations yet.<br />Start chatting!</p>}
          {Object.entries(groups).map(([label, items]) => items.length === 0 ? null : (
            <div key={label} className="mb-3">
              <p className="text-xs text-gray-600 px-3 py-1.5 font-medium tracking-wide uppercase">{label}</p>
              {items.map(t => (
                <div key={t.id} className="group relative mb-0.5">
                  {editId === t.id ? (
                    <div className="px-2 py-1">
                      <input ref={editRef} value={editVal} onChange={e => setEditVal(e.target.value)}
                        onBlur={() => confirmRename(t.id)}
                        onKeyDown={e => { if (e.key === "Enter") confirmRename(t.id); if (e.key === "Escape") setEditId(null); }}
                        className="w-full px-3 py-2 rounded-xl text-xs text-white outline-none" style={{ background: "rgba(6,182,212,0.1)", border: "1px solid rgba(6,182,212,0.3)" }} />
                    </div>
                  ) : (
                    <button onClick={() => { onSelect(t.id); onClose(); }}
                      className="w-full text-left px-3 py-2.5 rounded-xl transition-all"
                      style={{ background: activeId === t.id ? "rgba(6,182,212,0.1)" : "transparent", border: activeId === t.id ? "1px solid rgba(6,182,212,0.14)" : "1px solid transparent" }}
                      onMouseEnter={e => { if (activeId !== t.id) e.currentTarget.style.background = "rgba(255,255,255,0.03)"; }}
                      onMouseLeave={e => { if (activeId !== t.id) e.currentTarget.style.background = "transparent"; }}>
                      <div className="flex items-start gap-2 pr-14">
                        <svg className="w-3.5 h-3.5 text-gray-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" /></svg>
                        <div className="flex-1 min-w-0">
                          <p className="text-xs text-gray-200 truncate font-medium">{t.title}</p>
                          <p className="text-xs text-gray-600 mt-0.5">{fmtTime(t.updatedAt)} · {Math.max(0, t.messages.length - 1)} msgs</p>
                        </div>
                      </div>
                    </button>
                  )}
                  <div className="absolute right-2 top-1/2 -translate-y-1/2 hidden group-hover:flex items-center gap-0.5" style={{ background: "rgba(4,9,22,0.95)", borderRadius: 8, padding: "2px 4px" }}>
                    <button title="Rename" onClick={e => { e.stopPropagation(); setEditVal(t.title); setEditId(t.id); }} className="p-1.5 rounded-lg text-gray-500 hover:text-cyan-400 transition-colors">
                      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" /></svg>
                    </button>
                    <button title="Delete" onClick={e => { e.stopPropagation(); if (confirm("Delete this conversation?")) onDelete(t.id); }} className="p-1.5 rounded-lg text-gray-500 hover:text-red-400 transition-colors">
                      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ))}
        </div>
        <div className="px-4 py-3 flex-shrink-0" style={{ borderTop: "1px solid rgba(6,182,212,0.07)" }}>
          <p className="text-xs text-gray-700 text-center font-mono">Saved locally · Private · No cloud</p>
        </div>
      </aside>
    </>
  );
}

/* ═══ RESUME MODAL ══════════════════════════════════════════════════════ */
function ResumeModal({ onClose }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4" onClick={onClose}>
      <div className="absolute inset-0 bg-black/85 backdrop-blur-md" />
      <div className="relative z-10 w-full max-w-4xl h-[92vh] rounded-2xl overflow-hidden flex flex-col"
        style={{ border: "1px solid rgba(6,182,212,0.22)", boxShadow: "0 0 80px rgba(6,182,212,0.12)" }}
        onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between px-4 sm:px-5 py-3 flex-shrink-0"
          style={{ background: "rgba(2,8,23,0.99)", borderBottom: "1px solid rgba(6,182,212,0.12)" }}>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
            <span className="text-xs sm:text-sm font-mono text-cyan-300 tracking-wider uppercase">Resume Preview</span>
          </div>
          <div className="flex gap-2">
            <a href={`${API_URL}/api/v1/resume/download`} target="_blank" rel="noopener noreferrer"
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-mono transition-all"
              style={{ background: "rgba(6,182,212,0.1)", color: "#06b6d4", border: "1px solid rgba(6,182,212,0.22)" }}>
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>
              <span className="hidden sm:inline">Download</span> PDF
            </a>
            <button onClick={onClose} className="px-3 py-1.5 rounded-lg text-xs text-gray-400 hover:text-white transition-colors" style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.07)" }}>
              ✕
            </button>
          </div>
        </div>
        <iframe src={`${API_URL}/api/v1/resume/view#toolbar=1&navpanes=0`} className="flex-1 w-full" style={{ background: "#0a0a0a" }} title="Resume" />
      </div>
    </div>
  );
}

/* ═══ ACTION BAR — always visible on mobile, hover on desktop ══════════ */
function ActionBar({ msg, onSuggest, tts, isMobile }) {
  const [copied, setCopied] = useState(false);
  const copy = () => { navigator.clipboard.writeText(msg.content); setCopied(true); setTimeout(() => setCopied(false), 1500); };

  return (
    <div className={`flex items-center gap-1.5 mt-3 pt-2.5 transition-opacity duration-200 ${isMobile ? "opacity-100" : "opacity-0 group-hover:opacity-100"}`}
      style={{ borderTop: "1px solid rgba(6,182,212,0.07)" }}>
      <button onClick={copy} className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs transition-colors" style={{ background: "rgba(6,182,212,0.05)", color: copied ? "#06b6d4" : "#6b7280" }}>
        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>
        {copied ? "Copied" : "Copy"}
      </button>
      {tts.supported && (
        <button onClick={() => tts.speaking ? tts.stop() : tts.speak(msg.content)}
          className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs transition-colors"
          style={{ background: tts.speaking ? "rgba(6,182,212,0.14)" : "rgba(6,182,212,0.05)", color: tts.speaking ? "#06b6d4" : "#6b7280" }}>
          {tts.speaking
            ? <><svg className="w-3 h-3" fill="currentColor" viewBox="0 0 24 24"><rect x="6" y="4" width="4" height="16" /><rect x="14" y="4" width="4" height="16" /></svg>Stop</>
            : <><svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.536 8.464a5 5 0 010 7.072M17.95 6.05a8 8 0 010 11.9M6.5 8.5l4.5-3v13l-4.5-3H3a1 1 0 01-1-1v-5a1 1 0 011-1h3.5z" /></svg>Listen</>
          }
        </button>
      )}
      <button onClick={onSuggest} className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs transition-colors ml-auto" style={{ background: "rgba(139,92,246,0.05)", color: "#8b5cf6" }}>
        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" /></svg>
        Follow-ups
      </button>
    </div>
  );
}

/* ═══ MESSAGE ════════════════════════════════════════════════════════════ */
function Message({ msg, onSuggest, tts, isMobile }) {
  const isUser = msg.role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} group`}
      style={{ animation: "msgIn 0.28s cubic-bezier(0.34,1.56,0.64,1) both" }}>
      {!isUser && (
        <div className="w-8 h-8 sm:w-9 sm:h-9 rounded-xl flex-shrink-0 mr-2 sm:mr-3 mt-0.5 flex items-center justify-center text-xs font-bold text-black"
          style={{ background: "linear-gradient(135deg,#06b6d4,#8b5cf6)", boxShadow: "0 0 20px rgba(6,182,212,0.35)" }}>V</div>
      )}
      <div className={`flex flex-col gap-1 ${isUser ? "items-end" : "items-start"} max-w-[88%] sm:max-w-[84%]`}>
        {isUser ? (
          <div className="px-4 py-3 rounded-2xl rounded-tr-sm text-sm leading-relaxed text-white"
            style={{ background: "linear-gradient(135deg,rgba(8,145,178,0.88),rgba(124,58,237,0.88))", boxShadow: "0 4px 20px rgba(8,145,178,0.22)" }}>
            {msg.content}
          </div>
        ) : (
          <div className="px-4 sm:px-5 py-3.5 sm:py-4 rounded-2xl rounded-tl-sm w-full"
            style={{ background: "rgba(11,18,36,0.92)", border: "1px solid rgba(6,182,212,0.11)", backdropFilter: "blur(14px)", boxShadow: "0 4px 30px rgba(0,0,0,0.35)" }}>
            <div className={`prose prose-invert prose-sm max-w-none ${msg.streaming ? "typing-cur" : ""}`}>
              <ReactMarkdown remarkPlugins={[remarkGfm]} components={{
                a: ({ href, children }) => (
                  <a href={href} target="_blank" rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 font-medium underline underline-offset-2 transition-colors"
                    style={{ color: "#22d3ee" }}>
                    {children}
                    <svg className="w-3 h-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" /></svg>
                  </a>
                ),
                code({ inline, children, ...p }) {
                  return inline
                    ? <code className="px-1.5 py-0.5 rounded text-cyan-300 text-xs font-mono" style={{ background: "rgba(6,182,212,0.09)" }} {...p}>{children}</code>
                    : <pre className="rounded-xl p-3 sm:p-4 overflow-x-auto my-2" style={{ background: "rgba(0,0,0,0.6)", border: "1px solid rgba(6,182,212,0.09)" }}><code className="text-emerald-300 text-xs font-mono" {...p}>{children}</code></pre>;
                },
                h1: ({ children }) => <h1 className="text-base font-bold mb-2 mt-0 leading-snug" style={{ color: "#67e8f9" }}>{children}</h1>,
                h2: ({ children }) => <h2 className="text-sm font-bold mb-1.5 mt-3 leading-snug" style={{ color: "#a5f3fc" }}>{children}</h2>,
                h3: ({ children }) => <h3 className="text-sm font-semibold mb-1 mt-2" style={{ color: "#cffafe" }}>{children}</h3>,
                strong: ({ children }) => <strong className="font-semibold" style={{ color: "#67e8f9" }}>{children}</strong>,
                p: ({ children }) => <p className="mb-2 last:mb-0 leading-relaxed" style={{ color: "#d1d5db" }}>{children}</p>,
                ul: ({ children }) => <ul className="mb-2 space-y-1 mt-1">{children}</ul>,
                ol: ({ children }) => <ol className="mb-2 space-y-1 mt-1 list-decimal list-inside">{children}</ol>,
                li: ({ children }) => <li className="flex gap-2 text-sm" style={{ color: "#d1d5db" }}><span className="flex-shrink-0 mt-0.5" style={{ color: "#06b6d4" }}>▸</span><span>{children}</span></li>,
                table: ({ children }) => <div className="overflow-x-auto my-2 rounded-xl" style={{ border: "1px solid rgba(6,182,212,0.1)" }}><table className="text-xs w-full" style={{ borderCollapse: "collapse" }}>{children}</table></div>,
                th: ({ children }) => <th className="px-3 py-2 text-left text-xs font-medium" style={{ background: "rgba(6,182,212,0.06)", borderBottom: "1px solid rgba(6,182,212,0.12)", color: "#67e8f9" }}>{children}</th>,
                td: ({ children }) => <td className="px-3 py-2 text-xs" style={{ borderBottom: "1px solid rgba(255,255,255,0.03)", color: "#d1d5db" }}>{children}</td>,
                blockquote: ({ children }) => <blockquote className="pl-3 my-2 italic" style={{ borderLeft: "2px solid rgba(6,182,212,0.3)", color: "#9ca3af" }}>{children}</blockquote>,
              }}>
                {msg.content || ""}
              </ReactMarkdown>
            </div>
            {!msg.streaming && (
              <ActionBar msg={msg} onSuggest={onSuggest} tts={tts} isMobile={isMobile} />
            )}
          </div>
        )}
        <span className="text-xs px-1" style={{ color: "#374151", opacity: isMobile ? 0.6 : undefined }} >
          {fmtTime(msg.timestamp || now())}
        </span>
      </div>
    </div>
  );
}

/* ═══ MAIN APP ══════════════════════════════════════════════════════════ */
export default function App() {
  const [threads, setThreads] = useState(() => {
    const t = loadThreads();
    if (Object.keys(t).length === 0) { const th = makeThread("Welcome to VenkatGPT"); return { [th.id]: th }; }
    return t;
  });
  const [activeId, setActiveId] = useState(() => {
    const saved = localStorage.getItem(ACTIVE_KEY);
    const t = loadThreads();
    if (saved && t[saved]) return saved;
    return Object.keys(t)[0] || "";
  });
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [streaming, setStreaming] = useState(false);
  const [input, setInput] = useState("");
  const [suggestions, setSuggestions] = useState([]);
  const [showResume, setShowResume] = useState(false);
  const [isMobile, setIsMobile] = useState(false);

  const bottomRef = useRef(null);
  const inputRef = useRef(null);
  const abortRef = useRef(null);
  const tts = useTTS();

  // Detect mobile (touch device — no hover support)
  useEffect(() => {
    const check = () => setIsMobile(window.innerWidth < 768 || 'ontouchstart' in window);
    check();
    window.addEventListener("resize", check);
    return () => window.removeEventListener("resize", check);
  }, []);

  const activeThread = threads[activeId];
  const messages = activeThread?.messages || [];
  const isFirstVisit = messages.length <= 1;

  useEffect(() => { saveThreads(threads); }, [threads]);
  useEffect(() => { localStorage.setItem(ACTIVE_KEY, activeId); }, [activeId]);
  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  const createThread = useCallback(() => {
    const t = makeThread("New conversation");
    setThreads(p => ({ ...p, [t.id]: t }));
    setActiveId(t.id);
    setSuggestions([]);
  }, []);

  const deleteThread = useCallback((id) => {
    setThreads(p => {
      const n = { ...p }; delete n[id];
      if (Object.keys(n).length === 0) { const f = makeThread("Welcome"); n[f.id] = f; setActiveId(f.id); }
      else if (id === activeId) setActiveId(Object.keys(n)[0]);
      return n;
    });
    setSuggestions([]);
  }, [activeId]);

  const renameThread = useCallback((id, title) => {
    setThreads(p => ({ ...p, [id]: { ...p[id], title } }));
  }, []);

  const selectThread = useCallback((id) => {
    setActiveId(id); setSuggestions([]);
  }, []);

  const autoTitle = (q) => q.length > 48 ? q.slice(0, 48) + "…" : q;

  const send = async (text) => {
    const q = (text || input).trim();
    if (!q || streaming) return;
    setInput(""); setStreaming(true); setSuggestions([]);
    if (/\b(resume|cv)\b/i.test(q)) setTimeout(() => setShowResume(true), 800);

    const mid = genId(), aid = genId();
    setThreads(p => {
      const th = { ...p[activeId] };
      if (th.messages.length === 1) th.title = autoTitle(q);
      th.messages = [...th.messages, { id: mid, role: "user", content: q, timestamp: now() }, { id: aid, role: "assistant", content: "", streaming: true, timestamp: now() }];
      th.updatedAt = now();
      return { ...p, [activeId]: th };
    });

    let acc = "";
    try {
      abortRef.current = new AbortController();
      const res = await fetch(`${API_URL}/api/v1/chat`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: q, mode: "technical" }),
        signal: abortRef.current.signal,
      });
      const reader = res.body.getReader(); const dec = new TextDecoder();
      while (true) {
        const { done, value } = await reader.read(); if (done) break;
        for (const line of dec.decode(value, { stream: true }).split("\n")) {
          if (!line.startsWith("data: ")) continue;
          try { const ev = JSON.parse(line.slice(6)); if (ev.type === "token") { acc += ev.data; setThreads(p => ({ ...p, [activeId]: { ...p[activeId], messages: p[activeId].messages.map(m => m.id === aid ? { ...m, content: acc } : m) } })); } } catch { }
        }
      }
      setThreads(p => ({ ...p, [activeId]: { ...p[activeId], messages: p[activeId].messages.map(m => m.id === aid ? { ...m, streaming: false } : m) } }));
      setSuggestions(buildFollowUps(q, acc));
    } catch (e) {
      if (e.name !== "AbortError") {
        setThreads(p => ({ ...p, [activeId]: { ...p[activeId], messages: p[activeId].messages.map(m => m.id === aid ? { ...m, content: "Connection error. Please try again.", streaming: false } : m) } }));
      }
    } finally { setStreaming(false); inputRef.current?.focus(); }
  };

  const stopStream = () => { abortRef.current?.abort(); setStreaming(false); setThreads(p => ({ ...p, [activeId]: { ...p[activeId], messages: p[activeId].messages.map(m => m.streaming ? { ...m, streaming: false } : m) } })); };

  return (
    <div className="flex h-screen overflow-hidden" style={{ background: "#020817", fontFamily: "'DM Sans',sans-serif" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700&family=DM+Mono:wght@400;500&display=swap');
        *{box-sizing:border-box;}
        ::-webkit-scrollbar{width:4px;height:4px;}
        ::-webkit-scrollbar-track{background:transparent;}
        ::-webkit-scrollbar-thumb{background:rgba(6,182,212,0.15);border-radius:9999px;}
        @keyframes orb1{0%,100%{transform:translate(0,0)}50%{transform:translate(36px,-28px)}}
        @keyframes orb2{0%,100%{transform:translate(0,0)}50%{transform:translate(-30px,20px)}}
        @keyframes msgIn{from{opacity:0;transform:translateY(10px) scale(0.97)}to{opacity:1;transform:translateY(0) scale(1)}}
        @keyframes blink{0%,50%{opacity:1}51%,100%{opacity:0}}
        @keyframes bars{0%,80%,100%{transform:scaleY(0.3)}40%{transform:scaleY(1)}}
        @keyframes jIn{from{opacity:0;transform:translateY(5px)}to{opacity:1;transform:translateY(0)}}
        .typing-cur::after{content:'▊';animation:blink 0.8s infinite;color:#06b6d4;margin-left:2px;}
        .prose{color:#d1d5db;}
        .glow-input:focus{box-shadow:0 0 0 1px rgba(6,182,212,0.3),0 0 28px rgba(6,182,212,0.07);}
        .jcard{transition:all 0.2s cubic-bezier(0.34,1.56,0.64,1);}
        .jcard:hover,.jcard:active{transform:translateY(-2px) scale(1.02);}
        .sfbtn{transition:all 0.15s ease;}
        .sfbtn:hover,.sfbtn:active{background:rgba(139,92,246,0.15)!important;border-color:rgba(139,92,246,0.32)!important;color:#c4b5fd!important;}
        /* Mobile safe area */
        @supports(padding-bottom:env(safe-area-inset-bottom)){
          .input-bar{padding-bottom:calc(0.75rem + env(safe-area-inset-bottom));}
        }
      `}</style>

      <ParticleField />
      <Sidebar threads={threads} activeId={activeId} onSelect={selectThread} onNew={createThread} onDelete={deleteThread} onRename={renameThread} isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} onResumeOpen={() => setShowResume(true)} />

      {/* MAIN */}
      <div className="flex flex-col flex-1 min-w-0 relative z-10">

        {/* HEADER */}
        <header className="flex-shrink-0 flex items-center justify-between px-3 sm:px-4 py-3"
          style={{ borderBottom: "1px solid rgba(6,182,212,0.08)", background: "rgba(2,8,23,0.93)", backdropFilter: "blur(22px)" }}>
          <div className="flex items-center gap-2 sm:gap-3">
            {/* Hamburger */}
            <button onClick={() => setSidebarOpen(o => !o)} className="flex flex-col justify-center gap-[5px] w-9 h-9 rounded-xl hover:bg-white/[0.04] flex-shrink-0 transition-colors" aria-label="Menu">
              <span className="w-[17px] h-[1.5px] rounded-full bg-gray-400 block mx-auto" />
              <span className="w-[17px] h-[1.5px] rounded-full bg-gray-400 block mx-auto" />
              <span className="w-[12px] h-[1.5px] rounded-full bg-gray-400 block mx-auto" />
            </button>
            {/* Logo */}
            <div className="flex items-center gap-2">
              <div className="relative w-9 h-9 rounded-xl flex items-center justify-center text-xs font-bold text-black flex-shrink-0"
                style={{ background: "linear-gradient(135deg,#06b6d4,#8b5cf6)", boxShadow: "0 0 22px rgba(6,182,212,0.42)" }}>
                V
                <div className="absolute inset-0 rounded-xl animate-ping opacity-[0.17]" style={{ background: "linear-gradient(135deg,#06b6d4,#8b5cf6)", animationDuration: "3s" }} />
              </div>
              <div>
                <div className="flex items-center gap-1.5">
                  <span className="font-bold text-white text-sm sm:text-base tracking-tight" style={{ fontFamily: "'DM Mono',monospace" }}>VenkatGPT</span>
                  <span className="text-xs px-1.5 py-0.5 rounded font-mono hidden sm:inline" style={{ background: "rgba(6,182,212,0.1)", color: "#06b6d4", border: "1px solid rgba(6,182,212,0.18)" }}>v2.0</span>
                </div>
                <p className="text-xs hidden sm:block" style={{ color: "#6b7280" }}>AI Portfolio Engine</p>
              </div>
            </div>
          </div>

          {/* Center title */}
          <div className="hidden md:flex flex-1 justify-center px-3">
            <p className="text-xs truncate max-w-[200px]" style={{ color: "#4b5563" }}>{activeThread?.title || "New conversation"}</p>
          </div>

          {/* Right */}
          <div className="flex items-center gap-1.5 sm:gap-2">
            <button onClick={() => setShowResume(true)}
              className="hidden sm:flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg transition-all"
              style={{ background: "rgba(6,182,212,0.07)", color: "#67e8f9", border: "1px solid rgba(6,182,212,0.14)" }}>
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
              Resume
            </button>
            <button onClick={createThread}
              className="flex items-center gap-1 text-xs px-2.5 sm:px-3 py-1.5 rounded-lg transition-all"
              style={{ background: "rgba(255,255,255,0.03)", color: "#9ca3af", border: "1px solid rgba(255,255,255,0.06)" }}>
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" /></svg>
              <span className="hidden sm:inline">New</span>
            </button>
            <div className="flex items-center gap-1.5 pl-1">
              <div className="relative"><div className="w-2 h-2 rounded-full bg-emerald-400" /><div className="absolute inset-0 w-2 h-2 rounded-full bg-emerald-400 animate-ping opacity-40" /></div>
              <span className="text-xs hidden sm:block" style={{ color: "#6b7280" }}>Online</span>
            </div>
          </div>
        </header>

        {/* MESSAGES */}
        <main className="flex-1 overflow-y-auto px-3 sm:px-4 py-5 sm:py-6">
          <div className="max-w-3xl mx-auto space-y-4 sm:space-y-5">
            {messages.map((m, idx) => (
              <Message key={m.id} msg={m} tts={tts} isMobile={isMobile}
                onSuggest={() => {
                  const prevUser = [...messages].slice(0, idx).reverse().find(x => x.role === "user");
                  setSuggestions(buildFollowUps(prevUser?.content || "", m.content));
                }} />
            ))}

            {/* Typing indicator */}
            {streaming && messages[messages.length - 1]?.role === "user" && (
              <div className="flex items-center gap-2 sm:gap-3" style={{ animation: "msgIn 0.25s ease both" }}>
                <div className="w-8 h-8 sm:w-9 sm:h-9 rounded-xl flex-shrink-0 flex items-center justify-center text-xs font-bold text-black" style={{ background: "linear-gradient(135deg,#06b6d4,#8b5cf6)", boxShadow: "0 0 20px rgba(6,182,212,0.35)" }}>V</div>
                <div className="px-4 sm:px-5 py-3.5 sm:py-4 rounded-2xl rounded-tl-sm" style={{ background: "rgba(11,18,36,0.92)", border: "1px solid rgba(6,182,212,0.11)" }}>
                  <div className="flex gap-[3px] items-end" style={{ height: 18 }}>
                    {[0, 1, 2].map(i => <div key={i} className="w-[3px] rounded-full bg-cyan-400" style={{ height: 18, animation: `bars 1.2s ease-in-out ${i * 0.15}s infinite`, transformOrigin: "bottom" }} />)}
                  </div>
                </div>
              </div>
            )}

            {/* JOURNEY MAP */}
            {isFirstVisit && !streaming && (
              <div className="ml-10 sm:ml-12">
                <p className="text-xs uppercase tracking-widest mb-3 font-mono" style={{ color: "#4b5563" }}>↓ Start your journey</p>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                  {JOURNEY.map((s, i) => (
                    <button key={s.label} onClick={() => send(s.q)}
                      className="jcard flex flex-col items-center gap-2 p-3 sm:p-3.5 rounded-xl text-center active:scale-95"
                      style={{ background: "rgba(11,18,36,0.85)", border: "1px solid rgba(6,182,212,0.1)", animation: `jIn 0.3s ease both ${i * 0.06}s` }}>
                      <span className="text-xl sm:text-2xl">{s.icon}</span>
                      <span className="text-xs font-medium leading-tight" style={{ color: "#d1d5db" }}>{s.label}</span>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* SMART FOLLOW-UPS */}
            {suggestions.length > 0 && !streaming && (
              <div className="ml-10 sm:ml-12" style={{ animation: "jIn 0.3s ease both" }}>
                <p className="text-xs mb-2 font-mono tracking-wide" style={{ color: "#4b5563" }}>Suggested follow-ups:</p>
                <div className="flex flex-wrap gap-1.5 sm:gap-2">
                  {suggestions.map(s => (
                    <button key={s} onClick={() => { setSuggestions([]); send(s); }}
                      className="sfbtn text-xs px-3 py-1.5 rounded-xl active:scale-95"
                      style={{ background: "rgba(139,92,246,0.07)", color: "#a78bfa", border: "1px solid rgba(139,92,246,0.16)" }}>
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            )}

            <div ref={bottomRef} />
          </div>
        </main>

        {/* INPUT BAR */}
        <div className="input-bar flex-shrink-0 px-3 sm:px-4 pb-3 sm:pb-4 pt-2"
          style={{ borderTop: "1px solid rgba(6,182,212,0.07)", background: "rgba(2,8,23,0.96)", backdropFilter: "blur(22px)" }}>
          <div className="max-w-3xl mx-auto">
            <div className="flex gap-2 sm:gap-3 items-end">
              <div className="flex-1 min-w-0">
                <textarea ref={inputRef} value={input} rows={1}
                  onChange={e => { setInput(e.target.value); e.target.style.height = "auto"; e.target.style.height = Math.min(e.target.scrollHeight, 140) + "px"; }}
                  onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } }}
                  placeholder="Ask about projects, skills, achievements, coding profiles..."
                  disabled={streaming}
                  className="glow-input w-full text-sm text-gray-100 placeholder-gray-600 rounded-2xl resize-none px-4 sm:px-5 py-3 sm:py-3.5 outline-none transition-all"
                  style={{ background: "rgba(11,18,36,0.85)", border: "1px solid rgba(6,182,212,0.17)", overflow: "hidden", fontFamily: "'DM Sans',sans-serif", lineHeight: 1.6, minHeight: 48 }} />
              </div>
              {streaming ? (
                <button onClick={stopStream}
                  className="flex-shrink-0 w-11 h-11 rounded-xl flex items-center justify-center transition-all active:scale-95"
                  style={{ background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.22)", color: "#f87171" }}>
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><rect x="6" y="6" width="12" height="12" rx="2" /></svg>
                </button>
              ) : (
                <button onClick={() => send()} disabled={!input.trim()}
                  className="flex-shrink-0 w-11 h-11 rounded-xl flex items-center justify-center transition-all active:scale-95"
                  style={{ background: input.trim() ? "linear-gradient(135deg,#06b6d4,#8b5cf6)" : "rgba(255,255,255,0.03)", border: input.trim() ? "none" : "1px solid rgba(255,255,255,0.06)", boxShadow: input.trim() ? "0 0 24px rgba(6,182,212,0.28)" : "none", cursor: input.trim() ? "pointer" : "not-allowed" }}>
                  <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" /></svg>
                </button>
              )}
            </div>
            <p className="text-center text-xs mt-2 font-mono tracking-wide" style={{ color: "#374151" }}>
              {isMobile ? "Threads auto-saved · RAG-grounded · Send ↑" : "Threads auto-saved · RAG-grounded · Enter to send · Shift+Enter for new line"}
            </p>
          </div>
        </div>
      </div>

      {showResume && <ResumeModal onClose={() => setShowResume(false)} />}
    </div>
  );
}