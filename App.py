import streamlit as st
import os
import json
from groq import Groq

# -----------------------------------------------------------------------------
# Page Configuration & Branding
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="AI Mock Test | The Molecular Man Expert Tuition Solutions",
    page_icon="⚛️",
    layout="wide"
)

st.title("The Molecular Man Expert Tuition Solutions")
st.header("AI Mock Test Generator")

# -----------------------------------------------------------------------------
# State Management Initialization
# -----------------------------------------------------------------------------
if 'test_generated' not in st.session_state:
    st.session_state.test_generated = False
if 'questions' not in st.session_state:
    st.session_state.questions = []
if 'submitted' not in st.session_state:
    st.session_state.submitted = False

def reset_test():
    st.session_state.test_generated = False
    st.session_state.questions = []
    st.session_state.submitted = False

# -----------------------------------------------------------------------------
# Sidebar Configuration
# -----------------------------------------------------------------------------
with st.sidebar:
    st.subheader("Test Configuration")
    
    board = st.selectbox("Board", ["CBSE", "ICSE", "State Boards", "IGCSE", "IB", "Global"])
    class_level = st.selectbox("Class Level", ["Class 12", "Class 11", "Class 10", "Class 9", "Class 8", "Class 7", "Class 6", "NEET", "JEE"])
    subject = st.selectbox("Subject", ["Chemistry", "Physics", "Mathematics", "Biology", "History", "General"])
    topic = st.text_input("Topic/Chapter", placeholder="e.g., Organic Chemistry")
    difficulty = st.select_slider("Difficulty", options=["Easy", "Medium", "Hard"])
    num_questions = st.slider("Number of Questions", min_value=5, max_value=20, value=10)
    
    generate_btn = st.button("Generate Mock Test", type="primary", on_click=reset_test)

# -----------------------------------------------------------------------------
# Groq API Integration & Logic
# -----------------------------------------------------------------------------
def fetch_questions(board, class_level, subject, topic, difficulty, num_questions):
    # Retrieve API key securely
    api_key = st.secrets.get("GROQ_API_KEY", os.environ.get("GROQ_API_KEY"))
    if not api_key:
        st.error("Groq API Key not found. Please set it in Streamlit secrets or as an environment variable.")
        return None

    client = Groq(api_key=api_key)
    
    system_prompt = (
        "You are an expert educational content creator. Your task is to generate high-quality, "
        "multiple-choice questions based strictly on the user's parameters. "
        "You MUST output ONLY a valid JSON object. Do not include any introductory text, markdown blocks (like ```json), "
        "or concluding remarks. The JSON structure MUST be exactly as follows:\n"
        "{\n"
        '  "questions": [\n'
        "    {\n"
        '      "question": "Question text here",\n'
        '      "options": ["Option A", "Option B", "Option C", "Option D"],\n'
        '      "correct_answer": "Exact text of the correct option",\n'
        '      "explanation": "Detailed explanation of why this is correct."\n'
        "    }\n"
        "  ]\n"
        "}"
    )
    
    user_prompt = (
        f"Generate {num_questions} multiple-choice questions for {board} board, {class_level} level. "
        f"Subject: {subject}. Topic: '{topic}'. Difficulty: {difficulty}."
    )

    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model="llama3-8b-8192", 
            response_format={"type": "json_object"}, # Forces JSON output structurally
            temperature=0.3 # Lower temperature for more consistent, factual formatting
        )
        
        raw_content = response.choices[0].message.content.strip()
        data = json.loads(raw_content)
        return data.get("questions", [])
        
    except json.JSONDecodeError:
        st.error("Failed to parse the AI response. The model did not return valid JSON.")
        return None
    except Exception as e:
        st.error(f"An error occurred while generating the test: {e}")
        return None

# -----------------------------------------------------------------------------
# Main Application Flow
# -----------------------------------------------------------------------------
if generate_btn:
    if not topic.strip():
        st.warning("Please enter a Topic/Chapter to generate the test.")
    else:
        with st.spinner("The Molecular Man AI is constructing your test..."):
            questions = fetch_questions(board, class_level, subject, topic, difficulty, num_questions)
            if questions:
                st.session_state.questions = questions
                st.session_state.test_generated = True

# -----------------------------------------------------------------------------
# Test Taking & Evaluation Interface
# -----------------------------------------------------------------------------
if st.session_state.test_generated and not st.session_state.submitted:
    st.subheader(f"Mock Test: {topic} ({subject} - {class_level})")
    st.write(f"**Difficulty:** {difficulty} | **Questions:** {len(st.session_state.questions)}")
    st.divider()
    
    # Using st.form prevents the app from rerunning every time a radio button is clicked
    with st.form("mock_test_form"):
        for i, q in enumerate(st.session_state.questions):
            st.markdown(f"**Q{i+1}. {q['question']}**")
            # Create a unique key for each radio button to capture the answer on submit
            st.radio("Select an option:", options=q["options"], key=f"user_ans_{i}", label_visibility="collapsed")
            st.write("") 
        
        submit_btn = st.form_submit_button("Submit Test", type="primary")
        if submit_btn:
            st.session_state.submitted = True
            st.rerun()

# -----------------------------------------------------------------------------
# Results & Feedback View
# -----------------------------------------------------------------------------
if st.session_state.submitted:
    st.subheader("Test Results & Analysis")
    st.divider()
    
    # Calculate Score
    score = 0
    total = len(st.session_state.questions)
    
    for i, q in enumerate(st.session_state.questions):
        user_ans = st.session_state.get(f"user_ans_{i}")
        if user_ans == q["correct_answer"]:
            score += 1

    # Display Final Score
    st.markdown(f"### Your Score: :blue[{score} / {total}]")
    st.progress(score / total)
    st.divider()

    # Detailed Feedback loop
    for i, q in enumerate(st.session_state.questions):
        user_ans = st.session_state.get(f"user_ans_{i}")
        correct_ans = q["correct_answer"]
        is_correct = (user_ans == correct_ans)
        
        st.markdown(f"**Q{i+1}. {q['question']}**")
        
        if is_correct:
            st.success(f"**Your Answer:** {user_ans} ✅")
        else:
            st.error(f"**Your Answer:** {user_ans} ❌")
            st.success(f"**Correct Answer:** {correct_ans}")
            
        with st.expander("View Explanation"):
            st.info(q["explanation"])
            
        st.write("---")

    # Reset Option
    if st.button("Start New Test"):
        reset_test()
        st.rerun()
