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
import urllib.parse 

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

# API Keys
try:
    groq_api_key = st.secrets.get("GROQ_API_KEY")
    groq_client = Groq(api_key=groq_api_key)
    openai_client = OpenAI(api_key=groq_api_key, base_url="https://api.groq.com/openai/v1")
except Exception:
    pass 

# -----------------------------------------------------------------------------
# 3. HELPER FUNCTIONS
# -----------------------------------------------------------------------------
def get_image_path(filename_base):
    extensions = [".png", ".jpg", ".jpeg", ".webp", ".gif"]
    paths = [f"images/{filename_base}", f"assets/{filename_base}", filename_base, f"./{filename_base}"]
    for path in paths:
        for ext in extensions:
            full_path = path + ext
            if os.path.exists(full_path):
                return full_path
    return None

def render_image(filename, caption=None, width=None, use_column_width=False):
    img_path = get_image_path(filename)
    try:
        if img_path:
            if use_column_width:
                st.image(img_path, caption=caption, use_container_width=True)
            else:
                st.image(img_path, caption=caption, width=width)
            return True
        return False
    except:
        return False

def login_user(username, password):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(spreadsheet="https://docs.google.com/spreadsheets/d/18o58Ot15bBL2VA4uMib_HWJWgd112e2dKuil2YwojDk/edit?usp=sharing")
        df.columns = df.columns.str.strip()
        df['username'] = df['username'].astype(str).str.strip()
        df['password'] = df['password'].astype(str).str.strip()
        
        clean_username = username.strip()
        clean_password = password.strip()
        
        user_row = df[df['username'] == clean_username]
        if not user_row.empty:
            stored_password = str(user_row.iloc[0]['password'])
            if stored_password == clean_password:
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
    new_notif = {"date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "message": message}
    notifs.insert(0, new_notif)
    with open(NOTIFICATIONS_FILE, "w") as f: json.dump(notifs, f)

def get_live_status():
    try:
        with open(LIVE_STATUS_FILE, "r") as f: return json.load(f)
    except: return {"is_live": False, "topic": "", "link": ""}

def set_live_status(is_live, topic="", link=""):
    status = {"is_live": is_live, "topic": topic, "link": link}
    with open(LIVE_STATUS_FILE, "w") as f: json.dump(status, f)

def clean_json_response(raw_text):
    """Pro-level JSON extraction to prevent LLM hallucination crashes."""
    match = re.search(r'\[\s*\{.*?\}\s*\]', raw_text, re.DOTALL)
    if match: return match.group(0)
    return raw_text.replace("```json", "").replace("```", "").strip()

# -----------------------------------------------------------------------------
# 4. ADAPTIVE CSS STYLING
# -----------------------------------------------------------------------------
st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%) !important; background-attachment: fixed; }
    h1, h2, h3, h4, p, span, div, label { color: var(--text-color) !important; }
    div.stButton > button { background: linear-gradient(90deg, #1e3a5f, #3b6b9e); color: white !important; border-radius: 8px; border: none; transition: 0.3s; }
    div.stButton > button:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0,0,0,0.3); }
    .stTextInput>div>div>input, .stTextArea>div>div>textarea, .stSelectbox>div>div { background-color: var(--background-color) !important; color: var(--text-color) !important; border-radius: 8px; border: 1px solid rgba(128,128,128,0.3) !important; }
    .hero-ad-box { background: rgba(0, 0, 0, 0.8); backdrop-filter: blur(12px); border: 2px solid #ffd700; border-radius: 20px; padding: 40px 20px; margin: 30px 0; text-align: center; }
    .hero-headline { font-size: 32px; font-weight: 900; background: linear-gradient(to right, #ffffff, #ffd700); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 15px; }
    .founder-header-container { text-align: center; padding: 35px 20px; background: linear-gradient(135deg, rgba(0,0,0,0.8) 0%, rgba(0,0,0,0.6) 100%); border-radius: 20px; border: 1px solid rgba(255, 255, 255, 0.1); margin-bottom: 30px; }
    .founder-headline { font-size: 2.2rem; font-weight: 900; background: linear-gradient(to right, #ffffff 0%, #a1c4fd 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .white-card-fix { background-color: var(--background-color) !important; border: 1px solid rgba(128,128,128,0.2); padding: 20px !important; border-radius: 10px !important; box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important; margin-bottom: 20px !important; }
    @media (prefers-color-scheme: dark) { .stApp { background: linear-gradient(135deg, #004e92 0%, #000428 100%) !important; } }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 5. DYNAMIC NAVIGATION
# -----------------------------------------------------------------------------
st.markdown("""
<div class="founder-header-container">
<div class="founder-headline">Other Apps Were Coded by Engineers. This One Was Coded by Your Master Tutor - Mohammed Salmaan.</div>
<p style="color: #e2e8f0; font-size: 1.2rem; margin-top: 10px;">The only online tuition service in the world running on a proprietary AI-engine built by the Founder.</p>
<p style="color: #ffd700; font-weight: 800; text-transform: uppercase; letter-spacing: 2px;">Pure Teaching Intelligence. Zero Corporate Noise.</p>
</div>
""", unsafe_allow_html=True)

if not st.session_state.logged_in:
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        if st.button("🏠 Home", use_container_width=True): st.session_state.page = "Home"; st.rerun()
    with col2:
        if st.button("📚 Services", use_container_width=True): st.session_state.page = "Services"; st.rerun()
    with col3:
        if st.button("💬 Stories", use_container_width=True): st.session_state.page = "Testimonials"; st.rerun()
    with col4:
        if st.button("🐍 Bootcamp", use_container_width=True): st.session_state.page = "Bootcamp"; st.rerun()
    with col5:
        if st.button("🔐 Student Portal", use_container_width=True, type="primary"): st.session_state.page = "Login"; st.rerun()
    st.write("")
    ai_col1, ai_col2 = st.columns(2)
    with ai_col1:
        if st.button("🧠 Chat with AyA (AI Tutor)", use_container_width=True): st.session_state.page = "AyA_AI"; st.rerun()
    with ai_col2:
        if st.button("📝 AI - Mock Test", use_container_width=True): st.session_state.page = "Mock_Test"; st.rerun()

elif st.session_state.logged_in and not st.session_state.is_admin:
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        if st.button("🎓 Dashboard", use_container_width=True): st.session_state.page = "Dashboard"; st.rerun()
    with col2:
        if st.button("🔴 Live Class", use_container_width=True): st.session_state.page = "Live Class"; st.rerun()
    with col3:
        if st.button("📚 Vault", use_container_width=True): st.session_state.page = "Vault"; st.rerun()
    with col4:
        if st.button("📈 Progress", use_container_width=True): st.session_state.page = "Progress"; st.rerun()
    with col5:
        if st.button("🤖 AI Tools", use_container_width=True): st.session_state.page = "AI_Menu"; st.rerun()
    with col6:
        if st.button("🚪 Logout", use_container_width=True): 
            st.session_state.logged_in = False
            st.session_state.page = "Home"
            st.rerun()

elif st.session_state.is_admin:
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("👨‍🏫 Admin Hub", use_container_width=True): st.session_state.page = "Admin"; st.rerun()
    with col2:
        if st.button("🔴 Manage Live", use_container_width=True): st.session_state.page = "Live Class"; st.rerun()
    with col3:
        if st.button("🚪 Logout", use_container_width=True): 
            st.session_state.logged_in = False
            st.session_state.page = "Home"
            st.rerun()

st.divider()

# -----------------------------------------------------------------------------
# 6. PAGE LOGIC
# -----------------------------------------------------------------------------

if st.session_state.page == "Home":
    st.markdown("""
<div class="hero-ad-box">
<div class="hero-headline">🚨 The Education System Just Got a Reality Check</div>
<p style="color: #e0e0e0; font-size: 18px;">Stop paying for "premium" test series. The corporate coaching giants are scared.</p>
<p style="color: #00ffff; font-size: 22px; font-weight: 800; text-transform: uppercase;">INTRODUCING: THE MOLECULAR MAN AI SUITE</p>
<p style="color: #ff4d4d; font-size: 14px; font-weight: 800;">🚫 NO SUBSCRIPTIONS. NO HIDDEN FEES. PURE TEACHING INTELLIGENCE.</p>
</div>
""", unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    with m1: st.metric("Students Taught", "500+")
    with m2: st.metric("Success Rate", "100%")
    with m3: st.metric("Support", "24/7")
    with m4: st.metric("Experience", "5+ Years")

elif st.session_state.page == "Login":
    st.markdown("# 🔐 Student Portal")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.container(border=True):
            username = st.text_input("👤 Username")
            password = st.text_input("🔑 Password", type="password")
            if st.button("Access Campus 🚀", use_container_width=True, type="primary"):
                if login_user(username, password):
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.is_admin = (username == "Mohammed")
                    st.session_state.page = "Dashboard" if not st.session_state.is_admin else "Admin"
                    st.rerun()
                else:
                    st.error("❌ Invalid Credentials")

elif st.session_state.page == "Dashboard":
    st.markdown(f"# 🎓 Welcome back, {st.session_state.username}!")
    st.info("Keep studying! Check your AI tools for new Mock Tests.")
    s1, s2, s3, s4 = st.columns(4)
    with s1: st.metric("🔥 Day Streak", "12 Days")
    with s2: st.metric("📝 Tests Taken", "8")
    with s3: st.metric("🧠 AyA Questions", "45")
    with s4: st.markdown("🏆 **Current Badge:**\n⚛️ *Molecule Master*")

elif st.session_state.page == "AI_Menu":
    st.markdown("# 🤖 The Molecular Man AI Suite")
    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.markdown("### 🧠 AyA AI Tutor")
            st.write("Chat with your personal 24/7 teaching assistant.")
            if st.button("Open AyA", use_container_width=True, type="primary"): st.session_state.page = "AyA_AI"; st.rerun()
    with col2:
        with st.container(border=True):
            st.markdown("### 📝 Mock Test Generator")
            st.write("Generate unlimited targeted mock tests with strict syllabus grading.")
            if st.button("Open Test Generator", use_container_width=True, type="primary"): st.session_state.page = "Mock_Test"; st.rerun()

elif st.session_state.page == "AyA_AI":
    st.markdown("## 🧠 AyA - The Molecular Man AI")
    SYSTEM_PROMPT = """You are **Aya**, the Lead AI Tutor at **The Molecular Man Expert Tuition Solutions**. 
    Structure: 🧠 CONCEPT -> 🌍 CONTEXT -> ✍️ SOLUTION -> ✅ ANSWER -> 🚀 HERO TIP."""

    with st.expander("📝 New Problem Input", expanded=(len(st.session_state.aya_messages) == 0)):
        input_type = st.radio("Input Method:", ["📄 Text Problem", "📕 Upload PDF"], horizontal=True)
        if input_type == "📄 Text Problem":
            user_text = st.text_area("Paste question:")
            if st.button("Ask AyA 🚀"):
                st.session_state.aya_messages = [{"role": "user", "content": f"PROBLEM:\n{user_text}"}]
                st.rerun()
        elif input_type == "📕 Upload PDF":
            uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])
            if st.button("Analyze PDF 🚀"):
                if uploaded_file:
                    try:
                        pdf_reader = PyPDF2.PdfReader(uploaded_file)
                        pdf_text = "".join([pdf_reader.pages[i].extract_text()[:3000] for i in range(min(2, len(pdf_reader.pages)))])
                        st.session_state.aya_messages = [{"role": "user", "content": f"PROBLEM from PDF:\n{pdf_text}"}]
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error reading PDF: {e}")

    for msg in st.session_state.aya_messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

    if st.session_state.aya_messages and st.session_state.aya_messages[-1]["role"] == "user":
        with st.chat_message("assistant"):
            with st.spinner("🤖 AyA is thinking..."):
                msgs = [{"role": "system", "content": SYSTEM_PROMPT}] + st.session_state.aya_messages
                res = groq_client.chat.completions.create(messages=msgs, model="llama-3.3-70b-versatile", temperature=0.5)
                reply = res.choices[0].message.content
                st.markdown(reply)
                st.session_state.aya_messages.append({"role": "assistant", "content": reply})

    if user_input := st.chat_input("Ask a follow-up..."):
        st.session_state.aya_messages.append({"role": "user", "content": user_input})
        st.rerun()

# ==========================================
# ADVANCED MOCK TEST ENGINE
# ==========================================
elif st.session_state.page == "Mock_Test":
    st.markdown("## 📝 Pro-Level AI Mock Test Engine")
    st.caption("Strict syllabus adherence. Anti-hallucination protocols enabled.")
    
    def get_questions_json(board, cls, sub, chap, num, diff, q_type):
        prompt = f"""
        Act as the Chief Examiner and strict syllabus setter for the {board} Board in India.
        Create a highly accurate, syllabus-aligned test for Class {cls} {sub}, focusing STRICTLY on the chapter: '{chap}'.
        Difficulty level: {diff}. You must generate exactly {num} {q_type} questions.

        CRITICAL INSTRUCTIONS:
        1. NO HALLUCINATIONS. Every fact, formula, and concept must be 100% accurate and strictly within the official {board} syllabus for Class {cls}.
        2. Output ONLY a valid JSON array. Do not include markdown formatting like ```json or any conversational text.
        """
        if q_type == "MCQ":
            prompt += """
        3. For MCQs, the `correct_answer` MUST EXACTLY MATCH one of the strings in the `options` array. 
        FORMAT:
        [
          {
            "id": 1,
            "question": "Clear, unambiguous question text",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "correct_answer": "Exact match to one option",
            "explanation": "Detailed, step-by-step reason why this is correct."
          }
        ]
        """
        elif q_type == "Numerical":
            prompt += """
        3. For Numerical problems, ensure the math is 100% correct. Provide the correct answer with exact proper units.
        FORMAT:
        [
          {
            "id": 1,
            "question": "Clear numerical problem with exact values",
            "correct_answer": "Final numerical answer with units",
            "marks": 3,
            "explanation": "Step-by-step mathematical derivation."
          }
        ]
        """
        else:
            prompt += """
        3. For Descriptive questions, provide a clear marking scheme with essential key points.
        FORMAT:
        [
          {
            "id": 1,
            "question": "Clear descriptive question",
            "marks": 5,
            "key_points": ["Essential point 1", "Essential point 2"],
            "explanation": "A complete, ideal textbook answer."
          }
        ]
        """
        try:
            res = openai_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            return json.loads(clean_json_response(res.choices[0].message.content))
        except Exception as e: 
            return None

    if not st.session_state.mt_questions:
        with st.container(border=True):
            c1, c2 = st.columns(2)
            with c1:
                board = st.selectbox("Board", ["CBSE", "ICSE", "State Board", "NEET/JEE Foundation"])
                # Expanded Classes 6-12
                cls = st.selectbox("Class", [str(i) for i in range(6, 13)], index=4) 
                diff = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"])
            with c2:
                sub = st.text_input("Subject", "Physics")
                chap = st.text_input("Chapter", "Thermodynamics")
                # Added Numerical Option
                q_type = st.radio("Format", ["MCQ", "Numerical", "Descriptive"], horizontal=True)
                num = st.slider("Questions", 3, 20, 5)

        if st.button("🚀 Generate Pro Test", type="primary"):
            if sub and chap:
                with st.spinner("AyA is cross-referencing syllabus and drafting paper..."):
                    st.session_state.mt_q_type = q_type
                    st.session_state.board = board
                    st.session_state.cls = cls
                    questions = get_questions_json(board, cls, sub, chap, num, diff, q_type)
                    if questions:
                        st.session_state.mt_questions = questions
                        st.session_state.mt_answers = {}
                        st.session_state.mt_feedback = None
                        st.rerun()
                    else:
                        st.error("Engine failed to format correctly. Try reducing question count.")

    else:
        if st.session_state.mt_feedback:
            st.success("Test Graded Successfully")
            st.markdown(st.session_state.mt_feedback)
            if st.button("🔄 Start New Test", type="primary"):
                st.session_state.mt_questions = None
                st.rerun()
        else:
            with st.form("mock_test_form"):
                for q in st.session_state.mt_questions:
                    st.markdown(f"**Q{q['id']}. {q['question']}**")
                    if st.session_state.mt_q_type == "MCQ":
                        st.radio("Choose:", q.get('options', []), key=f"q_{q['id']}", label_visibility="collapsed", index=None)
                    else:
                        st.text_area("Your Answer:", key=f"q_{q['id']}")
                    st.divider()
                
                submitted = st.form_submit_button("✅ Submit for Grading")
            
            if submitted:
                answers = {str(q['id']): st.session_state.get(f"q_{q['id']}") for q in st.session_state.mt_questions}
                
                # Deterministic Grading for MCQs (Zero mistakes, fast)
                if st.session_state.mt_q_type == "MCQ":
                    score = 0
                    feedback = ""
                    for q in st.session_state.mt_questions:
                        user_ans = answers[str(q['id'])]
                        if user_ans == q['correct_answer']:
                            score += 1
                            feedback += f"✅ **Q{q['id']}: Correct!**\n*AyA's Note:* {q.get('explanation', '')}\n\n---\n"
                        else:
                            feedback += f"❌ **Q{q['id']}: Incorrect.**\nYour Answer: '{user_ans}'\nCorrect Answer: **{q['correct_answer']}**\n*AyA's Note:* {q.get('explanation', '')}\n\n---\n"
                    
                    st.session_state.mt_feedback = f"### Final Score: {score}/{len(st.session_state.mt_questions)}\n\n" + feedback
                    st.rerun()
                
                # LLM Grading for Numerical/Descriptive based on Pre-Generated Answer Key
                else:
                    prompt = f"""
                    You are AyA, the Lead Tutor grading a Class {st.session_state.cls} {st.session_state.board} student.
                    Official Answer Key & Marking Scheme: {json.dumps(st.session_state.mt_questions)}
                    Student's Answers: {json.dumps(answers)}

                    Evaluate each answer. Be strict but fair. Assign partial marks based on the key points/steps.
                    Format as Markdown. Start with an estimated Total Score, then detailed feedback for each question explaining where they lost marks.
                    """
                    with st.spinner("AyA is grading your paper..."):
                        try:
                            res = openai_client.chat.completions.create(
                                model="llama-3.3-70b-versatile",
                                messages=[{"role": "user", "content": prompt}],
                                temperature=0.2
                            )
                            st.session_state.mt_feedback = res.choices[0].message.content
                            st.rerun()
                        except Exception as e:
                            st.error("Grading Engine offline. Try again.")

# (Your Live Class, Vault, Progress, Services, Testimonials, and Contact pages remain exactly identical here. Omitted to save your reading space, but keep them at the bottom of the script!)
