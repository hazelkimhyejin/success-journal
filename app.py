import streamlit as st
import pandas as pd
from datetime import date, datetime
import gspread
from google.oauth2.service_account import Credentials
import json
import plotly.graph_objects as go
import plotly.express as px

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Daily Success Journal",
    page_icon="📓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500;700&family=DM+Sans:wght@300;400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

h1, h2, h3 {
    font-family: 'Playfair Display', serif !important;
    font-weight: 500 !important;
}

.section-header {
    font-family: 'Playfair Display', serif;
    font-size: 1.3rem;
    font-weight: 500;
    margin-top: 1.5rem;
    margin-bottom: 0.2rem;
    color: #1a1a1a;
}

.section-sub {
    font-size: 0.82rem;
    color: #888;
    font-style: italic;
    margin-bottom: 1rem;
}

.tag {
    display: inline-block;
    font-size: 0.65rem;
    font-weight: 600;
    padding: 2px 10px;
    border-radius: 20px;
    margin-left: 8px;
    vertical-align: middle;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

.tag-am  { background: #FAEEDA; color: #854F0B; }
.tag-pm  { background: #EEEDFE; color: #3C3489; }
.tag-think { background: #E1F5EE; color: #0F6E56; }

.quote-block {
    border-left: 3px solid #ddd;
    padding: 0.75rem 1.2rem;
    background: #fafafa;
    border-radius: 0 8px 8px 0;
    margin-bottom: 1.5rem;
    font-family: 'Playfair Display', serif;
    font-style: italic;
    font-size: 0.95rem;
    color: #555;
}

.quote-attr {
    font-size: 0.75rem;
    color: #aaa;
    margin-top: 4px;
    font-family: 'DM Sans', sans-serif;
    font-style: normal;
}

.metric-card {
    background: #f7f7f5;
    border-radius: 10px;
    padding: 1rem 1.25rem;
    text-align: center;
}

.saved-banner {
    background: #E1F5EE;
    color: #0F6E56;
    padding: 0.75rem 1rem;
    border-radius: 8px;
    font-weight: 500;
    margin-top: 1rem;
}

div[data-testid="stSidebar"] {
    background: #fafaf8;
}

.stTextArea textarea {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.88rem;
}

.stSlider > div { padding-top: 0.25rem; }

hr { border-color: #eee; margin: 1.5rem 0; }
</style>
""", unsafe_allow_html=True)

# ── Quotes ────────────────────────────────────────────────────────────────────
QUOTES = [
    ("I don't want to be defined by one thing. I want to be the best version of myself in everything I do.", "Eileen Gu"),
    ("The first rule of compounding: never interrupt it unnecessarily.", "Charlie Munger"),
    ("You do not rise to the level of your goals. You fall to the level of your systems.", "James Clear"),
    ("The most important investment you can make is in yourself.", "Warren Buffett"),
    ("It's not what you do once in a while. It's what you do day in and day out that makes the difference.", "Jenny Craig"),
    ("Metacognition is the skill of watching your own mind think. Master it and you master everything.", "John Flavell"),
    ("An investment in knowledge pays the best interest.", "Benjamin Franklin"),
    ("Do not save what is left after spending; instead spend what is left after saving.", "Warren Buffett"),
]

# ── Google Sheets connection ──────────────────────────────────────────────────
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

COLUMNS = [
    "date", "identity", "non_negotiable", "priority_1", "priority_2", "priority_3",
    "weekly_focus", "fear_facing", "mental_model", "lying_to_myself",
    "assumption_testing", "skill_practicing", "value_created", "asset_building",
    "financial_insight", "deep_work_hours", "amount_invested",
    "habits_checked", "wins", "what_drained", "mistake", "insight",
    "avoided_conversation", "letter_to_future",
    "score_focus", "score_energy", "score_alignment", "score_progress", "score_mindset",
    "total_score"
]

@st.cache_resource
def get_sheet():
    try:
        creds_dict = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        client = gspread.authorize(creds)
        sheet_id = st.secrets["google_sheet_id"]
        sh = client.open_by_key(sheet_id)
        worksheet = sh.sheet1
        # Ensure header row exists
        existing = worksheet.row_values(1)
        if not existing or existing[0] != "date":
            worksheet.update([COLUMNS], "A1")
        return worksheet
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

# ── Sidebar navigation ────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📓 Success Journal")
    st.markdown("---")
    page = st.radio(
        "Navigate",
        ["Today's Entry", "Past Entries", "Progress Dashboard"],
        label_visibility="collapsed"
    )
    st.markdown("---")
    today_date = date.today()
    st.markdown(f"**{today_date.strftime('%A, %B %d %Y')}**")

    idx = today_date.weekday()
    quote_text, quote_attr = QUOTES[idx % len(QUOTES)]
    st.markdown(f"""
    <div style="font-family:'Playfair Display',serif;font-style:italic;font-size:0.8rem;color:#777;margin-top:1rem;line-height:1.5;">
    "{quote_text}"<br>
    <span style="font-size:0.7rem;color:#aaa;font-style:normal;">— {quote_attr}</span>
    </div>
    """, unsafe_allow_html=True)

# ── Load sheet ────────────────────────────────────────────────────────────────
ws = get_sheet()

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: TODAY'S ENTRY
# ═══════════════════════════════════════════════════════════════════════════════
if page == "Today's Entry":
    st.markdown("# Daily Success Journal")
    st.markdown(f"*{today_date.strftime('%A, %B %d, %Y')}*")
    st.markdown("---")

    # ── MORNING ──────────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">Intention & Identity <span class="tag tag-am">Morning</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Eileen Gu trained her mind before her body. Who are you becoming today?</div>', unsafe_allow_html=True)

    identity = st.text_area("Who am I today? *(write as if already true)*",
        placeholder="I am a disciplined creator, a sharp thinker, and a generous builder...",
        height=80, key="identity")

    non_negotiable = st.text_area("My one non-negotiable today",
        placeholder="No matter what, I will...",
        height=70, key="non_neg")

    col1, col2, col3 = st.columns(3)
    with col1:
        p1 = st.text_input("Priority 1", placeholder="Most important task...", key="p1")
    with col2:
        p2 = st.text_input("Priority 2", placeholder="Second priority...", key="p2")
    with col3:
        p3 = st.text_input("Priority 3", placeholder="Third priority...", key="p3")

    weekly_focus = st.text_area("What am I optimizing for this week?",
        placeholder="This week I'm building / growing / learning...",
        height=70, key="weekly_focus")

    fear = st.text_area("Fear I'm choosing to face today",
        placeholder="I'm going to do the hard thing: ...",
        height=70, key="fear")

    st.markdown("---")

    # ── METACOGNITION ─────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">Mind Operating System <span class="tag tag-think">Metacognition</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Successful people think about their thinking. This is the edge most people skip.</div>', unsafe_allow_html=True)

    mental_model = st.text_area("What mental model am I applying today?",
        placeholder="e.g. First principles, inversion, second-order effects, compounding, Pareto...",
        height=70, key="mental_model")

    lying = st.text_area("Where am I lying to myself?",
        placeholder="I've been telling myself... but actually...",
        height=80, key="lying")

    assumption = st.text_area("What assumption am I testing today?",
        placeholder="I believe X, so today I'll test it by...",
        height=70, key="assumption")

    skill = st.text_area("Skill I'm deliberately practicing",
        placeholder="I'm getting 1% better at...",
        height=70, key="skill")

    st.markdown("---")

    # ── WEALTH ───────────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">Wealth Architecture</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Wealth comes from creating value at scale. What are you building that works while you sleep?</div>', unsafe_allow_html=True)

    value_created = st.text_area("Where did I create value for someone today?",
        placeholder="I created real value by...",
        height=70, key="value")

    asset = st.text_area("One asset I'm building (not just earning)",
        placeholder="Skills, audience, IP, relationships, systems, capital, reputation...",
        height=70, key="asset")

    fin_insight = st.text_area("Best financial or strategic insight this week",
        placeholder="Something I learned / noticed / connected...",
        height=70, key="fin_insight")

    c1, c2 = st.columns(2)
    with c1:
        deep_work = st.number_input("Hours of deep work today", min_value=0.0, max_value=16.0, step=0.5, key="deep_work")
    with c2:
        invested = st.text_input("Amount invested today ($)", placeholder="0", key="invested")

    st.markdown("---")

    # ── HABITS ───────────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">Non-Negotiable Habits</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">The habits elite performers do even when unmotivated.</div>', unsafe_allow_html=True)

    HABITS = [
        "Morning movement / workout",
        "Cold water / breathwork",
        "No phone first 30 mins",
        "Read 20+ pages",
        "Deep work block (2h+)",
        "Healthy nutrition",
        "Connect with a mentor/peer",
        "Evening wind-down ritual",
    ]
    cols = st.columns(2)
    checked_habits = []
    for i, h in enumerate(HABITS):
        with cols[i % 2]:
            if st.checkbox(h, key=f"habit_{i}"):
                checked_habits.append(h)

    st.markdown("---")

    # ── EVENING ──────────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">Reflection & Calibration <span class="tag tag-pm">Evening</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Charlie Munger reviewed every decision. Loop closing is how you actually improve.</div>', unsafe_allow_html=True)

    wins = st.text_area("3 wins today (however small)",
        placeholder="1.\n2.\n3.",
        height=100, key="wins")

    drained = st.text_area("What drained me today? (and why)",
        placeholder="I felt drained when... because...",
        height=80, key="drained")

    mistake = st.text_area("The mistake I'll not repeat",
        placeholder="I should have... instead I...",
        height=80, key="mistake")

    insight = st.text_area("What did I learn today that changed how I think?",
        placeholder="The insight was...",
        height=80, key="insight")

    avoided = st.text_area("The conversation I should have had (but avoided)",
        placeholder="I need to talk to ___ about...",
        height=70, key="avoided")

    future_letter = st.text_area("Letter to future me (one sentence)",
        placeholder="Dear future me, remember that...",
        height=70, key="future")

    st.markdown("---")

    # ── SCORES ───────────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">Day Rating</div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        s_focus     = st.slider("Focus",        1, 10, 5, key="s_focus")
        s_energy    = st.slider("Energy",       1, 10, 5, key="s_energy")
        s_alignment = st.slider("Alignment",    1, 10, 5, key="s_align")
    with c2:
        s_progress  = st.slider("Progress on goal", 1, 10, 5, key="s_prog")
        s_mindset   = st.slider("Mindset quality",  1, 10, 5, key="s_mind")

    total = s_focus + s_energy + s_alignment + s_progress + s_mindset
    st.markdown(f"### Total: **{total} / 50**")

    st.markdown("---")

    # ── SAVE ─────────────────────────────────────────────────────────────────
    if st.button("💾  Save Today's Entry", type="primary", use_container_width=True):
        if ws is None:
            st.error("Cannot save — Google Sheets not connected. Check your secrets setup.")
        else:
            row = {
                "date": str(today_date),
                "identity": identity,
                "non_negotiable": non_negotiable,
                "priority_1": p1,
                "priority_2": p2,
                "priority_3": p3,
                "weekly_focus": weekly_focus,
                "fear_facing": fear,
                "mental_model": mental_model,
                "lying_to_myself": lying,
                "assumption_testing": assumption,
                "skill_practicing": skill,
                "value_created": value_created,
                "asset_building": asset,
                "financial_insight": fin_insight,
                "deep_work_hours": deep_work,
                "amount_invested": invested,
                "habits_checked": ", ".join(checked_habits),
                "wins": wins,
                "what_drained": drained,
                "mistake": mistake,
                "insight": insight,
                "avoided_conversation": avoided,
                "letter_to_future": future_letter,
                "score_focus": s_focus,
                "score_energy": s_energy,
                "score_alignment": s_alignment,
                "score_progress": s_progress,
                "score_mindset": s_mindset,
                "total_score": total,
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

            selected_date = st.selectbox(
                "Select a date",
                df["date"].dt.strftime("%A, %B %d %Y").tolist()
            )
            idx = df["date"].dt.strftime("%A, %B %d %Y").tolist().index(selected_date)
            row = df.iloc[idx]

            st.markdown(f"## {selected_date}")
            st.markdown(f"**Total Score:** {row.get('total_score', '—')} / 50")
            st.markdown("---")

            def show_field(label, key):
                val = row.get(key, "")
                if val:
                    st.markdown(f"**{label}**")
                    st.markdown(f"> {val}")

            show_field("Identity", "identity")
            show_field("Non-negotiable", "non_negotiable")

            p1, p2, p3 = row.get("priority_1",""), row.get("priority_2",""), row.get("priority_3","")
            if any([p1, p2, p3]):
                st.markdown("**Top 3 Priorities**")
                for i, p in enumerate([p1, p2, p3], 1):
                    if p: st.markdown(f"> {i}. {p}")

            show_field("Weekly Focus", "weekly_focus")
            show_field("Fear Facing", "fear_facing")
            st.markdown("---")
            show_field("Mental Model", "mental_model")
            show_field("Lying to Myself", "lying_to_myself")
            show_field("Assumption Testing", "assumption_testing")
            show_field("Skill Practicing", "skill_practicing")
            st.markdown("---")
            show_field("Value Created", "value_created")
            show_field("Asset Building", "asset_building")
            show_field("Financial Insight", "financial_insight")

            habits = row.get("habits_checked", "")
            if habits:
                st.markdown("**Habits Checked**")
                for h in str(habits).split(", "):
                    if h: st.markdown(f"> ✅ {h}")
            st.markdown("---")
            show_field("Wins", "wins")
            show_field("What Drained Me", "what_drained")
            show_field("Mistake", "mistake")
            show_field("Insight", "insight")
            show_field("Avoided Conversation", "avoided_conversation")
            show_field("Letter to Future Me", "letter_to_future")

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
            st.info("Keep journaling — your dashboard will come alive after a few entries!")
        else:
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values("date")

            for col in ["score_focus","score_energy","score_alignment","score_progress","score_mindset","total_score","deep_work_hours"]:
                df[col] = pd.to_numeric(df[col], errors="coerce")

            # Summary metrics
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Entries", len(df))
            c2.metric("Avg Daily Score", f"{df['total_score'].mean():.1f} / 50")
            c3.metric("Avg Deep Work (hrs)", f"{df['deep_work_hours'].mean():.1f}")
            c4.metric("Best Day", df.loc[df['total_score'].idxmax(), 'date'].strftime("%b %d"))

            st.markdown("---")

            # Score trend
            st.markdown("### Daily Score Trend")
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df["date"], y=df["total_score"],
                mode="lines+markers",
                line=dict(color="#534AB7", width=2),
                marker=dict(size=7),
                name="Total Score"
            ))
            fig.update_layout(
                yaxis=dict(range=[0, 50], title="Score / 50"),
                xaxis_title="Date",
                height=300,
                margin=dict(l=20, r=20, t=20, b=20),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig, use_container_width=True)

            # Radar: avg scores
            st.markdown("### Dimension Averages")
            dims = ["Focus", "Energy", "Alignment", "Progress", "Mindset"]
            avgs = [
                df["score_focus"].mean(),
                df["score_energy"].mean(),
                df["score_alignment"].mean(),
                df["score_progress"].mean(),
                df["score_mindset"].mean(),
            ]
            fig2 = go.Figure(go.Scatterpolar(
                r=avgs + [avgs[0]],
                theta=dims + [dims[0]],
                fill="toself",
                line_color="#1D9E75",
                fillcolor="rgba(29,158,117,0.15)"
            ))
            fig2.update_layout(
                polar=dict(radialaxis=dict(range=[0, 10])),
                height=350,
                margin=dict(l=40, r=40, t=20, b=20),
                paper_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig2, use_container_width=True)

            # Deep work trend
            st.markdown("### Deep Work Hours")
            fig3 = px.bar(df, x="date", y="deep_work_hours",
                          color_discrete_sequence=["#AFA9EC"])
            fig3.update_layout(
                height=250,
                margin=dict(l=20, r=20, t=10, b=20),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                yaxis_title="Hours"
            )
            st.plotly_chart(fig3, use_container_width=True)
