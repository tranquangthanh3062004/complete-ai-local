"""
Streamlit Frontend v3.0 — CompleteAI
Tính năng mới: Model selector, Temperature slider, Gợi ý câu hỏi,
Xuất chat, Xóa tài liệu, Đoạn trích nguồn, Copy button.
"""
import streamlit as st
import requests
import plotly.graph_objects as go
import json
import uuid
import os
from datetime import datetime

BASE_URL = "http://localhost:8000"

st.set_page_config(
    page_title="CompleteAI v3 - Trợ Lý AI Cục Bộ",
    page_icon="🤖",
    layout="wide",
)

# ─── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background: #0f0f1a; }
    .main-header {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        padding: 20px 28px; border-radius: 14px; margin-bottom: 20px;
        border: 1px solid #e94560;
        box-shadow: 0 4px 24px rgba(233,69,96,0.15);
    }
    .metric-card {
        background: #1a1a2e; border-radius: 10px; padding: 15px;
        border: 1px solid #0f3460; text-align: center;
    }
    .suggestion-btn {
        background: #16213e; border: 1px solid #0f3460;
        border-radius: 8px; padding: 6px 12px;
        color: #a8b2d8; font-size: 13px; cursor: pointer;
        margin: 3px; display: inline-block;
    }
    .source-chip {
        display: inline-block; padding: 2px 10px; border-radius: 20px;
        font-size: 11px; margin: 2px;
        background: #0f3460; color: #a8b2d8; border: 1px solid #1a4a8a;
    }
    .excerpt-box {
        background: #12122a; border-left: 3px solid #e94560;
        padding: 8px 12px; border-radius: 0 6px 6px 0;
        font-size: 12px; color: #8892b0; margin: 4px 0;
    }
    .stTabs [data-baseweb="tab"] { color: #a8b2d8; }
    .stTabs [aria-selected="true"] { color: #e94560; border-bottom-color: #e94560; }
</style>
""", unsafe_allow_html=True)


# ─── Session State ────────────────────────────────────────────────────────────
defaults = {
    "session_id"   : str(uuid.uuid4())[:8],
    "messages"     : [],
    "rag_messages" : [],
    "token"        : None,
    "username"     : None,
    "model_list"   : [],
    "selected_model": None,
    "temperature"  : 0.1,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


def headers():
    h = {"Content-Type": "application/json"}
    if st.session_state.token:
        h["Authorization"] = f"Bearer {st.session_state.token}"
    return h


def get_models():
    try:
        r = requests.get(f"{BASE_URL}/models", timeout=5)
        if r.ok:
            return r.json().get("models", [])
    except Exception:
        pass
    return []


# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🤖 CompleteAI v3")
    st.markdown("*Trợ lý AI hoàn toàn cục bộ*")
    st.divider()

    # Đăng nhập
    if st.session_state.token is None:
        st.subheader("🔐 Đăng nhập")
        email = st.text_input("Email", value="admin@local.com", key="login_email")
        pwd   = st.text_input("Mật khẩu", type="password", value="admin123", key="login_pass")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Đăng nhập", type="primary", use_container_width=True):
                try:
                    resp = requests.post(f"{BASE_URL}/auth/token",
                                         data={"username": email, "password": pwd}, timeout=10)
                    if resp.status_code == 200:
                        st.session_state.token    = resp.json()["access_token"]
                        st.session_state.username = email.split("@")[0]
                        st.success(f"✅ Xin chào {st.session_state.username}!")
                        st.rerun()
                    else:
                        st.error("❌ Sai email hoặc mật khẩu")
                except requests.exceptions.ConnectionError:
                    st.error("❌ Không kết nối được backend. Hệ thống đang bận hoặc chưa khởi động xong.")
                except Exception as e:
                    st.error(f"❌ Lỗi đăng nhập: {e}")
        with c2:
            if st.button("Khách", use_container_width=True):
                st.session_state.username = "Khách"
                st.rerun()
        st.caption("Mặc định: admin@local.com / admin123")
    else:
        st.success(f"👤 {st.session_state.username}")
        if st.button("🚪 Đăng xuất", use_container_width=True):
            for k in ["token", "username", "messages", "rag_messages"]:
                st.session_state[k] = [] if k in ["messages", "rag_messages"] else None
            st.rerun()

    st.divider()

    # Chọn model & temperature
    st.subheader("⚙️ Cài đặt AI")
    if st.button("🔄 Tải danh sách model", use_container_width=True):
        st.session_state.model_list = get_models()

    if st.session_state.model_list:
        st.session_state.selected_model = st.selectbox(
            "🧠 Model AI", st.session_state.model_list,
            index=0, key="model_selector"
        )
    else:
        st.caption("Bấm nút trên để tải model")

    st.session_state.temperature = st.slider(
        "🎨 Sáng tạo (Temperature)",
        min_value=0.0, max_value=1.0,
        value=st.session_state.temperature, step=0.05,
        help="0 = chính xác, 1 = sáng tạo"
    )

    st.divider()

    # Kiểm tra kết nối
    st.subheader("📡 Trạng thái")
    if st.button("🔄 Kiểm tra kết nối", use_container_width=True):
        try:
            resp = requests.get(f"{BASE_URL}/health", timeout=5)
            if resp.ok:
                data = resp.json()
                if data.get("ollama_online"):
                    models = data.get("ollama_models", [])
                    st.success(f"✅ Ollama online ({data.get('ollama_latency','?')})")
                    if models:
                        st.info(f"Models: {', '.join(models)}")
                else:
                    st.warning("⚠️ Ollama offline\n`ollama serve`")
            else:
                st.error("❌ Backend offline")
        except Exception:
            st.error("❌ Không kết nối được backend")

    st.caption(f"Session: `{st.session_state.session_id}`")


# ─── Header ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1 style="color:#e94560;margin:0">🤖 CompleteAI v3.0</h1>
    <p style="color:#a8b2d8;margin:5px 0 0 0">Trợ lý AI cục bộ — Không cần internet · Không hết API · Bảo mật tuyệt đối</p>
</div>
""", unsafe_allow_html=True)


# ─── Tabs ─────────────────────────────────────────────────────────────────────
tab_chat, tab_rag, tab_analytics, tab_docs = st.tabs([
    "💬 Chat Trực Tiếp",
    "📚 RAG - Hỏi Tài Liệu",
    "📊 Phân Tích Học Tập",
    "📁 Quản Lý Tài Liệu",
])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1: CHAT TRỰC TIẾP
# ══════════════════════════════════════════════════════════════════════════════
with tab_chat:
    st.subheader("💬 Chat trực tiếp với Ollama")

    # Lịch sử
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant":
                ev_id = msg.get("event_id")
                c1, c2, c3, c4 = st.columns([1, 1, 2, 6])
                with c1:
                    if ev_id and st.button("👍", key=f"pos_{ev_id}_{msg.get('idx',0)}"):
                        r = requests.post(f"{BASE_URL}/learning/feedback",
                                          json={"event_id": ev_id, "feedback": 1},
                                          headers=headers())
                        if r.ok:
                            st.success("Cảm ơn! 🎉")
                with c2:
                    if ev_id and st.button("👎", key=f"neg_{ev_id}_{msg.get('idx',0)}"):
                        r = requests.post(f"{BASE_URL}/learning/feedback",
                                          json={"event_id": ev_id, "feedback": -1},
                                          headers=headers())
                        if r.ok:
                            st.warning("Đã ghi nhận!")
                with c3:
                    # Copy button
                    st.button("📋 Copy", key=f"copy_{ev_id}_{msg.get('idx',0)}",
                              on_click=lambda c=msg["content"]: st.write(f"```\n{c}\n```"))

            # Gợi ý câu hỏi
            if msg.get("suggestions"):
                st.markdown("**💡 Câu hỏi gợi ý:**")
                for i, sug in enumerate(msg["suggestions"]):
                    if st.button(f"→ {sug}", key=f"sug_{msg.get('event_id',0)}_{i}"):
                        st.session_state["prefill_chat"] = sug
                        st.rerun()

    # Chat input
    prefill = st.session_state.pop("prefill_chat", "")
    if prompt := st.chat_input("Hỏi AI bất cứ điều gì...", key="chat_input"):
        idx = len(st.session_state.messages)
        st.session_state.messages.append({"role": "user", "content": prompt, "idx": idx})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("🤔 Đang suy nghĩ..."):
                try:
                    resp = requests.post(
                        f"{BASE_URL}/agents/direct",
                        json={
                            "query"      : prompt,
                            "model_name" : st.session_state.selected_model,
                            "temperature": st.session_state.temperature,
                            "messages"   : st.session_state.messages[-10:],
                            "session_id" : st.session_state.session_id,
                            "suggest"    : True,
                        },
                        headers=headers(), timeout=120,
                    )
                    if resp.ok:
                        data        = resp.json()
                        answer      = data.get("result", "")
                        if not answer or not answer.strip():
                            answer = "Xin lỗi, tôi không thể trả lời câu hỏi này vào lúc này."
                        ev_id       = data.get("event_id")
                        suggestions = data.get("suggestions", [])
                        resp_ms     = data.get("response_ms", 0)
                        st.markdown(answer)
                        st.caption(f"⏱️ {resp_ms:.0f}ms · Model: {data.get('model','?')}")
                        idx2 = len(st.session_state.messages)
                        st.session_state.messages.append({
                            "role"       : "assistant",
                            "content"    : answer,
                            "event_id"   : ev_id,
                            "suggestions": suggestions,
                            "idx"        : idx2,
                        })
                    else:
                        err = resp.json().get("detail", resp.text)
                        st.error(f"❌ {err}")
                except requests.exceptions.ConnectionError:
                    st.error("❌ Không kết nối được backend. Chạy: `START.bat`")
                except requests.exceptions.Timeout:
                    st.error("⏰ Timeout — model xử lý quá lâu. Thử câu hỏi ngắn hơn.")
        st.rerun()

    col_clear, col_export = st.columns([1, 1])
    with col_clear:
        if st.button("🗑️ Xóa lịch sử", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
    with col_export:
        if st.button("💾 Xuất chat (.txt)", use_container_width=True):
            if st.session_state.messages:
                lines = []
                for m in st.session_state.messages:
                    role = "Bạn" if m["role"] == "user" else "AI"
                    lines.append(f"[{role}]\n{m['content']}\n")
                text = f"CompleteAI — Chat Export\n{'='*40}\n\n" + "\n".join(lines)
                st.download_button(
                    "⬇️ Tải file", data=text.encode("utf-8"),
                    file_name=f"chat_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                    mime="text/plain"
                )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2: RAG
# ══════════════════════════════════════════════════════════════════════════════
with tab_rag:
    st.subheader("📚 Hỏi về tài liệu đã upload")
    st.caption("AI sẽ tìm kiếm trong tài liệu của bạn để trả lời chính xác.")

    for msg in st.session_state.rag_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("topic"):
                src_html = " ".join(
                    f'<span class="source-chip">📄 {s}</span>'
                    for s in msg.get("sources", [])
                )
                st.markdown(
                    f'<span class="source-chip">🏷️ {msg["topic"]}</span> {src_html}',
                    unsafe_allow_html=True
                )
            if msg.get("excerpts"):
                with st.expander("📖 Xem đoạn trích từ tài liệu"):
                    for ex in msg["excerpts"]:
                        st.markdown(
                            f'<div class="excerpt-box">{ex}</div>',
                            unsafe_allow_html=True
                        )
            if msg["role"] == "assistant" and msg.get("event_id"):
                ev_id = msg["event_id"]
                c1, c2, _ = st.columns([1, 1, 8])
                with c1:
                    if st.button("👍", key=f"rag_pos_{ev_id}"):
                        requests.post(f"{BASE_URL}/learning/feedback",
                                      json={"event_id": ev_id, "feedback": 1},
                                      headers=headers())
                        st.success("👍")
                with c2:
                    if st.button("👎", key=f"rag_neg_{ev_id}"):
                        requests.post(f"{BASE_URL}/learning/feedback",
                                      json={"event_id": ev_id, "feedback": -1},
                                      headers=headers())
                        st.warning("👎")
            if msg.get("suggestions"):
                st.markdown("**💡 Gợi ý tiếp:**")
                for i, sug in enumerate(msg["suggestions"]):
                    if st.button(f"→ {sug}", key=f"rag_sug_{msg.get('event_id',0)}_{i}"):
                        st.session_state["prefill_rag"] = sug
                        st.rerun()

    if rag_prompt := st.chat_input("Hỏi về tài liệu...", key="rag_input"):
        st.session_state.rag_messages.append({"role": "user", "content": rag_prompt})
        with st.chat_message("user"):
            st.markdown(rag_prompt)

        with st.chat_message("assistant"):
            with st.spinner("🔍 Đang tìm trong tài liệu..."):
                try:
                    resp = requests.post(
                        f"{BASE_URL}/documents/chat/",
                        json={
                            "query"      : rag_prompt,
                            "session_id" : st.session_state.session_id,
                            "model_name" : st.session_state.selected_model,
                            "suggest"    : True,
                        },
                        headers=headers(), timeout=120,
                    )
                    if resp.ok:
                        data        = resp.json()
                        answer      = data.get("response", "")
                        if not answer or not answer.strip():
                            answer = "Xin lỗi, tôi không thể tìm thấy câu trả lời phù hợp trong tài liệu."
                        ev_id       = data.get("event_id")
                        topic       = data.get("topic", "")
                        sources     = data.get("sources", [])
                        excerpts    = data.get("excerpts", [])
                        suggestions = data.get("suggestions", [])
                        st.markdown(answer)
                        if sources:
                            st.caption(f"📄 Nguồn: {', '.join(sources)}")
                        st.session_state.rag_messages.append({
                            "role"       : "assistant",
                            "content"    : answer,
                            "event_id"   : ev_id,
                            "topic"      : topic,
                            "sources"    : sources,
                            "excerpts"   : excerpts,
                            "suggestions": suggestions,
                        })
                    else:
                        err = resp.json().get("detail", resp.text)
                        st.error(f"❌ {err}")
                except requests.exceptions.ConnectionError:
                    st.error("❌ Không kết nối được backend. Vui lòng bật hệ thống backend (START.bat).")
                except requests.exceptions.Timeout:
                    st.error("⏰ Timeout — model xử lý quá lâu.")
                except Exception as e:
                    st.error(f"❌ Lỗi RAG: {e}")
        st.rerun()

    if st.button("🗑️ Xóa lịch sử RAG"):
        st.session_state.rag_messages = []
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3: ANALYTICS
# ══════════════════════════════════════════════════════════════════════════════
with tab_analytics:
    st.subheader("📊 Phân Tích Điểm Mạnh / Điểm Yếu")

    if st.button("🔄 Tải dữ liệu phân tích", type="primary"):
        try:
            resp       = requests.get(f"{BASE_URL}/learning/profile", headers=headers(), timeout=10)
            stats_resp = requests.get(f"{BASE_URL}/learning/stats", timeout=10)

            if resp.ok:
                profile = resp.json()
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("📝 Tổng câu hỏi",  profile["total_questions"])
                col2.metric("💬 Đã phản hồi",   profile["total_feedback"])
                col3.metric("💪 Chủ đề mạnh",   len(profile["strong_topics"]))
                col4.metric("⚠️ Cần cải thiện", len(profile["weak_topics"]))
                st.divider()

                all_topics = profile.get("all_topics", [])
                if all_topics:
                    col_chart, col_list = st.columns([2, 1])
                    with col_chart:
                        st.subheader("🎯 Bản đồ năng lực")
                        topics = [t["topic"] for t in all_topics]
                        scores = [round(t["mastery_score"] * 100, 1) for t in all_topics]
                        fig = go.Figure()
                        fig.add_trace(go.Scatterpolar(
                            r=scores + [scores[0]], theta=topics + [topics[0]],
                            fill="toself", name="Điểm năng lực",
                            line=dict(color="#e94560"), fillcolor="rgba(233,69,96,0.2)",
                        ))
                        fig.update_layout(
                            polar=dict(radialaxis=dict(visible=True, range=[0, 100]),
                                       bgcolor="#1a1a2e"),
                            showlegend=False, paper_bgcolor="#0f0f1a",
                            font_color="#a8b2d8",
                            margin=dict(l=40, r=40, t=40, b=40),
                        )
                        st.plotly_chart(fig, use_container_width=True)

                    with col_list:
                        st.subheader("📋 Chi tiết")
                        for t in all_topics:
                            score_pct = round(t["mastery_score"] * 100)
                            icon  = "💪" if score_pct >= 60 else ("⚠️" if score_pct < 40 else "📌")
                            color = "normal" if score_pct >= 60 else ("inverse" if score_pct < 40 else "off")
                            st.metric(
                                label=f"{icon} {t['topic'].capitalize()}",
                                value=f"{score_pct}%",
                                delta=f"{t['total_questions']} câu hỏi",
                                delta_color=color,
                            )

                    st.subheader("📈 Số câu hỏi theo chủ đề")
                    fig2 = go.Figure(go.Bar(
                        x=[t["topic"] for t in all_topics],
                        y=[t["total_questions"] for t in all_topics],
                        marker_color=[
                            "#00ff88" if t["mastery_score"] >= 0.6
                            else "#ff6b6b" if t["mastery_score"] < 0.4 else "#f39c12"
                            for t in all_topics
                        ],
                        text=[t["total_questions"] for t in all_topics],
                        textposition="outside",
                    ))
                    fig2.update_layout(
                        paper_bgcolor="#0f0f1a", plot_bgcolor="#1a1a2e",
                        font_color="#a8b2d8",
                        xaxis=dict(gridcolor="#0f3460"),
                        yaxis=dict(gridcolor="#0f3460"),
                        margin=dict(l=20, r=20, t=20, b=20),
                    )
                    st.plotly_chart(fig2, use_container_width=True)
                else:
                    st.info("💡 Chưa có dữ liệu. Hãy chat và bấm 👍/👎 để xây dựng hồ sơ!")

                st.divider()
                st.subheader("🕐 5 câu hỏi gần nhất")
                for q in profile.get("recent_questions", []):
                    fb = "👍" if q["feedback"] == 1 else ("👎" if q["feedback"] == -1 else "⬜")
                    st.markdown(f"{fb} **[{q['topic']}]** {q['question']}")

            if stats_resp.ok:
                st.divider()
                st.subheader("🌐 Thống kê toàn hệ thống")
                s = stats_resp.json()
                c1, c2, c3 = st.columns(3)
                c1.metric("Tổng câu hỏi",   s["total_questions"])
                c2.metric("Tỉ lệ hài lòng", s["satisfaction_rate"])
                c3.metric("Chủ đề phổ biến",
                          s["top_topics"][0]["topic"] if s["top_topics"] else "N/A")

        except requests.exceptions.ConnectionError:
            st.error("❌ Không kết nối được backend")
    else:
        st.info("👆 Bấm 'Tải dữ liệu phân tích' để xem hồ sơ học tập")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4: QUẢN LÝ TÀI LIỆU
# ══════════════════════════════════════════════════════════════════════════════
with tab_docs:
    st.subheader("📁 Quản Lý Tài Liệu")

    st.markdown("### ⬆️ Upload tài liệu mới")
    st.caption("Hỗ trợ: **PDF**, **TXT**, **DOCX**")

    uploaded = st.file_uploader(
        "Kéo thả hoặc chọn file",
        type=["pdf", "txt", "docx"],
        help="Tài liệu sẽ được chia nhỏ và lưu vào ChromaDB"
    )

    if uploaded:
        col1, col2 = st.columns([2, 1])
        with col1:
            st.info(f"📄 **{uploaded.name}** — {uploaded.size/1024:.1f} KB")
        with col2:
            if st.button("🚀 Xử lý & Index", type="primary", use_container_width=True):
                with st.spinner("⚙️ Đang đọc và index..."):
                    try:
                        resp = requests.post(
                            f"{BASE_URL}/documents/upload/",
                            files={"file": (uploaded.name, uploaded.getvalue(),
                                            "application/octet-stream")},
                            headers={k: v for k, v in headers().items()
                                     if k != "Content-Type"},
                            timeout=120,
                        )
                        if resp.ok:
                            data = resp.json()
                            st.success(data.get("message", "✅ Thành công!"))
                            st.balloons()
                            st.json({
                                "Số đoạn": data.get("chunks"),
                                "Số trang": data.get("pages"),
                                "Kích thước": f"{data.get('size_mb', 0):.2f} MB",
                            })
                        else:
                            err = resp.json().get("detail", resp.text)
                            st.error(f"❌ {err}")
                    except requests.exceptions.ConnectionError:
                        st.error("❌ Không kết nối được backend.")
                    except requests.exceptions.Timeout:
                        st.error("⏰ Timeout — xử lý tài liệu quá lâu.")
                    except Exception as e:
                        st.error(f"❌ Lỗi: {e}")

    st.divider()
    st.markdown("### 📋 Tài liệu đã upload")
    if st.button("🔄 Tải danh sách", use_container_width=False):
        try:
            resp = requests.get(f"{BASE_URL}/documents/list/", headers=headers(), timeout=10)
            if resp.ok:
                docs = resp.json()
                if docs:
                    for d in docs:
                        col1, col2, col3 = st.columns([4, 2, 1])
                        with col1:
                            st.markdown(f"📄 **{d['filename']}**")
                        with col2:
                            st.caption(d["created_at"][:10])
                        with col3:
                            if st.button("🗑️", key=f"del_{d['id']}",
                                         help=f"Xóa {d['filename']}"):
                                try:
                                    r = requests.delete(
                                        f"{BASE_URL}/documents/delete/{d['id']}",
                                        headers=headers(), timeout=10,
                                    )
                                    if r.ok:
                                        st.success(r.json().get("message", "Đã xóa"))
                                        st.rerun()
                                except requests.exceptions.ConnectionError:
                                    st.error("❌ Mất kết nối backend khi xóa.")
                                except Exception as e:
                                    st.error(f"❌ Lỗi xóa: {e}")
                else:
                    st.info("Chưa có tài liệu nào. Hãy upload file!")
            else:
                st.error("Lỗi tải danh sách")
        except requests.exceptions.ConnectionError:
            st.error("❌ Không kết nối được backend.")
        except Exception as e:
            st.error(f"❌ Lỗi: {e}")
