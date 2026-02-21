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
        3. The `correct_answer` MUST EXACTLY MATCH one of the strings in the `options` array. 
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
        3. For Numerical problems, ensure the math is 100% correct. Calculate the correct answer with exact proper units.
        4. Provide exactly 4 options. One MUST be the correct answer. The other three must be plausible distractors (e.g., answers resulting from common calculation mistakes or wrong units).
        FORMAT:
        [
          {
            "id": 1,
            "question": "Clear numerical problem with exact values",
            "options": ["Value A + Units", "Value B + Units", "Value C + Units", "Value D + Units"],
            "correct_answer": "Exact match to the correct option",
            "explanation": "Step-by-step mathematical derivation showing the formula used."
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
                cls = st.selectbox("Class", [str(i) for i in range(6, 13)], index=4) 
                diff = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"])
            with c2:
                sub = st.text_input("Subject", "Physics")
                chap = st.text_input("Chapter", "Thermodynamics")
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
                    # Both MCQ and Numerical now use the Radio button UI
                    if st.session_state.mt_q_type in ["MCQ", "Numerical"]:
                        st.radio("Choose:", q.get('options', []), key=f"q_{q['id']}", label_visibility="collapsed", index=None)
                    else:
                        st.text_area("Your Answer:", key=f"q_{q['id']}")
                    st.divider()
                
                submitted = st.form_submit_button("✅ Submit for Grading")
            
            if submitted:
                answers = {}
                all_answered = True
                
                # Validation Loop: Check if every question has an answer
                for q in st.session_state.mt_questions:
                    val = st.session_state.get(f"q_{q['id']}")
                    if val is None or str(val).strip() == "":
                        all_answered = False
                    answers[str(q['id'])] = val
                
                # Halt submission if not fully answered
                if not all_answered:
                    st.error("⚠️ You cannot submit yet! Please answer all questions before submitting the exam.")
                else:
                    # Deterministic Grading for both MCQs and Numericals
                    if st.session_state.mt_q_type in ["MCQ", "Numerical"]:
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
                    
                    # LLM Grading for Descriptive only
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
