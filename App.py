import streamlit as st
import os
import json
import datetime
import re
import urllib.parse 
import pandas as pd
from PIL import Image
from groq import Groq
from openai import OpenAI
import PyPDF2
from streamlit_gsheets import GSheetsConnection

# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION (Must be first)
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

# API Keys Setup
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
    """Pro-level JSON extractor and LaTeX escape-fixer."""
    match = re.search(r'\[\s*\{.*?\}\s*\]', raw_text, re.DOTALL)
    if match:
        raw_json = match.group(0)
    else:
        raw_json = raw_text.replace("```json", "").replace("```", "").strip()
    fixed_json = re.sub(r'(?<!\\)\\(?![nrt"\\/])', r'\\\\', raw_json)
    return fixed_json

# -----------------------------------------------------------------------------
# 4. ADAPTIVE CSS STYLING
# -----------------------------------------------------------------------------
st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%) !important; background-attachment: fixed; }
    .block-container { padding-top: 1rem !important; padding-bottom: 5rem !important; }
    h1, h2, h3, h4, h5, h6, p, div, span, li, label, .stMarkdown { color: var(--text-color) !important; }
    div.stButton > button { background: linear-gradient(90deg, #1e3a5f, #3b6b9e, #1e3a5f); color: white !important; border-radius: 25px !important; border: 1px solid rgba(255,255,255,0.2) !important; }
    div.stButton > button:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0,0,0,0.3); }
    div[data-testid="stFormSubmitButton"] > button { background: #1e3a5f !important; color: #ffffff !important; border: 2px solid var(--text-color) !important; }
    .stTextInput>div>div>input, .stTextArea>div>div>textarea, .stSelectbox>div>div { background-color: var(--background-color) !important; color: var(--text-color) !important; border-radius: 8px; border: 1px solid rgba(128,128,128,0.3) !important; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
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

st.markdown("### 🧭 Main Menu")

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

# ==========================================
# PAGE: AYA AI TUTOR
# ==========================================
elif st.session_state.page == "AyA_AI":
    st.markdown("## 🧠 AyA - The Molecular Man AI")
    
    SYSTEM_PROMPT = """You are **Aya**, the Lead AI Tutor at **The Molecular Man Expert Tuition Solutions**. 
    Tone: Encouraging, clear, patient, and intellectually rigorous.
    
    CRITICAL LATEX INSTRUCTIONS:
    1. You MUST format all mathematical equations using standard LaTeX. Use `$` for inline math and `$$` for block math.
    2. NEVER use the `\\times` command (it breaks our formatting engine). Use `\\cdot` or `*` for multiplication.
    3. Use double line breaks (`\n\n`) to separate steps visually.
    
    Structure: 🧠 CONCEPT -> 🌍 CONTEXT -> ✍️ SOLUTION -> ✅ ANSWER."""

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
# PAGE: MOCK TEST ENGINE
# ==========================================
elif st.session_state.page == "Mock_Test":
    st.markdown("## 📝 Pro-Level AI Mock Test Engine")
    st.caption("Strict syllabus adherence. Native JSON mode and Chain-of-Thought math verification enabled.")
    
    def get_questions_json(board, cls, sub, chap, num, diff, q_type):
        prompt = f"Act as the Chief Examiner for the {board} Board in India.\n"
        prompt += f"Create a test for Class {cls} {sub}, chapter: '{chap}'. Difficulty: {diff}. Count: {num} {q_type}.\n\n"
        
        prompt += """CRITICAL INSTRUCTIONS TO PREVENT CRASHES AND ERRORS:
        1. JSON ONLY: Output a valid JSON object containing a "questions" array.
        2. NO \\times COMMAND: NEVER use `\\times` for multiplication. It crashes the renderer. Use `\\cdot` or `*`.
        3. DOUBLE ESCAPE LATEX: You MUST double-escape all LaTeX commands (e.g., write `\\\\frac` instead of `\\frac`). 
        4. MATH ACCURACY: You MUST calculate the exact mathematical answer in the "draft_calculation" field FIRST. The `correct_answer` MUST EXACTLY MATCH one of the strings in the `options` array.
        """
        
        if q_type in ["MCQ", "Numerical"]:
            prompt += """
        JSON FORMAT EXACTLY LIKE THIS:
        {
          "questions": [
            {
              "id": 1,
              "draft_calculation": "1/v - 1/u = 1/f => 1/v = 1/20 + 1/(-40) => 1/v = 1/40 => v = +40 cm.",
              "question": "A convex lens has a focal length of $f = +20$ cm. If an object is placed at $u = -40$ cm, what is the image distance $v$?",
              "options": ["+20 cm", "+40 cm", "-40 cm", "-80 cm"],
              "correct_answer": "+40 cm",
              "explanation": "Given: $f = +20$ cm, $u = -40$ cm.\\n\\nUsing the lens formula:\\n$$\\\\frac{1}{v} - \\\\frac{1}{u} = \\\\frac{1}{f}$$\\n\\n$$\\\\frac{1}{v} = \\\\frac{1}{20} - \\\\frac{1}{40} = \\\\frac{1}{40}$$\\n\\n$v = +40$ cm."
            }
          ]
        }
        """
        else:
            prompt += """
        JSON FORMAT EXACTLY LIKE THIS:
        {
          "questions": [
            {
              "id": 1,
              "question": "Clear descriptive question",
              "marks": 5,
              "key_points": ["Point 1", "Point 2"],
              "explanation": "A complete textbook answer."
            }
          ]
        }
        """
        try:
            res = openai_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=4000,
                response_format={"type": "json_object"} 
            )
            data = json.loads(res.choices[0].message.content)
            return data.get("questions", [])
        except Exception as e:
            st.error(f"API Error. Please try reducing the question count. Details: {e}")
            return None

    if not st.session_state.mt_questions:
        with st.container(border=True):
            c1, c2 = st.columns(2)
            with c1:
                board = st.selectbox("Board", ["CBSE", "ICSE", "State Board", "NEET/JEE Foundation"])
                cls = st.selectbox("Class", [str(i) for i in range(6, 13)], index=4) 
                diff = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"])
            with c2:
                sub = st.text_input("Subject", "Physics")
                chap = st.text_input("Chapter", "Light - Reflection and Refraction")
                q_type = st.radio("Format", ["MCQ", "Numerical", "Descriptive"], horizontal=True)
                num = st.slider("Questions", 3, 20, 5)

        if st.button("🚀 Generate Pro Test", type="primary"):
            if sub and chap:
                with st.spinner("AyA is running internal math calculations and drafting paper..."):
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
                    if st.session_state.mt_q_type in ["MCQ", "Numerical"]:
                        st.radio("Choose:", q.get('options', []), key=f"q_{q['id']}", label_visibility="collapsed", index=None)
                    else:
                        st.text_area("Your Answer:", key=f"q_{q['id']}")
                    st.divider()
                
                submitted = st.form_submit_button("✅ Submit for Grading")
            
            if submitted:
                answers = {}
                all_answered = True
                
                for q in st.session_state.mt_questions:
                    val = st.session_state.get(f"q_{q['id']}")
                    if val is None or str(val).strip() == "":
                        all_answered = False
                    answers[str(q['id'])] = val
                
                if not all_answered:
                    st.error("⚠️ You cannot submit yet! Please answer all questions before submitting the exam.")
                else:
                    if st.session_state.mt_q_type in ["MCQ", "Numerical"]:
                        score = 0
                        feedback = ""
                        for q in st.session_state.mt_questions:
                            user_ans = answers[str(q['id'])]
                            
                            expl = q.get('explanation', '')
                            expl_formatted = str(expl).replace('\\n', '\n').replace('\n', '\n\n')
                            
                            if user_ans == q['correct_answer']:
                                score += 1
                                feedback += f"### ✅ Q{q['id']}: Correct!\n**AyA's Explanation:**\n\n{expl_formatted}\n\n---\n"
                            else:
                                feedback += f"### ❌ Q{q['id']}: Incorrect.\nYour Answer: *{user_ans}*\nCorrect Answer: **{q['correct_answer']}**\n\n**AyA's Explanation:**\n\n{expl_formatted}\n\n---\n"
                        
                        st.session_state.mt_feedback = f"## Final Score: {score}/{len(st.session_state.mt_questions)}\n\n---\n" + feedback
                        st.rerun()
                    
                    else: 
                        prompt = f"""
                        You are AyA, the Lead Tutor grading a Class {st.session_state.cls} {st.session_state.board} student.
                        Official Answer Key & Marking Scheme: {json.dumps(st.session_state.mt_questions)}
                        Student's Answers: {json.dumps(answers)}

                        Evaluate each answer. Be strict but fair. Assign partial marks based on the key points/steps.
                        Format as Markdown. Use LaTeX for math. Start with an estimated Total Score, then detailed feedback for each question.
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

# ==========================================
# PAGE: LIVE CLASS
# ==========================================
elif st.session_state.page == "Live Class":
    st.markdown("# 🔴 Molecular Man Live Classroom")
    if not st.session_state.logged_in:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown('<div style="font-size: 24px; text-align: center; margin-bottom: 20px;">Restricted Access</div>', unsafe_allow_html=True)
            with st.container(border=True):
                username = st.text_input("👤 Username")
                password = st.text_input("🔐 Password", type="password")
                if st.button("Login to Classroom 🚀", use_container_width=True):
                    if login_user(username, password):
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.session_state.is_admin = (username == "Mohammed")
                        st.rerun()
                    else:
                        st.error("❌ Invalid Credentials")
    else:
        col1, col2 = st.columns([3, 1])
        with col1: st.write(f"Logged in as: **{st.session_state.username}**")
        with col2:
            if st.button("Logout"):
                st.session_state.logged_in = False
                st.session_state.username = "Student"
                st.rerun()
        st.divider()

        if st.session_state.is_admin:
            st.markdown("## 👨‍🏫 Teacher Command Center")
            col1, col2 = st.columns([2, 1])
            with col1:
                st.markdown("### 🔴 Live Class Controls")
                with st.container(border=True):
                    status = get_live_status()
                    if status["is_live"]:
                        st.success(f"✅ Class is LIVE: {status['topic']}")
                        raw_link = status['link'].strip()
                        final_display_link = "https://" + raw_link if not raw_link.startswith(("http://", "https://")) else raw_link
                        st.markdown(f"**Current Link:** {final_display_link}")
                        st.markdown(f"""
                            <div style="text-align:center; margin: 20px;">
                                <a href="{final_display_link}" target="_blank" style="text-decoration:none;">
                                    <button style="background: linear-gradient(45deg, #00c853, #b2ff59); color: black; padding: 15px 30px; border: none; border-radius: 50px; font-weight: bold; font-size: 18px; cursor: pointer;">
                                        🎥 Enter Meeting
                                    </button>
                                </a>
                            </div>
                        """, unsafe_allow_html=True)
                        if st.button("End Class ⏹️", type="primary"):
                            set_live_status(False)
                            st.rerun()
                    else:
                        st.info("Start a new session")
                        with st.form("start_live"):
                            topic = st.text_input("Class Topic", placeholder="e.g., Thermodynamics Part 2")
                            meet_link = st.text_input("Meeting Link", placeholder="Paste Google Meet / Teams / Zoom link here...")
                            if st.form_submit_button("Go Live 📡"):
                                if topic and meet_link:
                                    meet_link = "https://" + meet_link if not meet_link.startswith(("http://", "https://")) else meet_link
                                    set_live_status(True, topic, meet_link)
                                    add_notification(f"🔴 Live Class Started: {topic}. Join now!")
                                    st.rerun()
                                else:
                                    st.warning("Please enter both Topic and Meeting Link")

            with col2:
                st.markdown("### 📢 Send Notification")
                with st.form("notif_form"):
                    msg = st.text_area("Announcement Message")
                    if st.form_submit_button("Send Blast 🚀", use_container_width=True) and msg:
                        add_notification(msg)
                        st.success("Notification Sent!")
                st.markdown("### 📜 History")
                with st.container(border=True):
                    for n in get_notifications()[:5]: st.markdown(f"<small>{n['date']}</small><br>{n['message']}<hr>", unsafe_allow_html=True)

        else:
            st.write("")
            status = get_live_status()
            if status["is_live"]:
                raw_link = status['link'].strip()
                final_link = "https://" + raw_link if not raw_link.startswith(("http://", "https://")) else raw_link
                st.markdown(f"""
                <div style="background: rgba(255, 0, 0, 0.1); border: 2px solid red; padding: 30px; border-radius: 15px; text-align: center; margin-bottom: 20px;">
                    <h1 style="color: #ff4444 !important; margin:0; font-size: 40px;">🔴 LIVE NOW</h1>
                    <h2 style="color: var(--text-color) !important; margin-top: 10px;">Topic: {status['topic']}</h2>
                    <br>
                    <div class="live-button-container">
                        <a href="{final_link}" target="_blank" style="text-decoration:none;">
                            <button style="background: linear-gradient(45deg, #ff0000, #ff5252); color: white; padding: 20px 40px; border: none; border-radius: 50px; font-weight: bold; font-size: 24px; cursor: pointer; box-shadow: 0 0 20px rgba(255, 0, 0, 0.5);">
                                👉 CLICK TO JOIN CLASS
                            </button>
                        </a>
                    </div>
                    <p style="margin-top: 15px; color: #aaa;">(Opens Google Meet / Teams in new tab)</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="padding: 40px; text-align: center; border: 2px dashed #ffd700; border-radius: 15px; margin-bottom: 20px;">
                    <h2 style="color: #888 !important;">💤 No live class right now</h2>
                    <p>Check notifications below for schedule.</p>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("### 🔔 Notice Board")
            notifs = get_notifications()
            if notifs:
                for n in notifs:
                    st.markdown(f"""
                    <div class="notif-card">
                        <div style="color: #ffd700; font-size: 12px; font-weight: bold;">📅 {n['date']}</div>
                        <div style="color: var(--text-color); font-size: 16px;">{n['message']}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No new announcements.")

elif st.session_state.page == "Vault":
    st.markdown("# 📚 The Resource Vault")
    st.write("Access proprietary notes, formula sheets, and recorded lectures 24/7.")
    tab1, tab2, tab3, tab4 = st.tabs(["⚡ Physics", "⚗️ Chemistry", "🧬 Biology", "📐 Mathematics"])
    with tab1:
        with st.expander("CBSE Class 10: Light - Reflection and Refraction"):
            st.write("📝 **Master Notes:** Complete breakdown of spherical mirrors and lenses.")
            st.download_button("Download PDF", data="dummy data", file_name="Reflection_Notes.pdf", mime="application/pdf")
    with tab2:
        with st.expander("ICSE Class 10: Chemical Bonding"):
            st.write("📝 **Master Notes:** Electrovalent, Covalent, and Coordinate bonding simplified.")
            st.download_button("Download PDF", data="dummy data", file_name="Chemical_Bonding.pdf", mime="application/pdf")
    with tab3:
        with st.expander("CBSE Class 10: Life Processes"):
            st.write("📝 **Master Notes:** Nutrition, Respiration, Transportation, and Excretion diagrams.")
            st.download_button("Download PDF", data="dummy data", file_name="Life_Processes.pdf", mime="application/pdf")
    with tab4:
        with st.expander("CBSE Class 10: Polynomials"):
            st.write("📝 **Master Notes:** Zeroes of a polynomial and relationship with coefficients.")
            st.download_button("Download PDF", data="dummy data", file_name="Polynomials_Formulas.pdf", mime="application/pdf")

elif st.session_state.page == "Progress":
    st.markdown("# 📈 Performance Analytics")
    st.write("Track your Mock Test scores and identify areas for improvement.")
    chart_data = pd.DataFrame(
        {
            "Physics": [65, 70, 75, 82, 85, 90],
            "Chemistry": [80, 78, 85, 88, 92, 95],
            "Biology": [60, 65, 70, 72, 78, 80],
            "Mathematics": [50, 60, 65, 75, 80, 88]
        },
        index=["Week 1", "Week 2", "Week 3", "Week 4", "Week 5", "Week 6"]
    )
    st.markdown("### 📊 Mock Test Score Trend (%)")
    st.line_chart(chart_data)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 🎯 Strongest Areas")
        st.success("1. ICSE Class 10 Chemistry: Chemical Bonding")
        st.success("2. CBSE Class 10 Physics: Electricity")
    with col2:
        st.markdown("### 🚧 Focus Areas (AyA's Advice)")
        st.warning("1. CBSE Class 10 Biology: Life Processes")
        st.warning("2. CBSE Class 10 Mathematics: Polynomials")
        if st.button("Ask AyA for help with Polynomials 🧠"):
            st.session_state.page = "AyA_AI"
            st.rerun()

elif st.session_state.page == "Services":
    st.markdown("# 📚 Our Services")
    st.markdown("## 🎓 Subjects We Teach")
    sub1, sub2 = st.columns(2)
    with sub1:
        with st.container(border=True):
            st.markdown("### 📐 Mathematics")
            st.write("Classes 6-12 (CBSE/State/Commerce/Science)")
        st.write("")
        with st.container(border=True):
            st.markdown("### ⚗️ Chemistry")
            st.write("NEET/JEE Chemistry, Organic & Inorganic")
    with sub2:
        with st.container(border=True):
            st.markdown("### ⚡ Physics")
            st.write("Conceptual clarity & Numerical problem solving")
        st.write("")
        with st.container(border=True):
            st.markdown("### 🧬 Biology")
            st.write("Botany, Zoology & NEET Prep")

elif st.session_state.page == "Testimonials":
    st.markdown("# 💬 Student Success Stories")
    t1, t2 = st.columns(2)
    def testimonial_card(text, author):
        st.markdown(f"""
        <div class="white-card-fix">
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

    st.write("")
    st.markdown("## 🏆 Our Results")
    r1, r2, r3 = st.columns(3)
    with r1: st.markdown('<div class="white-card-fix" style="text-align:center;"><div style="font-weight:bold;">Board Exams</div><div style="font-size:28px;font-weight:bold;">80%</div><div style="font-size:12px;">Average Score</div></div>', unsafe_allow_html=True)
    with r2: st.markdown('<div class="white-card-fix" style="text-align:center;"><div style="font-weight:bold;">Improvement</div><div style="font-size:28px;font-weight:bold;">60%</div><div style="font-size:12px;">vs. Baseline</div></div>', unsafe_allow_html=True)
    with r3: st.markdown('<div class="white-card-fix" style="text-align:center;"><div style="font-weight:bold;">Doubt Support</div><div style="font-size:28px;font-weight:bold;">&lt; 2 Hrs</div><div style="font-size:12px;">Resolution Time</div></div>', unsafe_allow_html=True)

    st.write("")
    st.markdown("## 💡 Why Parents Trust Us")
    w1, w2, w3 = st.columns(3)
    with w1: st.markdown('<div class="white-card-fix"><h3 style="margin:0;">🎓 Expert Educator</h3><p style="margin-top:10px;">One-on-one mentoring that identifies specific learning gaps.</p></div>', unsafe_allow_html=True)
    with w2: st.markdown('<div class="white-card-fix"><h3 style="margin:0;">🧠 Conceptual</h3><p style="margin-top:10px;">No rote memorization. We focus on "Why" and "How".</p></div>', unsafe_allow_html=True)
    with w3: st.markdown('<div class="white-card-fix"><h3 style="margin:0;">💰 Fair Pricing</h3><p style="margin-top:10px;">No hidden fees. Quality education for every family.</p></div>', unsafe_allow_html=True)

    st.write("")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2: st.link_button("📱 Book Free Trial", "https://wa.me/917339315376", use_container_width=True)

elif st.session_state.page == "Bootcamp":
    st.markdown("# 🐍 Python for Data Science & AI")
    boot1, boot2 = st.columns([1, 1.5])
    with boot1:
        if not render_image("poster", use_column_width=True):
            if not render_image("python_bootcamp", use_column_width=True):
                with st.container(border=True):
                    st.markdown("# 🐍")
                    st.markdown("## Python")
                    st.markdown("### Weekend Intensive Program")
    with boot2:
        with st.container(border=True):
            st.markdown("### Weekend Intensive Program")
            st.write("Master the most in-demand programming language")
            st.write("")
            st.markdown("👨‍🏫 **Instructor:** Mohammed Salmaan M")
            st.caption("Data Science & AI Expert | Created Ed-Tech Plotform - The Molecular Man Expert Tuition Solutions")
            st.write("")
            st.markdown("📅 **Schedule:** Saturdays & Sundays")
            st.caption("1 hours per session | Morning & Evening batches")
            st.write("")
            st.markdown("💻 **Requirements:** Laptop with internet")
            st.caption("We'll help you setup Jupyter Notebook & VS Code")
            st.write("")
            with st.expander("📚 Curriculum Highlights"):
                st.write("• Python Basics & Data Structures")
                st.write("• NumPy & Pandas for Data Analysis")
                st.write("• Data Visualization with Matplotlib")
                st.write("• Introduction to Machine Learning")
                st.write("• Real-world Project: Build your first AI model")
        st.write("")
        st.link_button("📱 Enroll Now", "https://wa.me/917339315376", use_container_width=True)

elif st.session_state.page == "Contact":
    st.markdown("# 📞 Get In Touch")
    c1, c2 = st.columns([1, 1])
    with c1:
        with st.container(border=True):
            st.markdown("### Contact Information")
            st.markdown("**📱 Phone:** +91 73393 15376")
            st.markdown("**✉️ Email:** the.molecularmanexpert@gmail.com")
            st.write("")
            st.markdown("### 📍 Location")
            st.write("Madurai, Tamil Nadu")
            st.write("")
            st.link_button("💬 Chat on WhatsApp", "https://wa.me/917339315376", use_container_width=True)
    with c2:
        with st.container(border=True):
            st.markdown("### Send us a Message")
            with st.container():
                name = st.text_input("Name")
                phone = st.text_input("Phone")
                grade = st.selectbox("Grade", ["Class 6-8", "Class 9-10", "Class 11-12", "Repeater/Other"])
                msg = st.text_area("Message")
                if name and phone and msg:
                    subject = urllib.parse.quote(f"Tuition Inquiry from {name}")
                    body = urllib.parse.quote(f"Name: {name}\nPhone: {phone}\nGrade: {grade}\n\nMessage:\n{msg}")
                    mailto_link = f"mailto:the.molecularmanexpert@gmail.com?subject={subject}&body={body}"
                    st.markdown(f"""
                    <a href="{mailto_link}" target="_blank" style="text-decoration: none;">
                        <div style="width: 100%; background: linear-gradient(90deg, #1e3a5f, #3b6b9e); color: white; text-align: center; padding: 12px; border-radius: 25px; font-weight: bold; border: 1px solid white; margin-top: 10px; cursor: pointer;">
                            🚀 Click to Send Email
                        </div>
                    </a>
                    <div style="text-align:center; font-size:12px; color:#aaa; margin-top:5px;">(Opens your default email app)</div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div style="width: 100%; background: #444; color: #888; text-align: center; padding: 12px; border-radius: 25px; font-weight: bold; border: 1px solid #555; margin-top: 10px;">
                        Fill details to enable Send
                    </div>
                    """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# FOOTER
# -----------------------------------------------------------------------------
st.write("")
st.write("")
with st.container(border=True):
    st.markdown("""
        <style>
        @keyframes gradient-animation { 0% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } 100% { background-position: 0% 50%; } }
        .animated-footer-text {
            font-weight: 800; font-size: 24px; text-transform: uppercase; text-align: center; letter-spacing: 2px;
            background: linear-gradient(45deg, #ff0000, #ff7300, #fffb00, #48ff00, #00ffd5, #002bff, #7a00ff, #ff00c8, #ff0000); background-size: 300%;
            -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; color: transparent;
            animation: gradient-animation 10s ease infinite;
        }
        </style>
        <div class="animated-footer-text">PRECISE • PASSIONATE • PROFESSIONAL</div>
    """, unsafe_allow_html=True)
    st.markdown("<div style='text-align: center; color: gray; font-size: 12px; margin-top: 10px;'>© 2026 The Molecular Man Expert Tuition Solutions | Mohammed Salmaan M. All Rights Reserved.</div>", unsafe_allow_html=True)
