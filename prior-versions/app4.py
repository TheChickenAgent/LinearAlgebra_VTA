# streamlit run app4.py

import streamlit as st
import os
from dotenv import load_dotenv
from openai import OpenAI
import io
from fpdf import FPDF

# Load environment variables from a .env file
load_dotenv()
OPENAI_API = os.getenv('OPENAI_API_KEY')


def intro():
    st.write("# Virtual Teaching Assistant for Linear Algebra.👋 :mortar_board: :computer: :books: :school:")
    st.write("## :warning: THIS TOOL IS UNDER DEVELOPMENT :construction_worker:")
    #st.sidebar.success("Select a practice mode.")

    st.markdown(
        """
        This app is a virtual teaching assistant for linear algebra, powered by an LLM.
        It is designed to help students learn linear algebra concepts, like:
        - solving linear systems of equations;
        - matrix algebra;
        - determinants;
        - eigenvalues and eigenvectors;
        through the use of a chat interface and true/false questions.
    """
    )


def chat():
    st.title("Open QA chat")

    client = OpenAI(api_key=OPENAI_API)

    if "openai_model" not in st.session_state:
        st.session_state["openai_model"] = "gpt-3.5-turbo"

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask a question about linear algebra."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            stream = client.chat.completions.create(
                model=st.session_state["openai_model"],
                messages=[
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ],
                stream=True,
            )
            response = st.write_stream(stream)
        st.session_state.messages.append({"role": "assistant", "content": response})

def generate_questions():
    
    # List of True/False questions with answers
    questions = [
        {
            "question": "If a square matrix A is invertible, then its determinant is zero.",
            "answer": False
        },
        {
            "question": "The transpose of a product of two matrices equals the product of their transposes in reverse order.",
            "answer": True
        },
        {
            "question": "All eigenvalues of an orthogonal matrix have absolute value 1.",
            "answer": True
        }
    ]
    return questions

def sle_practise():
    questions = generate_questions()
    num_questions = len(questions)

    # === Session State Initialization ===
    if "question_index" not in st.session_state:
        st.session_state.question_index = 0
    if "submitted" not in st.session_state:
        st.session_state.submitted = [False] * num_questions
    if "user_answers" not in st.session_state:
        st.session_state.user_answers = [None] * num_questions
    if "show_score" not in st.session_state:
        st.session_state.show_score = False
    if "review_md" not in st.session_state:
        st.session_state.review_md = None

    # === Navigation Callbacks ===
    def go_to_next_question():
        if st.session_state.question_index < num_questions - 1:
            st.session_state.question_index += 1

    def go_to_previous_question():
        if st.session_state.question_index > 0:
            st.session_state.question_index -= 1

    def submit_answer(choice):
        index = st.session_state.question_index
        st.session_state.user_answers[index] = (choice == "True")
        st.session_state.submitted[index] = True

    def all_questions_answered():
        return all(st.session_state.submitted)

    def calculate_score():
        return sum(
            1 for i, q in enumerate(questions)
            if st.session_state.user_answers[i] == q["answer"]
        )

    def generate_review_markdown():
        lines = ["# Quiz Review\n"]
        score = calculate_score()
        lines.append(f"## Final Score: {score} / {num_questions}")
        for i, q in enumerate(questions):
            user_ans = st.session_state.user_answers[i]
            correct = q["answer"]
            result = "✅ Correct" if user_ans == correct else "❌ Incorrect"
            lines.append(f"### Question {i+1}: {q['question']}")
            #lines.append(f"**Q:** {q['question']}")
            lines.append(f"- Your answer: **{user_ans}**")
            lines.append(f"- Correct answer: **{correct}**")
            lines.append(f"- Result: {result}\n")

        return "\n".join(lines)


    def generate_review_pdf():
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        score = calculate_score()
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, "Quiz Review", ln=True)
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 10, f"Final Score: {score} / {num_questions}", ln=True)

        for i, q in enumerate(questions):
            user_ans = st.session_state.user_answers[i]
            correct = q["answer"]
            result = "Correct" if user_ans == correct else "Incorrect"

            pdf.ln(5)
            pdf.set_font("Arial", 'B', 12)
            pdf.multi_cell(0, 10, f"Question {i+1}: {q['question']}")
            pdf.set_font("Arial", size=12)
            pdf.cell(0, 10, f"- Your answer: {user_ans}", ln=True)
            pdf.cell(0, 10, f"- Correct answer: {correct}", ln=True)
            pdf.cell(0, 10, f"- Result: {result}", ln=True)

        # Get PDF as bytes
        pdf_str = str(pdf.output(dest='S'))
        pdf_bytes = pdf_str.encode('latin1')
        return io.BytesIO(pdf_bytes)

    # === Main UI ===
    st.write("# Practise SLE")
    st.write("The system will generate True/False questions about solving linear systems of equations.")
    index = st.session_state.question_index
    question = questions[index]

    #st.title("Linear Algebra: True/False Quiz")
    st.write(f"### Question {index + 1} of {num_questions}")
    st.write(question["question"])

    # Show previous answer if present
    previous_answer = st.session_state.user_answers[index]
    default_index = ["True", "False"].index("True" if previous_answer else "False") if previous_answer is not None else None

    user_choice = st.radio(
        "Select your answer:",
        options=["True", "False"],
        index=default_index if default_index is not None else None,
        key=f"radio_{index}"
    )

    # Submit button
    if st.button("Submit Answer") and user_choice is not None:
        submit_answer(user_choice)

    # Feedback
    if st.session_state.submitted[index]:
        correct = st.session_state.user_answers[index] == question["answer"]
        if correct:
            st.success("Correct!")
        else:
            st.error("Incorrect.")

    # Navigation buttons
    col1, col2 = st.columns(2)
    with col1:
        if index > 0:
            st.button("Previous Question", on_click=go_to_previous_question)
    with col2:
        if index < num_questions - 1:
            st.button("Next Question", on_click=go_to_next_question)

    # Show score & generate review
    if all_questions_answered() and not st.session_state.show_score:
        if st.button("Finish and Show Score"):
            st.session_state.show_score = True
            #st.session_state.review_file = True

    if st.session_state.show_score:
        score = calculate_score()
        st.markdown(f"## ✅ Final Score: {score} / {num_questions}")
        
        ## Markdown option
        #md_data = generate_review_markdown()
        #st.download_button(
        #    "Download Review as Markdown",
        #    md_data,
        #    file_name="quiz_review.md"
        #)

        ## PDF option
        pdf_data = generate_review_pdf()
        st.download_button(
            label="Download Review as PDF",
            data=pdf_data,
            file_name="quiz_review.pdf",
            mime="application/pdf"
        )

        

page_names_to_funcs = {
    "Main menu": intro,
    "Linear Algebra chat": chat,
    "Practise SLE": sle_practise,
}

demo_name = st.sidebar.selectbox("Select a practice mode:", page_names_to_funcs.keys())
page_names_to_funcs[demo_name]()