import streamlit as st
import os
import json
import datetime
import re
import pandas as pd
from PIL import Image
from groq import Groq
from openai import OpenAI
import PyPDF2
from streamlit_gsheets import GSheetsConnection

# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION
# -----------------------------------------------------------------------------
try:
    im = Image.open("logo.png")
except:
    im = "⚛️"

st.set_page_config(
    page_title="The Molecular Man | Expert Tuition Solutions",
    page_icon=im,
    layout="wide",
    initial_sidebar_state="collapsed"
)

# -----------------------------------------------------------------------------
# 2. SESSION STATE & FILE SETUP
# -----------------------------------------------------------------------------
if 'page' not in st.session_state: st.session_state.page = "Home"
if "username" not in st.session_state: st.session_state.username = "Student"
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "is_admin" not in st.session_state: st.session_state.is_admin = False
if "aya_messages" not in st.session_state: st.session_state.aya_messages = []
if 'mt_questions' not in st.session_state: st.session_state.mt_questions = None
if 'mt_answers' not in st.session_state: st.session_state.mt_answers = {}
if 'mt_feedback' not in st.session_state: st.session_state.mt_feedback = None

NOTIFICATIONS_FILE = "notifications.json"
LIVE_STATUS_FILE = "live_status.json"

def init_files():
    if not os.path.exists(NOTIFICATIONS_FILE):
        with open(NOTIFICATIONS_FILE, "w") as f: json.dump([], f)
    if not os.path.exists(LIVE_STATUS_FILE):
        with open(LIVE_STATUS_FILE, "w") as f: json.dump({"is_live": False, "topic": "", "link": ""}, f)
init_files()

# -----------------------------------------------------------------------------
# 3. API SETUP (Initialize Once)
# -----------------------------------------------------------------------------
try:
    groq_api_key = st.secrets["GROQ_API_KEY"]
    groq_client = Groq(api_key=groq_api_key)
    openai_client = OpenAI(api_key=groq_api_key, base_url="https://api.groq.com/openai/v1")
except Exception:
    st.error("⚠️ GROQ_API_KEY not found! Please check your .streamlit/secrets.toml file.")
    st.stop()

# -----------------------------------------------------------------------------
# 4. HELPER FUNCTIONS
# -----------------------------------------------------------------------------
def login_user(username, password):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(spreadsheet="https://docs.google.com/spreadsheets/d/18o58Ot15bBL2VA4uMib_HWJWgd112e2dKuil2YwojDk/edit?usp=sharing")
        df.columns = df.columns.str.strip()
        df['username'] = df['username'].astype(str).str.strip()
        df['password'] = df['password'].astype(str).str.strip()
        
        user_row = df[df['username'] == username.strip()]
        if not user_row.empty and str(user_row.iloc[0]['password']) == password.strip():
            return True
        return False
    except Exception as e:
        st.error(f"Login Error: {e}")
        return False

def get_notifications():
    try:
        with open(NOTIFICATIONS_FILE, "r") as f: return json.load(f)
    except: return []

