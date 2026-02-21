import streamlit as st
import os
import json
import datetime
import re
import math
import numpy as np
import pandas as pd
from PIL import Image
from groq import Groq
from openai import OpenAI
from streamlit_gsheets import GSheetsConnection

# -----------------------------------------------------------------------------
# 1. CORE ENGINE: THE UNIVERSAL MATH RESOLVER
# -----------------------------------------------------------------------------
def solve_math_tags(text):
    """
    Finds [[CALC: expression]] and replaces it with LaTeX formatted result.
    Example: [[CALC: 1/2 + 1/4]] -> $0.75$
    """
    def evaluate(match):
        expr = match.group(1).replace("^", "**").replace("×", "*").replace("÷", "/")
        try:
            # Safe evaluation using restricted namespace
            result = eval(expr, {"__builtins__": None}, {**vars(math), **vars(np)})
            # Return formatted as LaTeX
            if isinstance(result, float) and result.is_integer():
                return f"${int(result)}$"
            return f"${round(result, 3)}$"
        except:
            return f"[[Math Error]]"

    # Pattern to find [[CALC: ...]]
    return re.sub(r"\[\[CALC:\s*(.*?)\s*\]\]", evaluate, text)

# -----------------------------------------------------------------------------
# 2. PAGE & THEME CONFIGURATION
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="The Molecular Man AI",
    page_icon="⚛️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Deep Space Aesthetics
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
    
    .stApp {
        background: radial-gradient(circle at top right, #0a192f, #000000);
        font-family: 'Inter', sans-serif;
    }
    
    /* Glassmorphism Cards */
    .glass-card {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 25px;
        margin-bottom: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.8);
    }
    
    /* Neon Headlines */
    .neon-text {
        font-weight: 900;
        background: linear-gradient(90deg, #00d2ff, #3a7bd5, #00d2ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -1px;
    }
    
    /* Animated Buttons */
    div.stButton > button {
        background: linear-gradient(45deg, #1e3a5f, #00d2ff) !important;
        color: white !important;
        border-radius: 12px !important;
        border: none !important;
        padding: 10px 24px !important;
        transition: all 0.3s ease;
    }
    
    div.stButton > button:hover {
        transform: scale(1.02);
        box-shadow: 0 0 15px rgba(0, 210, 255, 0.5);
    }

    /* LaTeX Rendering Tweaks */
    .stMarkdown p { font-size: 1.1rem; line-height: 1.6; }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 3. API INITIALIZATION
# -----------------------------------------------------------------------------
try:
    GROQ_KEY = st.secrets["GROQ_API_KEY"]
    client = Groq(api_key=GROQ_KEY)
    # Using OpenAI wrapper for structured JSON output
    ai_json_client = OpenAI(api_key=GROQ_KEY, base_url="https://api.groq.com/openai/v1")
except:
    st.error("Missing GROQ_API_KEY in Streamlit Secrets.")

# -----------------------------------------------------------------------------
# 4. SESSION STATE
# -----------------------------------------------------------------------------
if 'page' not in st.session_state: st.session_state.page = "Home"
if 'chat_history' not in st.session_state: st.session_state.chat_history = []

# -----------------------------------------------------------------------------
# 5. UI COMPONENTS
# -----------------------------------------------------------------------------

def render_navbar():
    cols = st.columns([2, 1, 1, 1, 1])
    with cols[0]:
        st.markdown("<h2 class='neon-text'>⚛️ MOLECULAR MAN</h2>", unsafe_allow_html=True)
    with cols[1]:
        if st.button("🏠 Home", use_container_width=True): st.session_state.page = "Home"
    with cols[2]:
        if st.button("🧠 AyA AI", use_container_width=True): st.session_state.page = "AyA"
    with cols[3]:
        if st.button("📝 Mock Test", use_container_width=True): st.session_state.page = "Mock"
    with cols[4]:
        if st.button("🚪 Logout", use_container_width=True): st.session_state.page = "Home"
    st.divider()

# -----------------------------------------------------------------------------
# 6. PAGE: AyA AI TUTOR
# -----------------------------------------------------------------------------
def page_aya():
    st.markdown("<h1 class='neon-text'>🧠 AyA: The Universal Math Engine</h1>", unsafe_allow_html=True)
    st.caption("All calculations are performed by a deterministic Python engine for 100% accuracy.")

    SYSTEM_PROMPT = """You are AyA. 
    1. For every calculation, wrap it in [[CALC: expression]]. Example: 'Force = [[CALC: 5 * 9.8]] N'.
    2. Use standard LaTeX for all math formatting. Use $ for inline and $$ for block math.
    3. NEVER estimate math. Always use the [[CALC: ...]] tag."""

    # Chat Container
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if user_input := st.chat_input("Ask a complex numerical..."):
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.chat_message("user"): st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Calculating via Molecular-Engine..."):
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "system", "content": SYSTEM_PROMPT}] + st.session_state.chat_history
                )
                raw_text = response.choices[0].message.content
                # Trigger the Universal Resolver
                final_text = solve_math_tags(raw_text)
                st.markdown(final_text)
                st.session_state.chat_history.append({"role": "assistant", "content": final_text})

