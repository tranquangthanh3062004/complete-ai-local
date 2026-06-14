"""
Streamlit Frontend v6.0 — GTCC Bot
Thiết kế lại: Dark/light premium UI, tối giản, hiện đại.
"""
import streamlit as st
import requests
import uuid
import os
from datetime import datetime

# ── Config ────────────────────────────────────────────────────────────────────
BASE_URL        = os.environ.get("BACKEND_URL", "http://127.0.0.1:8000")
REQUEST_TIMEOUT = 120
HEALTH_TIMEOUT  = 5

st.set_page_config(
    page_title="GTCC Bot — Trợ Lý Giao Thông Công Cộng",
    page_icon="🚌",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Premium CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

/* ── Reset & Base ── */
*, html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
}
.stApp {
    background: #0D0F14 !important;
}
section[data-testid="stSidebar"] {
    background: #13161E !important;
    border-right: 1px solid rgba(255,255,255,0.06) !important;
}
.stApp > header { background: transparent !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.12); border-radius: 2px; }

/* ── HERO BANNER ── */
.hero-banner {
    background: linear-gradient(135deg, #1a1d27 0%, #0f1219 60%, #141720 100%);
    border: 1px solid rgba(99, 179, 237, 0.15);
    border-radius: 20px;
    padding: 32px 36px;
    margin-bottom: 24px;
    position: relative;
    overflow: hidden;
}
.hero-banner::before {
    content: '';
    position: absolute;
    top: -60px; right: -60px;
    width: 200px; height: 200px;
    background: radial-gradient(circle, rgba(56,189,248,0.12) 0%, transparent 70%);
    border-radius: 50%;
}
.hero-banner::after {
    content: '';
    position: absolute;
    bottom: -40px; left: 30%;
    width: 160px; height: 160px;
    background: radial-gradient(circle, rgba(168,85,247,0.08) 0%, transparent 70%);
    border-radius: 50%;
}
.hero-title {
    font-size: 1.9rem;
    font-weight: 800;
    background: linear-gradient(90deg, #E2E8F0 0%, #94A3B8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0 0 6px 0;
    line-height: 1.2;
}
.hero-sub {
    color: rgba(148, 163, 184, 0.7);
    font-size: 0.87rem;
    margin: 0;
    font-weight: 400;
    letter-spacing: 0.01em;
}
.hero-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(56,189,248,0.1);
    border: 1px solid rgba(56,189,248,0.25);
    color: #7DD3FC;
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    margin-bottom: 14px;
}

/* ── QUICK QUESTIONS ── */
.quick-label {
    color: rgba(148,163,184,0.55);
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin: 0 0 10px 0;
}

/* ── TABS ── */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    border-radius: 12px !important;
    padding: 4px !important;
    gap: 2px !important;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 9px !important;
    color: rgba(148,163,184,0.6) !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    padding: 8px 16px !important;
    transition: all 0.2s !important;
}
.stTabs [aria-selected="true"] {
    background: rgba(56,189,248,0.12) !important;
    color: #7DD3FC !important;
    border-bottom: none !important;
}
.stTabs [data-baseweb="tab-border"] { display: none !important; }

/* ── CHAT MESSAGES ── */
[data-testid="stChatMessage"] {
    background: transparent !important;
    border: none !important;
}
[data-testid="stChatMessageContent"] {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    border-radius: 16px !important;
    color: #CBD5E1 !important;
    padding: 14px 18px !important;
    line-height: 1.7 !important;
}
[data-testid="stChatMessage"][data-testid*="user"] [data-testid="stChatMessageContent"] {
    background: rgba(56,189,248,0.08) !important;
    border-color: rgba(56,189,248,0.2) !important;
}

/* ── CHAT INPUT ── */
[data-testid="stChatInput"] {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 14px !important;
    color: #E2E8F0 !important;
}
[data-testid="stChatInput"]:focus-within {
    border-color: rgba(56,189,248,0.4) !important;
    box-shadow: 0 0 0 3px rgba(56,189,248,0.06) !important;
}

/* ── BUTTONS ── */
.stButton > button {
    background: rgba(56,189,248,0.1) !important;
    color: #7DD3FC !important;
    border: 1px solid rgba(56,189,248,0.25) !important;
    border-radius: 10px !important;
    font-weight: 500 !important;
    font-size: 0.82rem !important;
    transition: all 0.18s !important;
    padding: 8px 16px !important;
}
.stButton > button:hover {
    background: rgba(56,189,248,0.18) !important;
    border-color: rgba(56,189,248,0.45) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 14px rgba(56,189,248,0.12) !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #0EA5E9 0%, #38BDF8 100%) !important;
    color: #0D0F14 !important;
    border: none !important;
    font-weight: 700 !important;
}
.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #38BDF8 0%, #7DD3FC 100%) !important;
    box-shadow: 0 6px 20px rgba(56,189,248,0.25) !important;
}

/* ── INPUTS & SELECTS ── */
.stTextInput > div > div > input,
.stSelectbox > div > div,
.stSlider > div,
input[type="password"] {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 10px !important;
    color: #CBD5E1 !important;
}