def add_notification(message):
    notifs = get_notifications()
    notifs.insert(0, {"date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "message": message})
    with open(NOTIFICATIONS_FILE, "w") as f: json.dump(notifs, f)

def get_live_status():
    try:
        with open(LIVE_STATUS_FILE, "r") as f: return json.load(f)
    except: return {"is_live": False, "topic": "", "link": ""}

def set_live_status(is_live, topic="", link=""):
    with open(LIVE_STATUS_FILE, "w") as f: json.dump({"is_live": is_live, "topic": topic, "link": link}, f)

def clean_json_response(raw_text):
    match = re.search(r'\[\s*\{.*?\}\s*\]', raw_text, re.DOTALL)
    if match: return match.group(0)
    return raw_text.replace("```json", "").replace("```", "").strip()

# -----------------------------------------------------------------------------
# 5. DYNAMIC THEME CSS (Light & Dark Compatible)
# -----------------------------------------------------------------------------
st.markdown("""
<style>
    /* BASE VARIABLES - Streamlit handles var(--text-color) and var(--background-color) automatically based on theme settings */
    h1, h2, h3, h4, p, span, div {
        color: var(--text-color);
    }

    /* LIGHT MODE CUSTOMIZATIONS (Default) */
    .stApp { 
        background: linear-gradient(135deg, #fdfbfb 0%, #ebedee 100%) !important; 
        background-attachment: fixed; 
    }
    div.stButton > button { 
        background: linear-gradient(90deg, #1e3a5f, #3b6b9e); 
        color: white !important; 
        border-radius: 8px; 
        border: none; 
        transition: 0.3s; 
    }
    div.stButton > button:hover { 
        transform: translateY(-2px); 
        box-shadow: 0 5px 15px rgba(30, 58, 95, 0.4); 
    }
    .theme-card { 
        background-color: #ffffff; 
        padding: 20px; 
        border-radius: 10px; 
        margin-bottom: 20px; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.05); 
        border: 1px solid #e0e0e0;
    }
    .founder-headline { 
        font-size: 2rem; 
        font-weight: 900; 
        background: linear-gradient(to right, #004e92, #000428); 
        -webkit-background-clip: text; 
        -webkit-text-fill-color: transparent; 
        text-align: center; 
        margin-bottom: 10px; 
    }
    .founder-subhead {
        text-align: center; 
        color: #004e92; 
        font-weight: bold;
    }

    /* DARK MODE OVERRIDES */
    @media (prefers-color-scheme: dark) {
        .stApp { 
            background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%) !important; 
        }
        div.stButton > button { 
            border: 1px solid rgba(255,255,255,0.2); 
        }
        div.stButton > button:hover { 
            box-shadow: 0 5px 15px rgba(0,255,255,0.2); 
            border-color: #00ffff; 
        }
        .theme-card { 
            background-color: rgba(255, 255, 255, 0.05); 
            border: 1px solid rgba(255,255,255,0.1);
            box-shadow: 0 4px 15px rgba(0,0,0,0.3); 
        }
        .founder-headline { 
            background: linear-gradient(to right, #ffffff, #a1c4fd); 
            -webkit-background-clip: text; 
            -webkit-text-fill-color: transparent; 
        }
        .founder-subhead {
            color: #ffd700; 
        }
        /* Ensure inputs look good in dark mode */
        .stTextInput>div>div>input, .stTextArea>div>div>textarea, .stSelectbox>div>div { 
            background-color: rgba(255, 255, 255, 0.05) !important; 
            color: white !important; 
            border: 1px solid rgba(255,255,255,0.2) !important; 
        }
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 6. NAVIGATION ROUTING
# -----------------------------------------------------------------------------
if not st.session_state.logged_in:
    st.markdown("<div class='founder-headline'>The Molecular Man Expert Tuition Solutions</div>", unsafe_allow_html=True)
    st.markdown("<p class='founder-subhead'>Pure Teaching Intelligence. Zero Corporate Noise.</p>", unsafe_allow_html=True)
    
    cols = st.columns(5)
    menus = ["Home", "Services", "Testimonials", "Bootcamp", "Login"]
    for i, col in enumerate(cols):
        with col:
            if st.button(menus[i], use_container_width=True, type="primary" if menus[i] == "Login" else "secondary"):
                st.session_state.page = menus[i]
                st.rerun()
    st.divider()
else:
    with st.sidebar:
        st.markdown(f"### 🎓 {st.session_state.username}")
        st.divider()
        if st.session_state.is_admin:
            if st.button("👨‍🏫 Admin Hub", use_container_width=True): st.session_state.page = "Admin"
            if st.button("🔴 Manage Live", use_container_width=True): st.session_state.page = "Live Class"
        else:
            if st.button("🎓 Dashboard", use_container_width=True): st.session_state.page = "Dashboard"
            if st.button("📚 Vault", use_container_width=True): st.session_state.page = "Vault"
            if st.button("📈 Progress", use_container_width=True): st.session_state.page = "Progress"
            if st.button("🤖 AI Suite", use_container_width=True): st.session_state.page = "AI_Menu"
            
        st.divider()
        if st.button("🔴 Live Class", use_container_width=True, type="primary"): st.session_state.page = "Live Class"
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.page = "Home"
            st.rerun()

# -----------------------------------------------------------------------------
# 7. PAGE RENDERERS
# -----------------------------------------------------------------------------

if st.session_state.page == "Home":
    st.markdown("## 📊 Our Impact")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Students Taught", "500+")
    m2.metric("Success Rate", "100%")
    m3.metric("Support", "24/7")
    m4.metric("Experience", "5+ Years")

elif st.session_state.page == "Login":
    st.markdown("## 🔐 Student Portal")
    with st.container(border=True):
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Access Campus 🚀", type="primary"):
            if login_user(u, p):
                st.session_state.logged_in = True
                st.session_state.username = u
                st.session_state.is_admin = (u == "Mohammed")
                st.session_state.page = "Admin" if st.session_state.is_admin else "Dashboard"
                st.rerun()
            else:
                st.error("❌ Invalid Credentials")

elif st.session_state.page == "Dashboard":
    st.markdown(f"# 🎓 Welcome back, {st.session_state.username}!")
    st.info("No new announcements today. Keep studying!")
    st.markdown("### ⚔️ Your Learning Stats")
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("🔥 Day Streak", "12 Days")
    s2.metric("📝 Tests Taken", "8")
    s3.metric("🧠 AyA Questions", "45")
    s4.markdown("🏆 **Badge:** *Molecule Master*")

elif st.session_state.page == "Testimonials":
    st.markdown("# 💬 Student Success Stories")
    t1, t2 = st.columns(2)
    
    def testimonial_card(text, author):
        # We now use 'theme-card' which adapts to light/dark automatically
        st.markdown(f"""
        <div class="theme-card">
            <div style="font-style:italic;">"{text}"</div>
            <div style="font-weight:bold; margin-top:10px; text-align:right;">- {author}</div>
        </div>
        """, unsafe_allow_html=True)

    with t1:
        testimonial_card("Sir's organic chemistry teaching helped me a lot!", "Pranav.S, Class 12")
        testimonial_card("Math grades improved from 60% to 95%.", "Mrs. Lakshmi, Parent")
    with t2:
        testimonial_card("Physics numericals used to scare me. Now I solve them confidently.", "Rahul M., JEE Aspirant")
        testimonial_card("The Python bootcamp was amazing!", "Divya S., College Student")

elif st.session_state.page == "Bootcamp":
    st.markdown("# 🐍 Python for Data Science & AI")
    with st.container(border=True):
        st.markdown("### Weekend Intensive Program")
        st.write("Master the most in-demand programming language.")
        st.markdown("👨‍🏫 **Instructor:** Mohammed Salmaan M")
        st.caption("Data Science & AI Expert | Founder - The Molecular Man Expert Tuition Solutions")
        st.write("")
        st.markdown("📅 **Schedule:** Saturdays & Sundays")
        st.caption("1 hour per session | Morning & Evening batches")
        st.write("")
        with st.expander("📚 Curriculum Highlights"):
            st.write("• Python Basics & Data Structures\n• NumPy & Pandas for Data Analysis\n• Data Visualization with Matplotlib\n• Introduction to Machine Learning\n• Real-world Project: Build your first AI model")
        st.link_button("📱 Enroll Now", "https://wa.me/917339315376", use_container_width=True)

elif st.session_state.page == "AI_Menu":
    st.markdown("# 🤖 The Molecular Man AI Suite")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### 🧠 AyA AI Tutor")
        st.write("Your personal 24/7 teaching assistant.")
        if st.button("Open AyA", type="primary"): st.session_state.page = "AyA_AI"; st.rerun()
    with c2:
        st.markdown("### 📝 Mock Test Generator")
        st.write("Generate unlimited targeted mock tests.")
        if st.button("Open Test Generator", type="primary"): st.session_state.page = "Mock_Test"; st.rerun()

elif st.session_state.page == "AyA_AI":
    st.markdown("## 🧠 AyA - The Molecular Man AI")
    SYSTEM_PROMPT = "You are Aya, the Lead AI Tutor at The Molecular Man Expert Tuition Solutions. Structure answers: 🧠 CONCEPT -> 🌍 CONTEXT -> ✍️ SOLUTION -> ✅ ANSWER."
    
    with st.expander("📝 Input Problem", expanded=(len(st.session_state.aya_messages) == 0)):
        user_text = st.text_area("Paste question:")
        if st.button("Ask AyA 🚀"):
            st.session_state.aya_messages = [{"role": "user", "content": f"PROBLEM:\n{user_text}"}]
            st.rerun()

    for msg in st.session_state.aya_messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

    if st.session_state.aya_messages and st.session_state.aya_messages[-1]["role"] == "user":
        with st.chat_message("assistant"):
            with st.spinner("AyA is thinking..."):
                msgs = [{"role": "system", "content": SYSTEM_PROMPT}] + st.session_state.aya_messages
                res = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=msgs, temperature=0.5)
                reply = res.choices[0].message.content
                st.markdown(reply)
                st.session_state.aya_messages.append({"role": "assistant", "content": reply})

    if user_input := st.chat_input("Ask a follow-up..."):
        st.session_state.aya_messages.append({"role": "user", "content": user_input})
        st.rerun()

elif st.session_state.page == "Mock_Test":
    st.markdown("## 📝 AI Mock Test Generator")
    
    def get_questions_json(board, cls, sub, chap, num, diff, q_type):
        prompt = f"""
        You are an Examiner for {board} Board. Subject: {sub}, Class: {cls}, Chapter: {chap}.
        Create a valid JSON list of {num} {diff} {q_type}s.
        Format MUST be exactly like this:
        [
            {{"id": 1, "question": "...", "options": ["A","B","C","D"], "correct_answer": "A", "explanation": "Why this is correct..."}}
        ]
        """
        try:
            res = openai_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )
            raw = res.choices[0].message.content
            clean = clean_json_response(raw)
            return json.loads(clean)
        except Exception as e:
            st.error(f"Generation Error. Please try again.")
            return None

    if not st.session_state.mt_questions:
        with st.container(border=True):
            c1, c2 = st.columns(2)
            with c1:
                board = st.selectbox("Board", ["CBSE", "ICSE", "State"])
                cls = st.selectbox("Class", ["9", "10", "11", "12"])
                diff = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"])
            with c2:
                sub = st.text_input("Subject", "Chemistry")
                chap = st.text_input("Chapter", "Chemical Bonding")
                num = st.slider("Questions", 3, 10, 5)

        if st.button("🚀 Generate Test", type="primary"):
            with st.spinner("AyA is drafting the paper..."):
                st.session_state.mt_questions = get_questions_json(board, cls, sub, chap, num, diff, "MCQ")
                st.session_state.mt_answers = {}
                st.session_state.mt_feedback = None
                st.rerun()
    else:
        if st.session_state.mt_feedback:
            st.success("Test Complete! Here is your analysis:")
            st.markdown(st.session_state.mt_feedback)
            if st.button("🔄 Start New Test"):
                st.session_state.mt_questions = None
                st.rerun()
        else:
            with st.form("exam_form"):
                for q in st.session_state.mt_questions:
                    st.markdown(f"**Q{q['id']}. {q['question']}**")
                    st.radio("Choose:", q.get('options', []), key=f"q_{q['id']}", index=None)
                    st.divider()
                if st.form_submit_button("✅ Submit Exam"):
                    score = 0
                    feedback_text = ""
                    for q in st.session_state.mt_questions:
                        user_ans = st.session_state.get(f"q_{q['id']}")
                        if user_ans == q['correct_answer']:
                            score += 1
                            feedback_text += f"✅ **Q{q['id']}: Correct!** {q.get('explanation', '')}\n\n"
                        else:
                            feedback_text += f"❌ **Q{q['id']}: Incorrect.** The right answer was **{q['correct_answer']}**. \n*Why:* {q.get('explanation', '')}\n\n"
                    
                    st.session_state.mt_feedback = f"### Final Score: {score}/{len(st.session_state.mt_questions)}\n\n---\n{feedback_text}"
                    st.rerun()