# -----------------------------------------------------------------------------
# 7. PAGE: MOCK TEST ENGINE
# -----------------------------------------------------------------------------
def page_mock_test():
    st.markdown("<h1 class='neon-text'>📝 Hybrid Mock Test Engine</h1>", unsafe_allow_html=True)
    
    with st.sidebar:
        subject = st.text_input("Subject", "Physics")
        topic = st.text_input("Topic", "Electricity")
        diff = st.select_slider("Difficulty", options=["Easy", "Medium", "Hard"])
        num_q = st.number_input("Number of Questions", 1, 10, 3)

    if st.button("Generate Bulletproof Paper 🚀"):
        prompt = f"""Generate {num_q} {diff} MCQs for {subject} on {topic}.
        For every numerical option and question part, use the [[CALC: ...]] tag.
        Format everything in LaTeX.
        Return ONLY a JSON object: 
        {{ "questions": [ {{ "q": "text with LaTeX", "options": ["[[CALC: ...]]", ...], "correct": "[[CALC: ...]]" }} ] }}"""

        with st.spinner("AI drafting... Python calculating..."):
            res = ai_json_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            data = json.loads(res.choices[0].message.content)
            
            # Universal Resolver on the whole JSON
            clean_json_str = solve_math_tags(json.dumps(data))
            st.session_state.current_test = json.loads(clean_json_str)

    if 'current_test' in st.session_state:
        for idx, q in enumerate(st.session_state.current_test['questions']):
            with st.container(border=True):
                st.markdown(f"**Q{idx+1}.** {q['q']}")
                st.radio("Select Answer:", q['options'], key=f"q_{idx}")

# -----------------------------------------------------------------------------
# 8. MAIN ROUTER
# -----------------------------------------------------------------------------
def main():
    render_navbar()
    
    if st.session_state.page == "Home":
        st.markdown("""
        <div class='glass-card' style='text-align: center;'>
            <h1 class='neon-text' style='font-size: 4rem;'>THE MOLECULAR MAN</h1>
            <p style='font-size: 1.5rem; color: #a1c4fd;'>Beyond Engineering. Pure Teaching Intelligence.</p>
            <br>
            <div style='display: flex; justify-content: center; gap: 20px;'>
                <div class='glass-card' style='width: 200px;'><h3>500+</h3><p>Students</p></div>
                <div class='glass-card' style='width: 200px;'><h3>100%</h3><p>Accuracy</p></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    elif st.session_state.page == "AyA":
        page_aya()
    elif st.session_state.page == "Mock":
        page_mock_test()

if __name__ == "__main__":
    main()