/* ── SIDEBAR ── */
.sidebar-logo {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 20px 0 16px;
    margin-bottom: 4px;
}
.sidebar-logo .logo-icon {
    width: 38px; height: 38px;
    background: linear-gradient(135deg, #0EA5E9, #7C3AED);
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 18px;
}
.sidebar-logo .logo-text {
    font-size: 1rem;
    font-weight: 700;
    color: #E2E8F0;
    line-height: 1.2;
}
.sidebar-logo .logo-ver {
    font-size: 0.68rem;
    color: rgba(148,163,184,0.4);
    font-weight: 400;
}
.sidebar-section {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px;
    padding: 14px;
    margin: 10px 0;
}
.sidebar-section-title {
    font-size: 0.68rem;
    font-weight: 700;
    color: rgba(148,163,184,0.4);
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin: 0 0 10px 0;
}

/* ── CHIPS ── */
.chip {
    display: inline-flex; align-items: center; gap: 4px;
    padding: 3px 10px; border-radius: 20px;
    font-size: 10px; font-weight: 600;
    margin: 2px 2px 0 0; vertical-align: middle;
}
.chip-topic { background: rgba(56,189,248,0.1); color: #7DD3FC; border: 1px solid rgba(56,189,248,0.2); }
.chip-cache { background: rgba(251,191,36,0.1); color: #FCD34D; border: 1px solid rgba(251,191,36,0.2); }
.chip-source { background: rgba(167,243,208,0.08); color: #6EE7B7; border: 1px solid rgba(167,243,208,0.15); }

/* ── CARDS ── */
.route-card {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 14px;
    padding: 18px 20px;
    margin: 10px 0;
    transition: border-color 0.2s;
}
.route-card:hover { border-color: rgba(56,189,248,0.25); }
.route-card-title { color: #7DD3FC; font-weight: 700; font-size: 0.95rem; }
.route-card-body { color: #94A3B8; font-size: 0.84rem; line-height: 1.7; margin-top: 8px; }

.faq-answer {
    background: rgba(255,255,255,0.025);
    border-left: 3px solid rgba(56,189,248,0.4);
    border-radius: 0 8px 8px 0;
    padding: 12px 16px;
    color: #94A3B8;
    font-size: 0.88rem;
    line-height: 1.7;
}
.excerpt-box {
    background: rgba(255,255,255,0.025);
    border-left: 3px solid rgba(56,189,248,0.3);
    border-radius: 0 8px 8px 0;
    padding: 10px 14px;
    color: #94A3B8;
    font-size: 0.83rem;
    line-height: 1.6;
    margin: 6px 0;
}

/* ── METRICS ── */
div[data-testid="metric-container"] {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    border-radius: 12px !important;
    padding: 14px !important;
}
div[data-testid="stMetricValue"] { color: #E2E8F0 !important; }
div[data-testid="stMetricLabel"] { color: rgba(148,163,184,0.6) !important; }

/* ── EXPANDER ── */
.streamlit-expander {
    background: rgba(255,255,255,0.02) !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    border-radius: 10px !important;
}

/* ── DIVIDER ── */
hr { border-color: rgba(255,255,255,0.06) !important; }

/* ── CAPTIONS ── */
.stCaption, [data-testid="stCaptionContainer"] { color: rgba(148,163,184,0.5) !important; }

/* ── SUCCESS/ERROR/INFO ── */
.stSuccess { background: rgba(16,185,129,0.08) !important; border-color: rgba(16,185,129,0.2) !important; color: #6EE7B7 !important; }
.stError { background: rgba(239,68,68,0.08) !important; border-color: rgba(239,68,68,0.2) !important; color: #FCA5A5 !important; }
.stWarning { background: rgba(245,158,11,0.08) !important; border-color: rgba(245,158,11,0.2) !important; color: #FCD34D !important; }
.stInfo { background: rgba(56,189,248,0.06) !important; border-color: rgba(56,189,248,0.15) !important; color: #7DD3FC !important; }

/* ── QUICK TIPS BANNER ── */
.status-dot {
    display: inline-block;
    width: 7px; height: 7px;
    border-radius: 50%;
    margin-right: 5px;
    vertical-align: middle;
}
.dot-green { background: #10B981; box-shadow: 0 0 6px rgba(16,185,129,0.6); }
.dot-red   { background: #EF4444; box-shadow: 0 0 6px rgba(239,68,68,0.6); }
.dot-amber { background: #F59E0B; box-shadow: 0 0 6px rgba(245,158,11,0.6); }

.info-strip {
    background: rgba(56,189,248,0.05);
    border: 1px solid rgba(56,189,248,0.12);
    border-radius: 10px;
    padding: 10px 16px;
    color: rgba(125,211,252,0.7);
    font-size: 0.8rem;
    margin-bottom: 16px;
}

/* ── SUGGESTION BUTTON ── */
.sug-btn > button {
    background: rgba(255,255,255,0.025) !important;
    border-color: rgba(255,255,255,0.08) !important;
    color: rgba(148,163,184,0.7) !important;
    font-size: 0.77rem !important;
    padding: 5px 12px !important;
    border-radius: 8px !important;
}
.sug-btn > button:hover {
    background: rgba(56,189,248,0.08) !important;
    color: #7DD3FC !important;
    border-color: rgba(56,189,248,0.25) !important;
}
</style>
""", unsafe_allow_html=True)


# ── Session State ─────────────────────────────────────────────────────────────
for k, v in {
    "session_id"    : str(uuid.uuid4())[:8],
    "messages"      : [],
    "rag_messages"  : [],
    "token"         : None,
    "username"      : None,
    "model_list"    : [],
    "selected_model": None,
    "temperature"   : 0.1,
    "prefill_chat"  : None,
    "prefill_rag"   : None,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ── Helpers ───────────────────────────────────────────────────────────────────
def auth_headers() -> dict:
    h = {"Content-Type": "application/json"}
    if st.session_state.token:
        h["Authorization"] = f"Bearer {st.session_state.token}"
    return h


def api_get(path: str, timeout: int = HEALTH_TIMEOUT):
    try:
        return requests.get(f"{BASE_URL}{path}", headers=auth_headers(), timeout=timeout)
    except Exception:
        return None


def api_post(path: str, payload: dict = None, timeout: int = REQUEST_TIMEOUT):
    try:
        return requests.post(
            f"{BASE_URL}{path}",
            json=payload or {},
            headers=auth_headers(),
            timeout=timeout,
        )
    except requests.exceptions.Timeout:
        return "timeout"
    except Exception:
        return None


def play_tts(text: str):
    if not text or len(text.strip()) < 5:
        return
    try:
        resp = requests.post(
            f"{BASE_URL}/tts",
            json={"text": text, "lang": "vi"},
            headers={"Content-Type": "application/json"},
            timeout=20,
        )
        if resp and resp.ok and resp.content:
            st.audio(resp.content, format="audio/mp3")
    except Exception:
        pass


def get_models() -> list:
    resp = api_get("/models")
    if resp and resp.ok:
        return resp.json().get("models", [])
    return []


# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sidebar-logo">
        <div class="logo-icon">🚌</div>
        <div>
            <div class="logo-text">GTCC Bot</div>
            <div class="logo-ver">v6.0 · AI Giao Thông</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    # Auth
    if st.session_state.token is None:
        st.markdown('<p class="sidebar-section-title">🔐 Đăng nhập</p>', unsafe_allow_html=True)
        with st.container():
            email = st.text_input("Email", value="admin@local.com", label_visibility="collapsed",
                                  placeholder="Email")
            pwd   = st.text_input("Mật khẩu", type="password", value="admin123",
                                  label_visibility="collapsed", placeholder="Mật khẩu")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Đăng nhập", type="primary", use_container_width=True):
                    try:
                        resp = requests.post(
                            f"{BASE_URL}/auth/token",
                            data={"username": email, "password": pwd}, timeout=10,
                        )
                        if resp.status_code == 200:
                            st.session_state.token    = resp.json()["access_token"]
                            st.session_state.username = email.split("@")[0]
                            st.rerun()
                        else:
                            st.error("Sai thông tin")
                    except Exception:
                        st.session_state.username = "Khách"
                        st.rerun()
            with c2:
                if st.button("Khách", use_container_width=True):
                    st.session_state.username = "Khách"
                    st.rerun()
    else:
        st.markdown(f"""
        <div class="sidebar-section">
            <p class="sidebar-section-title">Tài khoản</p>
            <p style="color:#7DD3FC; font-weight:600; margin:0; font-size:0.9rem;">
                👤 {st.session_state.username}
            </p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Đăng xuất", use_container_width=True):
            for k in ["token", "username"]:
                st.session_state[k] = None
            st.session_state.messages     = []
            st.session_state.rag_messages = []
            st.rerun()

    st.divider()

    # AI settings
    st.markdown('<p class="sidebar-section-title">⚙️ Cài đặt AI</p>', unsafe_allow_html=True)
    if st.button("↻ Tải danh sách model", use_container_width=True):
        st.session_state.model_list = get_models()
        if st.session_state.model_list:
            st.toast(f"Đã tải {len(st.session_state.model_list)} model", icon="✅")

    if st.session_state.model_list:
        st.session_state.selected_model = st.selectbox(
            "Model", st.session_state.model_list, index=0,
            label_visibility="collapsed"
        )
    else:
        st.caption("Nhấn ↻ để xem danh sách model")

    st.session_state.temperature = st.slider(
        "Sáng tạo", 0.0, 1.0,
        value=float(st.session_state.temperature), step=0.05,
        help="Temperature — càng cao càng sáng tạo"
    )

    st.divider()

    # Health
    st.markdown('<p class="sidebar-section-title">🔍 Trạng thái hệ thống</p>', unsafe_allow_html=True)
    if st.button("Kiểm tra kết nối", use_container_width=True):
        resp = api_get("/health", timeout=5)
        if resp and resp.ok:
            data = resp.json()
            online = data.get("ollama_online") or data.get("llm_online")
            dot = '<span class="status-dot dot-green"></span>' if online else '<span class="status-dot dot-amber"></span>'
            engine = data.get("engine", "LLM")
            status = "Online" if online else "Offline"
            st.markdown(f"<p style='color:#94A3B8;font-size:0.82rem'>{dot}{engine}: <b style='color:{'#6EE7B7' if online else '#FCD34D'}'>{status}</b></p>", unsafe_allow_html=True)
            st.caption(f"Model: {data.get('active_model','?')}")
        else:
            st.markdown('<p style="color:#FCA5A5;font-size:0.82rem"><span class="status-dot dot-red"></span>Backend chưa chạy</p>', unsafe_allow_html=True)

    st.divider()
    st.markdown('<p class="sidebar-section-title">Chủ đề hỗ trợ</p>', unsafe_allow_html=True)
    st.markdown("""
    <div style="color:rgba(148,163,184,0.6);font-size:0.8rem;line-height:2;">
        🚌 Xe Buýt &nbsp;·&nbsp; 🚇 Metro<br>
        🚍 BRT &nbsp;·&nbsp; 🎫 Vé & Giá<br>
        📋 Luật GT &nbsp;·&nbsp; ✈️ Sân Bay
    </div>
    """, unsafe_allow_html=True)
    st.caption(f"Session `{st.session_state.session_id}`")


# ── HERO ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-banner">
    <div class="hero-badge">✦ AI Giao Thông Việt Nam</div>
    <h1 class="hero-title">🚌 GTCC Bot</h1>
    <p class="hero-sub">Hỏi đáp thông minh về Xe Buýt · Metro · BRT · Lịch Trình · Giá Vé · Luật Giao Thông</p>
</div>
""", unsafe_allow_html=True)


# ── TABS ─────────────────────────────────────────────────────────────────────
tab_chat, tab_rag, tab_route, tab_faq, tab_stats, tab_docs = st.tabs([
    "💬 Hỏi AI",
    "📚 Tài Liệu RAG",
    "🗺️ Lộ Trình",
    "❓ FAQ",
    "📊 Thống Kê",
    "📁 Upload",
])


# ════════════════════════════════════════════════════════════════════════════════
# TAB 1 · CHAT
# ════════════════════════════════════════════════════════════════════════════════
with tab_chat:
    # Quick questions
    st.markdown('<p class="quick-label">💡 Gợi ý nhanh</p>', unsafe_allow_html=True)
    quick_qs = [
        "🚌 Metro số 1 HCM có những ga nào?",
        "✈️ Từ sân bay TSN vào trung tâm?",
        "🎫 Học sinh giảm giá vé không?",
        "📱 App tra cứu xe buýt tốt nhất?",
    ]
    cols = st.columns(4)
    for i, (col, q) in enumerate(zip(cols, quick_qs)):
        with col:
            if st.button(q, key=f"qk_{i}", use_container_width=True):
                st.session_state.prefill_chat = q
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # Message history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant":
                chips_html = ""
                if msg.get("topic"):
                    chips_html += f'<span class="chip chip-topic">📌 {msg["topic"]}</span>'
                if msg.get("cached"):
                    chips_html += '<span class="chip chip-cache">⚡ Cache</span>'
                if chips_html:
                    st.markdown(chips_html, unsafe_allow_html=True)

                ev_id = msg.get("event_id", -1)
                b1, b2, b3, _ = st.columns([1, 1, 1, 9])
                with b1:
                    if ev_id and ev_id > 0:
                        if st.button("👍", key=f"pos_{ev_id}_{msg.get('idx',0)}"):
                            api_post("/learning/feedback", {"event_id": ev_id, "feedback": 1}, timeout=5)
                            st.toast("Cảm ơn! 👍", icon="✅")
                with b2:
                    if ev_id and ev_id > 0:
                        if st.button("👎", key=f"neg_{ev_id}_{msg.get('idx',0)}"):
                            api_post("/learning/feedback", {"event_id": ev_id, "feedback": -1}, timeout=5)
                            st.toast("Đã ghi nhận 👎")
                with b3:
                    if st.button("🔊", key=f"tts_{ev_id}_{msg.get('idx',0)}"):
                        play_tts(msg["content"])

                if msg.get("suggestions"):
                    sug_cols = st.columns(min(len(msg["suggestions"]), 3))
                    for i, (scol, sug) in enumerate(zip(sug_cols, msg["suggestions"])):
                        with scol:
                            with st.container():
                                st.markdown('<div class="sug-btn">', unsafe_allow_html=True)
                                if st.button(f"→ {sug}", key=f"sug_c_{ev_id}_{i}",
                                             use_container_width=True):
                                    st.session_state.prefill_chat = sug
                                    st.rerun()
                                st.markdown('</div>', unsafe_allow_html=True)

    # Input
    prefill = st.session_state.prefill_chat
    st.session_state.prefill_chat = None
    prompt = st.chat_input("Hỏi về xe buýt, metro, luật giao thông...", key="chat_input")
    if not prompt and prefill:
        prompt = prefill

    if prompt:
        idx = len(st.session_state.messages)
        st.session_state.messages.append({"role": "user", "content": prompt, "idx": idx})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Đang tìm kiếm thông tin..."):
                resp = api_post("/agents/direct", {
                    "query"      : prompt,
                    "model_name" : st.session_state.selected_model,
                    "temperature": float(st.session_state.temperature),
                    "messages"   : st.session_state.messages[-6:],
                    "session_id" : st.session_state.session_id,
                    "suggest"    : True,
                }, timeout=REQUEST_TIMEOUT)

            if resp is None:
                answer = "❌ Không thể kết nối backend. Hãy chạy `START.bat` trước."
                st.error(answer)
            elif resp == "timeout":
                answer = "⏱️ Quá thời gian chờ. Model đang xử lý, thử lại sau."
                st.warning(answer)
            elif hasattr(resp, "status_code") and not resp.ok:
                try:    detail = resp.json().get("detail", resp.text)
                except: detail = resp.text
                answer = f"⚠️ {detail}" if resp.status_code == 400 else f"❌ Lỗi: {detail}"
                st.warning(answer) if resp.status_code == 400 else st.error(answer)
            else:
                data        = resp.json()
                answer      = data.get("result", "").strip() or "Xin lỗi, chưa tìm được thông tin."
                ev_id       = data.get("event_id", -1)
                topic       = data.get("topic", "")
                resp_ms     = data.get("response_ms", 0)
                is_cached   = data.get("cached", False)
                suggestions = data.get("suggestions", [])

                st.markdown(answer)

                chips = ""
                if topic:    chips += f'<span class="chip chip-topic">📌 {topic}</span>'
                if is_cached: chips += '<span class="chip chip-cache">⚡ Cache</span>'
                if chips: st.markdown(chips, unsafe_allow_html=True)

                label = "⚡ Cache" if is_cached else f"⏱️ {resp_ms:.0f}ms"
                st.caption(f"{label} · {data.get('model', '?')}")

                if len(answer) <= 250:
                    play_tts(answer)

                idx2 = len(st.session_state.messages)
                st.session_state.messages.append({
                    "role": "assistant", "content": answer,
                    "event_id": ev_id, "topic": topic,
                    "cached": is_cached, "suggestions": suggestions, "idx": idx2,
                })
        st.rerun()

    # Actions row
    st.markdown("<br>", unsafe_allow_html=True)
    a1, a2, _ = st.columns([1, 1, 5])
    with a1:
        if st.button("🗑️ Xóa lịch sử", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
    with a2:
        if st.button("💾 Xuất chat", use_container_width=True) and st.session_state.messages:
            lines = []
            for m in st.session_state.messages:
                role = "Bạn" if m["role"] == "user" else "GTCC Bot"
                lines.append(f"[{role}]\n{m['content']}\n")
            text = f"GTCC Bot — Export\n{'='*40}\n\n" + "\n".join(lines)
            st.download_button(
                "📥 Tải file", data=text.encode("utf-8"),
                file_name=f"gtcc_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain",
            )


# ════════════════════════════════════════════════════════════════════════════════
# TAB 2 · RAG
# ════════════════════════════════════════════════════════════════════════════════
with tab_rag:
    st.markdown("""
    <div class="info-strip">
        📚 AI tìm trong tài liệu GTCC bạn đã upload và trả lời có nguồn dẫn chứng cụ thể.
    </div>
    """, unsafe_allow_html=True)

    for msg in st.session_state.rag_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant":
                chips = ""
                if msg.get("topic"):  chips += f'<span class="chip chip-topic">📌 {msg["topic"]}</span>'
                if msg.get("cached"): chips += '<span class="chip chip-cache">⚡ Cache</span>'
                for s in msg.get("sources", []):
                    chips += f'<span class="chip chip-source">📄 {s}</span>'
                if chips: st.markdown(chips, unsafe_allow_html=True)

                if msg.get("excerpts"):
                    with st.expander("📑 Đoạn trích từ tài liệu"):
                        for ex in msg["excerpts"]:
                            st.markdown(f'<div class="excerpt-box">{ex}</div>', unsafe_allow_html=True)

                ev_id = msg.get("event_id", -1)
                if st.button("🔊", key=f"tts_rag_{ev_id}_{msg.get('idx',0)}"):
                    play_tts(msg["content"])

                if msg.get("suggestions"):
                    sug_cols = st.columns(min(len(msg["suggestions"]), 3))
                    for i, (scol, sug) in enumerate(zip(sug_cols, msg["suggestions"])):
                        with scol:
                            if st.button(f"→ {sug}", key=f"sug_r_{ev_id}_{i}", use_container_width=True):
                                st.session_state.prefill_rag = sug
                                st.rerun()

    rag_prefill = st.session_state.prefill_rag
    st.session_state.prefill_rag = None
    rag_prompt = st.chat_input("Hỏi về tài liệu GTCC đã nạp...", key="rag_input")
    if not rag_prompt and rag_prefill:
        rag_prompt = rag_prefill

    if rag_prompt:
        idx = len(st.session_state.rag_messages)
        st.session_state.rag_messages.append({"role": "user", "content": rag_prompt, "idx": idx})
        with st.chat_message("user"):
            st.markdown(rag_prompt)

        with st.chat_message("assistant"):
            with st.spinner("Đang tìm trong tài liệu..."):
                resp = api_post("/documents/chat/", {
                    "query"     : rag_prompt,
                    "session_id": st.session_state.session_id,
                    "model_name": st.session_state.selected_model,
                    "suggest"   : True,
                }, timeout=REQUEST_TIMEOUT)

            if resp is None:
                st.error("❌ Không kết nối được backend.")
            elif resp == "timeout":
                st.warning("⏱️ Quá thời gian. Thử lại sau.")
            elif hasattr(resp, "status_code") and not resp.ok:
                try:    detail = resp.json().get("detail", resp.text)
                except: detail = resp.text
                st.warning(f"⚠️ {detail}") if resp.status_code == 400 else st.error(f"❌ {detail}")
            else:
                data        = resp.json()
                answer      = data.get("response", "").strip() or "Chưa tìm được thông tin."
                ev_id       = data.get("event_id", -1)
                topic       = data.get("topic", "")
                sources     = data.get("sources", [])
                excerpts    = data.get("excerpts", [])
                suggestions = data.get("suggestions", [])

                st.markdown(answer)
                if sources:
                    st.caption(f"📄 Nguồn: {', '.join(sources)}")

                idx2 = len(st.session_state.rag_messages)
                st.session_state.rag_messages.append({
                    "role": "assistant", "content": answer,
                    "event_id": ev_id, "topic": topic,
                    "sources": sources, "excerpts": excerpts,
                    "suggestions": suggestions, "idx": idx2,
                })
        st.rerun()

    if st.button("🗑️ Xóa lịch sử RAG"):
        st.session_state.rag_messages = []
        st.rerun()


# ════════════════════════════════════════════════════════════════════════════════
# TAB 3 · LỘ TRÌNH
# ════════════════════════════════════════════════════════════════════════════════
with tab_route:
    st.markdown("""
    <div class="info-strip">
        🗺️ Chọn điểm đi / điểm đến để xem lộ trình đề xuất (thông tin tổng hợp, cập nhật 2025).
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        from_place = st.selectbox("📍 Điểm xuất phát", [
            "Sân bay Tân Sơn Nhất",
            "Bến Thành (Quận 1)",
            "Đại học Quốc gia TP.HCM",
            "Sân bay Nội Bài",
            "Bến xe Mỹ Đình (HN)",
            "Ga Cát Linh (HN)",
        ])
    with c2:
        to_place = st.selectbox("🏁 Điểm đến", [
            "Trung tâm Quận 1 (HCM)",
            "Suối Tiên / BX Miền Đông mới",
            "Thủ Đức / ĐHQG",
            "Trung tâm Hà Nội",
            "Hà Đông (HN)",
            "Nhổn (HN)",
        ])

    ROUTE_DB = {
        ("Sân bay Tân Sơn Nhất", "Trung tâm Quận 1 (HCM)"): {
            "title": "✈️ Sân bay TSN → Trung tâm Q.1",
            "options": [
                ("🚌 Xe buýt 152", "Sân bay TSN → Cộng Hòa → Bến Thành\n⏱ 30-45 phút · 💰 5.000đ/lượt"),
                ("🚌 Xe buýt 109", "Sân bay TSN → Đề Thám → Bến Thành\n⏱ 35-50 phút · 💰 5.000đ/lượt"),
            ]
        },
        ("Bến Thành (Quận 1)", "Thủ Đức / ĐHQG"): {
            "title": "🚇 Bến Thành → Thủ Đức",
            "options": [
                ("🚇 Metro số 1", "Ga Bến Thành → Ga Thủ Đức (7 ga)\n⏱ ~18 phút · 💰 10.000đ"),
                ("🚌 Xe buýt 36", "Bến Thành → Xa Lộ Hà Nội → ĐHQG\n⏱ 60-90 phút · 💰 7.000đ"),
            ]
        },
        ("Sân bay Nội Bài", "Trung tâm Hà Nội"): {
            "title": "✈️ Nội Bài → Trung tâm HN",
            "options": [
                ("🚌 Tuyến 7", "Nội Bài → QL2 → Bến xe Mỹ Đình\n⏱ 45-50 phút · 💰 9.000đ"),
                ("🚌 Tuyến 86", "Nội Bài → QL5 → Bến xe Gia Lâm\n⏱ 45-60 phút · 💰 9.000đ"),
            ]
        },
        ("Ga Cát Linh (HN)", "Hà Đông (HN)"): {
            "title": "🚇 Cát Linh → Hà Đông",
            "options": [
                ("🚇 Metro 2A", "Ga Cát Linh → Yên Nghĩa (12 ga)\n⏱ 23 phút · 💰 15.000đ"),
                ("🚍 BRT Kim Mã", "Kim Mã → Yên Nghĩa (21 trạm)\n⏱ 30-40 phút · 💰 9.000đ"),
            ]
        },
    }

    if st.button("🔍 Tìm lộ trình", type="primary"):
        info = ROUTE_DB.get((from_place, to_place))
        if info:
            st.markdown(f"<h3 style='color:#E2E8F0;margin:16px 0 12px'>{info['title']}</h3>",
                        unsafe_allow_html=True)
            for name, detail in info["options"]:
                st.markdown(f"""
                <div class="route-card">
                    <div class="route-card-title">{name}</div>
                    <div class="route-card-body"><pre style="font-family:inherit;white-space:pre-wrap;margin:0;background:transparent;border:none;padding:0">{detail}</pre></div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Chưa có lộ trình mặc định cho tuyến này — hỏi AI để được tư vấn.")
            if st.button("💬 Hỏi AI ngay"):
                st.session_state.prefill_chat = f"Đi từ {from_place} đến {to_place} bằng phương tiện công cộng?"
                st.rerun()

    st.divider()
    st.markdown("<h4 style='color:#94A3B8;margin-bottom:12px;'>📋 Thông tin nhanh</h4>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    cards = [
        ("🚇 Metro HCM số 1", "Bến Thành → Suối Tiên\n14 ga · 19.7km · ~30 phút\n5:30–22:00 · 6.000–20.000đ"),
        ("🚇 Metro HN 2A", "Cát Linh → Hà Đông\n12 ga · 13km · ~23 phút\n5:30–22:30 · 8.000–15.000đ"),
        ("🚍 BRT Hà Nội", "Kim Mã → Yên Nghĩa\n21 trạm · 14.7km\n5:00–22:00 · 9.000đ/lượt"),
    ]
    for col, (title, body) in zip([col1, col2, col3], cards):
        with col:
            st.markdown(f"""
            <div class="route-card">
                <div class="route-card-title">{title}</div>
                <div class="route-card-body"><pre style="font-family:inherit;white-space:pre-wrap;margin:0;background:transparent;border:none;padding:0">{body}</pre></div>
            </div>
            """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════════
# TAB 4 · FAQ
# ════════════════════════════════════════════════════════════════════════════════
with tab_faq:
    faqs = [
        ("🚌 Xe Buýt", [
            ("Giá vé xe buýt là bao nhiêu?",           "TP.HCM: 5.000–8.000đ/lượt. Hà Nội: 7.000–9.000đ/lượt."),
            ("Học sinh sinh viên có được giảm giá?",    "Có. HSSV giảm 50% khi xuất trình thẻ hợp lệ."),
            ("Mua vé tháng xe buýt ở đâu?",             "Tại các điểm bán vé tháng ở bến xe trung tâm hoặc văn phòng Transerco."),
            ("Xe buýt chạy đến mấy giờ?",               "Thông thường 5h00 đến 21h00–22h00 tùy tuyến."),
        ]),
        ("🚇 Metro", [
            ("Metro số 1 TP.HCM có những ga nào?",      "14 ga: Bến Thành, Ba Son, Văn Thánh, Tân Cảng, Thảo Điền, An Phú, Rạch Chiếc, Phước Long, Bình Thái, Thủ Đức, KHU CNC, Tân Phú, Bình Dương, Suối Tiên."),
            ("Giờ hoạt động của Metro?",                 "Metro HCM số 1: 5:30–22:00. Metro Cát Linh – Hà Đông: 5:30–22:30."),
            ("Quy định khi đi metro?",                   "Không ăn uống, không hút thuốc, không mang xe máy. Nhường chỗ người ưu tiên."),
        ]),
        ("✈️ Sân Bay", [
            ("Từ sân bay TSN vào trung tâm bằng gì?",   "Xe buýt 152 (5.000đ) hoặc 109. Kết hợp Metro số 1 đến Thủ Đức."),
            ("Từ sân bay Nội Bài vào HN bằng gì?",      "Xe buýt 86 (Gia Lâm) hoặc tuyến 7 (Mỹ Đình). Giá ~9.000đ."),
        ]),
        ("📱 Ứng Dụng", [
            ("App nào tốt nhất để tra cứu xe buýt?",    "BusMap (HCM + HN), Tìm Buýt (HN), Google Maps."),
            ("Có thể mua vé metro qua app không?",       "Có. TP.HCM: HCMC Metro App. Hà Nội: iMaaS."),
        ]),
    ]

    for category, qa_list in faqs:
        st.markdown(f"<h4 style='color:#94A3B8;margin:16px 0 8px;'>{category}</h4>",
                    unsafe_allow_html=True)
        for q, a in qa_list:
            with st.expander(q):
                st.markdown(f'<div class="faq-answer">{a}</div>', unsafe_allow_html=True)
                if st.button(f"💬 Hỏi thêm về: {q[:40]}...", key=f"faq_{hash(q)}"):
                    st.session_state.prefill_chat = q
                    st.rerun()
        st.divider()


# ════════════════════════════════════════════════════════════════════════════════
# TAB 5 · THỐNG KÊ
# ════════════════════════════════════════════════════════════════════════════════
with tab_stats:
    if st.button("🔄 Tải dữ liệu thống kê", type="primary"):
        col_prof, col_cache = st.columns(2)

        resp_prof = api_get("/learning/profile", timeout=10)
        if resp_prof and resp_prof.ok:
            p = resp_prof.json()
            with col_prof:
                st.markdown("<h4 style='color:#94A3B8'>👤 Hồ sơ cá nhân</h4>", unsafe_allow_html=True)
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Tổng câu hỏi",  p.get("total_questions", 0))
                m2.metric("Phản hồi",       p.get("total_feedback", 0))
                m3.metric("Chủ đề mạnh",    len(p.get("strong_topics", [])))
                m4.metric("Cần cải thiện",  len(p.get("weak_topics", [])))

                topics = p.get("all_topics", [])
                if topics:
                    st.markdown("<br>", unsafe_allow_html=True)
                    for t in topics:
                        pct = round(t["mastery_score"] * 100)
                        ico = "💪" if pct >= 60 else ("⚠️" if pct < 40 else "📌")
                        st.metric(f"{ico} {t['topic']}", f"{pct}%", f"{t['total_questions']} câu")
                else:
                    st.info("Chưa có dữ liệu. Hãy chat và bấm 👍/👎!")

        resp_cache = api_get("/cache-stats", timeout=5)
        if resp_cache and resp_cache.ok:
            cs = resp_cache.json()
            with col_cache:
                st.markdown("<h4 style='color:#94A3B8'>⚡ Cache Performance</h4>", unsafe_allow_html=True)
                ac = cs.get("agent_cache", {})
                rc = cs.get("rag_cache", {})
                cc1, cc2 = st.columns(2)
                cc1.metric("Agent Cache",  f"{ac.get('size',0)}/{ac.get('maxsize',0)}")
                cc2.metric("Hit Rate",     ac.get("hit_rate", "N/A"))
                cc1.metric("RAG Cache",    f"{rc.get('size',0)}/{rc.get('maxsize',0)}")
                cc2.metric("RAG Hits",     rc.get("hit_rate", "N/A"))

        resp_stats = api_get("/learning/stats", timeout=10)
        if resp_stats and resp_stats.ok:
            s = resp_stats.json()
            st.divider()
            st.markdown("<h4 style='color:#94A3B8'>🌐 Thống kê toàn hệ thống</h4>", unsafe_allow_html=True)
            sc1, sc2, sc3 = st.columns(3)
            sc1.metric("Tổng câu hỏi",    s.get("total_questions", 0))
            sc2.metric("Tỉ lệ hài lòng",  s.get("satisfaction_rate", "N/A"))
            top = s.get("top_topics", [])
            sc3.metric("Chủ đề phổ biến", top[0]["topic"] if top else "N/A")

        if not (resp_prof or resp_stats):
            st.error("Không kết nối được backend.")
    else:
        st.markdown("""
        <div class="info-strip" style="margin-top:12px;">
            📊 Nhấn nút bên trên để tải dữ liệu thống kê hệ thống và phân tích chủ đề.
        </div>
        """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════════
# TAB 6 · UPLOAD TÀI LIỆU
# ════════════════════════════════════════════════════════════════════════════════
with tab_docs:
    st.markdown("""
    <div class="info-strip">
        📁 Upload tài liệu PDF/TXT/DOCX để Bot học thêm kiến thức GTCC chuyên sâu.
    </div>
    """, unsafe_allow_html=True)

    uploaded = st.file_uploader(
        "Chọn tài liệu GTCC",
        type=["pdf", "txt", "docx"],
        help="Hỗ trợ: PDF · TXT · DOCX (tối đa 50MB)",
    )

    if uploaded:
        uc1, uc2 = st.columns([3, 1])
        with uc1:
            st.markdown(f"""
            <div class="route-card" style="padding:12px 16px;">
                <span style="color:#7DD3FC;font-weight:600;">📄 {uploaded.name}</span>
                <span style="color:rgba(148,163,184,0.5);font-size:0.8rem;margin-left:10px;">{uploaded.size/1024:.1f} KB</span>
            </div>
            """, unsafe_allow_html=True)
        with uc2:
            if st.button("⚙️ Index ngay", type="primary", use_container_width=True):
                with st.spinner("Đang xử lý..."):
                    try:
                        h = {k: v for k, v in auth_headers().items() if k != "Content-Type"}
                        resp = requests.post(
                            f"{BASE_URL}/documents/upload/",
                            files={"file": (uploaded.name, uploaded.getvalue(), "application/octet-stream")},
                            headers=h, timeout=120,
                        )
                        if resp.ok:
                            st.success(resp.json().get("message", "✅ Thành công!"))
                            st.balloons()
                        else:
                            try:    detail = resp.json().get("detail", resp.text)
                            except: detail = resp.text
                            st.error(f"Lỗi: {detail}")
                    except Exception as e:
                        st.error(f"Lỗi: {e}")

    st.divider()
    st.markdown("<h4 style='color:#94A3B8;margin-bottom:10px;'>📋 Tài liệu đã upload</h4>",
                unsafe_allow_html=True)
    if st.button("🔄 Tải danh sách"):
        resp = api_get("/documents/list/", timeout=10)
        if resp and resp.ok:
            docs = resp.json()
            if docs:
                for d in docs:
                    dc1, dc2, dc3 = st.columns([4, 2, 1])
                    with dc1:
                        st.markdown(f"<span style='color:#CBD5E1;font-size:0.88rem;'>📄 <b>{d['filename']}</b></span>",
                                    unsafe_allow_html=True)
                    with dc2:
                        st.caption(str(d.get("created_at", ""))[:10])
                    with dc3:
                        if st.button("🗑️", key=f"del_{d['id']}"):
                            try:
                                r = requests.delete(
                                    f"{BASE_URL}/documents/delete/{d['id']}",
                                    headers=auth_headers(), timeout=10,
                                )
                                if r.ok:
                                    st.toast("Đã xóa", icon="✅")
                                    st.rerun()
                            except Exception as e:
                                st.error(f"Lỗi xóa: {e}")
            else:
                st.info("Chưa có tài liệu nào. Upload file GTCC để bắt đầu!")
        else:
            st.error("Không kết nối được backend.")
