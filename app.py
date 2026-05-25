import streamlit as st
import pandas as pd
from datetime import date, datetime
import gspread
from google.oauth2.service_account import Credentials
import json
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(
    page_title="Daily Success Journal",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,500;0,700;1,400&family=DM+Sans:wght@300;400;500&display=swap');

/* ── Canvas & stars ── */
#stars-canvas {
    position: fixed;
    top: 0; left: 0;
    width: 100vw; height: 100vh;
    pointer-events: none;
    z-index: 0;
}

/* ── Global dark purple background ── */
html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
    background: #0d0b1e !important;
}

[data-testid="stAppViewContainer"] > .main {
    background: transparent !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #13103a !important;
    border-right: 1px solid rgba(175,169,236,0.15) !important;
}
[data-testid="stSidebar"] * { color: #c8c3f0 !important; }
[data-testid="stSidebar"] .stRadio label { color: #c8c3f0 !important; }

/* ── All text ── */
html, body, p, div, span, label, .stMarkdown, .stText {
    font-family: 'DM Sans', sans-serif !important;
    color: #e8e4ff !important;
}

h1, h2, h3 {
    font-family: 'Playfair Display', serif !important;
    font-weight: 500 !important;
    color: #f0eeff !important;
}

/* ── Inputs & textareas ── */
.stTextInput input, .stTextArea textarea, .stNumberInput input {
    background: rgba(83,74,183,0.18) !important;
    border: 1px solid rgba(175,169,236,0.3) !important;
    border-radius: 8px !important;
    color: #f0eeff !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.88rem !important;
}

.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: rgba(175,169,236,0.7) !important;
    box-shadow: 0 0 0 2px rgba(175,169,236,0.15) !important;
}

.stTextInput input::placeholder, .stTextArea textarea::placeholder {
    color: rgba(200,195,240,0.4) !important;
    font-style: italic !important;
}

/* ── Checkboxes ── */
.stCheckbox label { color: #c8c3f0 !important; }
.stCheckbox span { color: #c8c3f0 !important; }

/* ── Sliders ── */
.stSlider label { color: #c8c3f0 !important; }
.stSlider [data-testid="stThumbValue"] { color: #f0eeff !important; }

/* ── Buttons ── */
.stButton button {
    background: linear-gradient(135deg, #534AB7, #7F77DD) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    letter-spacing: 0.02em !important;
}
.stButton button:hover {
    background: linear-gradient(135deg, #6259c5, #9990e8) !important;
    transform: translateY(-1px) !important;
}

/* ── Metrics ── */
[data-testid="stMetric"] {
    background: rgba(83,74,183,0.2) !important;
    border: 1px solid rgba(175,169,236,0.2) !important;
    border-radius: 10px !important;
    padding: 1rem !important;
}
[data-testid="stMetricLabel"] { color: #a09ccc !important; }
[data-testid="stMetricValue"] { color: #f0eeff !important; }

/* ── Selectbox ── */
.stSelectbox div[data-baseweb="select"] > div {
    background: rgba(83,74,183,0.18) !important;
    border-color: rgba(175,169,236,0.3) !important;
    color: #f0eeff !important;
}

/* ── Divider ── */
hr { border-color: rgba(175,169,236,0.2) !important; }

/* ── Number input buttons ── */
.stNumberInput button {
    background: rgba(83,74,183,0.3) !important;
    border-color: rgba(175,169,236,0.3) !important;
    color: #f0eeff !important;
}

/* ── Success/error boxes ── */
.stSuccess { background: rgba(29,158,117,0.2) !important; border-color: #1D9E75 !important; }
.stError   { background: rgba(226,75,74,0.2)  !important; border-color: #E24B4A !important; }
.stInfo    { background: rgba(83,74,183,0.2)  !important; border-color: #534AB7 !important; }

/* ── Custom section styles ── */
.section-header {
    font-family: 'Playfair Display', serif;
    font-size: 1.25rem;
    font-weight: 500;
    margin-top: 1.5rem;
    margin-bottom: 0.2rem;
    color: #f0eeff;
}
.section-sub {
    font-size: 0.82rem;
    color: #8a84c0;
    font-style: italic;
    margin-bottom: 1rem;
}
.tag {
    display: inline-block;
    font-size: 0.62rem;
    font-weight: 600;
    padding: 2px 10px;
    border-radius: 20px;
    margin-left: 8px;
    vertical-align: middle;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}
.tag-am    { background: rgba(250,174,120,0.2); color: #FAC775; }
.tag-pm    { background: rgba(175,169,236,0.2); color: #AFA9EC; }
.tag-think { background: rgba(29,158,117,0.2);  color: #5DCAA5; }

.quote-block {
    border-left: 3px solid rgba(175,169,236,0.5);
    padding: 0.75rem 1.2rem;
    background: rgba(83,74,183,0.15);
    border-radius: 0 8px 8px 0;
    margin-bottom: 1.5rem;
}
.quote-text {
    font-family: 'Playfair Display', serif;
    font-style: italic;
    font-size: 0.95rem;
    color: #c8c3f0;
    line-height: 1.6;
}
.quote-attr {
    font-size: 0.72rem;
    color: #6e6a9e;
    margin-top: 6px;
}
</style>

<canvas id="stars-canvas"></canvas>

<script>
(function() {
    const canvas = document.getElementById('stars-canvas');
    const ctx = canvas.getContext('2d');
    let W, H, stars = [];

    function resize() {
        W = canvas.width  = window.innerWidth;
        H = canvas.height = window.innerHeight;
    }

    function init() {
        resize();
        stars = Array.from({length: 120}, () => ({
            x: Math.random() * W,
            y: Math.random() * H,
            r: Math.random() * 1.8 + 0.4,
            speed: Math.random() * 0.6 + 0.2,
            drift: (Math.random() - 0.5) * 0.4,
            alpha: Math.random() * 0.7 + 0.3,
            twinkle: Math.random() * Math.PI * 2,
            twinkleSpeed: Math.random() * 0.03 + 0.01,
        }));
    }

    function draw() {
        ctx.clearRect(0, 0, W, H);
        stars.forEach(s => {
            s.twinkle += s.twinkleSpeed;
            const a = s.alpha * (0.6 + 0.4 * Math.sin(s.twinkle));
            ctx.beginPath();
            ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(200, 190, 255, ${a})`;
            ctx.fill();

            // tiny sparkle cross
            if (s.r > 1.4) {
                ctx.strokeStyle = `rgba(220, 215, 255, ${a * 0.6})`;
                ctx.lineWidth = 0.5;
                ctx.beginPath();
                ctx.moveTo(s.x - s.r * 2.5, s.y);
                ctx.lineTo(s.x + s.r * 2.5, s.y);
                ctx.moveTo(s.x, s.y - s.r * 2.5);
                ctx.lineTo(s.x, s.y + s.r * 2.5);
                ctx.stroke();
            }

            s.y += s.speed;
            s.x += s.drift;
            if (s.y > H + 5) { s.y = -5; s.x = Math.random() * W; }
            if (s.x > W + 5) s.x = -5;
            if (s.x < -5)    s.x = W + 5;
        });
        requestAnimationFrame(draw);
    }

    window.addEventListener('resize', resize);
    init();
    draw();
})();
</script>
""", unsafe_allow_html=True)

# ── Quotes ────────────────────────────────────────────────────────────────────
QUOTES = [
    ("I don't want to be defined by one thing. I want to be the best version of myself in everything I do.", "Eileen Gu"),
    ("The first rule of compounding: never interrupt it unnecessarily.", "Charlie Munger"),
    ("You do not rise to the level of your goals. You fall to the level of your systems.", "James Clear"),
    ("The most important investment you can make is in yourself.", "Warren Buffett"),
    ("It's not what you do once in a while — it's what you do day in and day out that makes the difference.", "Jenny Craig"),
    ("Metacognition is the skill of watching your own mind think. Master it and you master everything.", "John Flavell"),
    ("An investment in knowledge pays the best interest.", "Benjamin Franklin"),
    ("Do not save what is left after spending; instead spend what is left after saving.", "Warren Buffett"),
]

# ── Google Sheets ─────────────────────────────────────────────────────────────
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

COLUMNS = [
    "date","identity","non_negotiable","priority_1","priority_2","priority_3",
    "weekly_focus","fear_facing","mental_model","lying_to_myself",
    "assumption_testing","skill_practicing","value_created","asset_building",
    "financial_insight","deep_work_hours","amount_invested",
    "habits_checked","wins","what_drained","mistake","insight",
    "avoided_conversation","letter_to_future",
    "score_focus","score_energy","score_alignment","score_progress","score_mindset","total_score"
]

@st.cache_resource
def get_sheet():
    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        client = gspread.authorize(creds)
        sheet_id = st.secrets["google_sheet_id"]
        sh = client.open_by_key(sheet_id)
        ws = sh.sheet1
        existing = ws.row_values(1)
        if not existing or existing[0] != "date":
            ws.update([COLUMNS], "A1")
        return ws
    except Exception as e:
        st.error(f"Google Sheets connection failed: {e}")
        return None

def load_entries(ws):
    try:
        data = ws.get_all_records()
        return pd.DataFrame(data) if data else pd.DataFrame(columns=COLUMNS)
    except:
        return pd.DataFrame(columns=COLUMNS)

def save_entry(ws, row_dict):
    row = [str(row_dict.get(col, "")) for col in COLUMNS]
    ws.append_row(row)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ✨ Success Journal")
    st.markdown("---")
    page = st.radio("Navigate", ["Today's Entry", "Past Entries", "Progress Dashboard"], label_visibility="collapsed")
    st.markdown("---")
    today_date = date.today()
    st.markdown(f"**{today_date.strftime('%A, %B %d %Y')}**")
    idx = today_date.weekday()
    qt, qa = QUOTES[idx % len(QUOTES)]
    st.markdown(f"""
    <div style="font-family:'Playfair Display',serif;font-style:italic;font-size:0.78rem;color:#8a84c0;margin-top:1rem;line-height:1.6;">
    "{qt}"<br><span style="font-size:0.68rem;color:#6e6a9e;font-style:normal;">— {qa}</span>
    </div>""", unsafe_allow_html=True)

ws = get_sheet()

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: TODAY'S ENTRY
# ═══════════════════════════════════════════════════════════════════════════════
if page == "Today's Entry":
    st.markdown("# ✨ Daily Success Journal")
    st.markdown(f"*{today_date.strftime('%A, %B %d, %Y')}*")

    qt, qa = QUOTES[today_date.day % len(QUOTES)]
    st.markdown(f'<div class="quote-block"><div class="quote-text">"{qt}"</div><div class="quote-attr">— {qa}</div></div>', unsafe_allow_html=True)

    st.markdown("---")

    # MORNING
    st.markdown('<div class="section-header">Intention & Identity <span class="tag tag-am">Morning</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Eileen Gu trained her mind before her body. Who are you becoming today?</div>', unsafe_allow_html=True)

    identity        = st.text_area("Who am I today? *(write as if already true)*", placeholder="I am a disciplined creator, a sharp thinker...", height=80)
    non_negotiable  = st.text_area("My one non-negotiable today", placeholder="No matter what, I will...", height=70)

    c1, c2, c3 = st.columns(3)
    with c1: p1 = st.text_input("Priority 1", placeholder="Most important task...")
    with c2: p2 = st.text_input("Priority 2", placeholder="Second priority...")
    with c3: p3 = st.text_input("Priority 3", placeholder="Third priority...")

    weekly_focus = st.text_area("What am I optimizing for this week?", placeholder="This week I'm building / growing / learning...", height=70)
    fear         = st.text_area("Fear I'm choosing to face today", placeholder="I'm going to do the hard thing: ...", height=70)

    st.markdown("---")

    # METACOGNITION
    st.markdown('<div class="section-header">Mind Operating System <span class="tag tag-think">Metacognition</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Successful people think about their thinking. This is the edge most people skip.</div>', unsafe_allow_html=True)

    mental_model = st.text_area("What mental model am I applying today?", placeholder="e.g. First principles, inversion, second-order effects, compounding...", height=70)
    lying        = st.text_area("Where am I lying to myself?", placeholder="I've been telling myself... but actually...", height=80)
    assumption   = st.text_area("What assumption am I testing today?", placeholder="I believe X, so today I'll test it by...", height=70)
    skill        = st.text_area("Skill I'm deliberately practicing", placeholder="I'm getting 1% better at...", height=70)

    st.markdown("---")

    # WEALTH
    st.markdown('<div class="section-header">Wealth Architecture</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Wealth comes from creating value at scale. What are you building that works while you sleep?</div>', unsafe_allow_html=True)

    value_created = st.text_area("Where did I create value for someone today?", placeholder="I created real value by...", height=70)
    asset         = st.text_area("One asset I'm building (not just earning)", placeholder="Skills, audience, IP, relationships, systems, capital...", height=70)
    fin_insight   = st.text_area("Best financial or strategic insight this week", placeholder="Something I learned / noticed / connected...", height=70)

    c1, c2 = st.columns(2)
    with c1: deep_work = st.number_input("Hours of deep work today", min_value=0.0, max_value=16.0, step=0.5)
    with c2: invested  = st.text_input("Amount invested today ($)", placeholder="0")

    st.markdown("---")

    # HABITS
    st.markdown('<div class="section-header">Non-Negotiable Habits</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">The habits elite performers do even when unmotivated.</div>', unsafe_allow_html=True)

    HABITS = [
        "Morning movement / workout", "Cold water / breathwork",
        "No phone first 30 mins",     "Read 20+ pages",
        "Deep work block (2h+)",      "Healthy nutrition",
        "Connect with a mentor/peer", "Evening wind-down ritual",
    ]
    cols = st.columns(2)
    checked_habits = []
    for i, h in enumerate(HABITS):
        with cols[i % 2]:
            if st.checkbox(h, key=f"habit_{i}"):
                checked_habits.append(h)

    st.markdown("---")

    # EVENING
    st.markdown('<div class="section-header">Reflection & Calibration <span class="tag tag-pm">Evening</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Charlie Munger reviewed every decision. Loop closing is how you actually improve.</div>', unsafe_allow_html=True)

    wins         = st.text_area("3 wins today (however small)", placeholder="1.\n2.\n3.", height=100)
    drained      = st.text_area("What drained me today? (and why)", placeholder="I felt drained when... because...", height=80)
    mistake      = st.text_area("The mistake I'll not repeat", placeholder="I should have... instead I...", height=80)
    insight      = st.text_area("What did I learn today that changed how I think?", placeholder="The insight was...", height=80)
    avoided      = st.text_area("The conversation I should have had (but avoided)", placeholder="I need to talk to ___ about...", height=70)
    future_letter= st.text_area("Letter to future me (one sentence)", placeholder="Dear future me, remember that...", height=70)

    st.markdown("---")

    # SCORES
    st.markdown('<div class="section-header">Day Rating</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        s_focus     = st.slider("Focus",         1, 10, 5)
        s_energy    = st.slider("Energy",        1, 10, 5)
        s_alignment = st.slider("Alignment",     1, 10, 5)
    with c2:
        s_progress  = st.slider("Progress on goal", 1, 10, 5)
        s_mindset   = st.slider("Mindset quality",  1, 10, 5)

    total = s_focus + s_energy + s_alignment + s_progress + s_mindset
    st.markdown(f"### ✨ Total: **{total} / 50**")
    st.markdown("---")

    if st.button("💾  Save Today's Entry", type="primary", use_container_width=True):
        if ws is None:
            st.error("Cannot save — Google Sheets not connected. Check your secrets setup.")
        else:
            row = {
                "date": str(today_date), "identity": identity,
                "non_negotiable": non_negotiable, "priority_1": p1,
                "priority_2": p2, "priority_3": p3,
                "weekly_focus": weekly_focus, "fear_facing": fear,
                "mental_model": mental_model, "lying_to_myself": lying,
                "assumption_testing": assumption, "skill_practicing": skill,
                "value_created": value_created, "asset_building": asset,
                "financial_insight": fin_insight, "deep_work_hours": deep_work,
                "amount_invested": invested,
                "habits_checked": ", ".join(checked_habits),
                "wins": wins, "what_drained": drained, "mistake": mistake,
                "insight": insight, "avoided_conversation": avoided,
                "letter_to_future": future_letter,
                "score_focus": s_focus, "score_energy": s_energy,
                "score_alignment": s_alignment, "score_progress": s_progress,
                "score_mindset": s_mindset, "total_score": total,
            }
            save_entry(ws, row)
            st.success("✅ Entry saved to Google Sheets!")
            st.balloons()

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: PAST ENTRIES
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "Past Entries":
    st.markdown("# Past Entries")
    st.markdown("---")
    if ws is None:
        st.error("Google Sheets not connected.")
    else:
        df = load_entries(ws)
        if df.empty:
            st.info("No entries yet. Fill in today's journal to get started!")
        else:
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values("date", ascending=False)
            selected = st.selectbox("Select a date", df["date"].dt.strftime("%A, %B %d %Y").tolist())
            idx = df["date"].dt.strftime("%A, %B %d %Y").tolist().index(selected)
            row = df.iloc[idx]

            st.markdown(f"## {selected}")
            st.markdown(f"**Total Score:** {row.get('total_score','—')} / 50")
            st.markdown("---")

            def show(label, key):
                val = row.get(key, "")
                if val:
                    st.markdown(f"**{label}**")
                    st.markdown(f"> {val}")

            show("Identity", "identity"); show("Non-negotiable", "non_negotiable")
            p1,p2,p3 = row.get("priority_1",""),row.get("priority_2",""),row.get("priority_3","")
            if any([p1,p2,p3]):
                st.markdown("**Top 3 Priorities**")
                for i,p in enumerate([p1,p2,p3],1):
                    if p: st.markdown(f"> {i}. {p}")
            show("Weekly Focus","weekly_focus"); show("Fear Facing","fear_facing")
            st.markdown("---")
            show("Mental Model","mental_model"); show("Lying to Myself","lying_to_myself")
            show("Assumption Testing","assumption_testing"); show("Skill Practicing","skill_practicing")
            st.markdown("---")
            show("Value Created","value_created"); show("Asset Building","asset_building")
            show("Financial Insight","financial_insight")
            habits = row.get("habits_checked","")
            if habits:
                st.markdown("**Habits Checked**")
                for h in str(habits).split(", "):
                    if h: st.markdown(f"> ✅ {h}")
            st.markdown("---")
            show("Wins","wins"); show("What Drained Me","what_drained")
            show("Mistake","mistake"); show("Insight","insight")
            show("Avoided Conversation","avoided_conversation"); show("Letter to Future Me","letter_to_future")

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "Progress Dashboard":
    st.markdown("# Progress Dashboard")
    st.markdown("---")
    if ws is None:
        st.error("Google Sheets not connected.")
    else:
        df = load_entries(ws)
        if df.empty or len(df) < 2:
            st.info("Keep journaling — your dashboard comes alive after a few entries!")
        else:
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values("date")
            for col in ["score_focus","score_energy","score_alignment","score_progress","score_mindset","total_score","deep_work_hours"]:
                df[col] = pd.to_numeric(df[col], errors="coerce")

            c1,c2,c3,c4 = st.columns(4)
            c1.metric("Entries", len(df))
            c2.metric("Avg Daily Score", f"{df['total_score'].mean():.1f} / 50")
            c3.metric("Avg Deep Work", f"{df['deep_work_hours'].mean():.1f} hrs")
            c4.metric("Best Day", df.loc[df['total_score'].idxmax(),'date'].strftime("%b %d"))

            st.markdown("---")
            st.markdown("### Daily Score Trend")
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df["date"], y=df["total_score"],
                mode="lines+markers",
                line=dict(color="#AFA9EC", width=2),
                marker=dict(size=7, color="#7F77DD"),
            ))
            fig.update_layout(yaxis=dict(range=[0,50],title="Score / 50",gridcolor="rgba(175,169,236,0.1)"),
                xaxis=dict(gridcolor="rgba(175,169,236,0.1)"),
                height=300, margin=dict(l=20,r=20,t=20,b=20),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(13,11,30,0.6)",
                font=dict(color="#c8c3f0"))
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("### Dimension Averages")
            dims = ["Focus","Energy","Alignment","Progress","Mindset"]
            avgs = [df["score_focus"].mean(),df["score_energy"].mean(),
                    df["score_alignment"].mean(),df["score_progress"].mean(),df["score_mindset"].mean()]
            fig2 = go.Figure(go.Scatterpolar(r=avgs+[avgs[0]], theta=dims+[dims[0]],
                fill="toself", line_color="#7F77DD", fillcolor="rgba(127,119,221,0.2)"))
            fig2.update_layout(polar=dict(radialaxis=dict(range=[0,10],gridcolor="rgba(175,169,236,0.2)"),
                angularaxis=dict(gridcolor="rgba(175,169,236,0.2)"),
                bgcolor="rgba(13,11,30,0.6)"),
                height=350, margin=dict(l=40,r=40,t=20,b=20),
                paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#c8c3f0"))
            st.plotly_chart(fig2, use_container_width=True)

            st.markdown("### Deep Work Hours")
            fig3 = px.bar(df, x="date", y="deep_work_hours", color_discrete_sequence=["#534AB7"])
            fig3.update_layout(height=250, margin=dict(l=20,r=20,t=10,b=20),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(13,11,30,0.6)",
                yaxis=dict(title="Hours", gridcolor="rgba(175,169,236,0.1)"),
                xaxis=dict(gridcolor="rgba(175,169,236,0.1)"),
                font=dict(color="#c8c3f0"))
            st.plotly_chart(fig3, use_container_width=True)
