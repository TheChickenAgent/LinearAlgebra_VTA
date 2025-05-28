# streamlit run app5.py

import streamlit as st
import os
import pandas as pd
import re
from dotenv import load_dotenv
from openai import OpenAI
import io
from fpdf import FPDF
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
import time

# Load environment variables from a .env file
load_dotenv()
OPENAI_API = os.getenv('OPENAI_API_KEY')
embedding = OpenAIEmbeddings(model="text-embedding-3-large", openai_api_key=OPENAI_API)
db_openai = Chroma(persist_directory="./vectordb/openai_vectorDB/", embedding_function=embedding) #for existing database

def get_page_numbers(page_numbers: list[str]) -> list[str]:
    """
    Get the page numbers from the metadata.

    Args:
        page_numbers (list): list of page numbers

    Returns:
        list: sorted list of page numbers
    """
    int_page_numbers = []
    for page_number in page_numbers:
        if "and" in page_number:
            page_number = page_number.split(" and ")
            page_number = [int(i) for i in page_number]
            int_page_numbers.extend(page_number)
        else:
            page_number = int(page_number)
            int_page_numbers.append(page_number)

    # Unique the page numbers
    int_page_numbers = list(set(int_page_numbers))

    # Sort the page numbers
    int_page_numbers.sort()

    # Now we need to string them again
    return [str(i) for i in int_page_numbers]


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

def stream_string_data(text: str):
    for word in text.split(" "):
        yield word + " "
        time.sleep(0.02)

def chat(help_TF_Q: dict|None = None):
    st.title("Open QA chat")

    llm = OpenAI(api_key=OPENAI_API)

    if "openai_model" not in st.session_state:
        st.session_state["openai_model"] = "gpt-3.5-turbo"
        #st.session_state["openai_model"] = "o4-mini"

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        if message["role"] == "references":
            with st.chat_message("references", avatar="📖"):
                st.markdown(message["content"])
        else:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # If this method is called through the TF questions page, we want make a query
    # to help the user understand the question and answer better.
    if isinstance(help_TF_Q, dict):
        question = help_TF_Q.get("question", "")
        explanation = help_TF_Q.get("explanation", "")
        answer = help_TF_Q.get("answer", "")
        if question=="" or explanation=="" or answer=="":
            st.error("Error: The question, explanation, or answer is missing.")
        else:
            query = f"Can you help me understand the question with answer and explanation better?"
            st.session_state.messages.append({"role": "user", "content": query})
            with st.chat_message("user"):
                st.markdown(query)
            #print(query)

            # Retrieve relevant context from the vector database
            retrieved_docs = db_openai.similarity_search(query, k=4)
            context = "\n\n".join(doc.page_content for doc in retrieved_docs)
            references = get_page_numbers([doc.metadata['page'] for doc in retrieved_docs])
            print(references)

            # Build custom prompt
            # Combine message history with the custom prompt as system message
            custom_prompt = (
                "You are an assistant for question-answering tasks in linear algebra. "
                "The user would like to get clarification on a True/False question. "
                "The question is: " + question + ". "
                "The explanation is: " + explanation + ". "
                "The answer is: " + str(answer) + ". "
                "Use the following pieces of retrieved context to aid the explanation. "
                "Please use LaTeX formatting for mathematical expressions by writing them between dollar signs."
                "For example, to write a matrix, use $\\begin{pmatrix} a & b \\\\ c & d \\end{pmatrix}$. "
                "If you don't know the answer, say that you don't know. "
                "\n\nContext:\n" + context
            )
            help_TF_Q = None  # Reset the help_TF_Q to avoid re-querying

            # Prepare messages: system prompt + previous messages + latest user query
            messages = [{"role": "system", "content": custom_prompt}]
            messages += [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages if m["role"] != "references"]
            # Overwrite the last user message to ensure it includes the context
            if messages and messages[-1]["role"] == "user":
                messages[-1]["content"] = query


            #with st.chat_message("assistant"):
            stream = llm.chat.completions.create(
                model=st.session_state["openai_model"],
                messages=messages,
                stream=False,
            )
            response = stream.choices[0].message.content

            with st.chat_message("assistant"):
                response = st.write_stream(stream_string_data(response))
            st.session_state.messages.append({"role": "assistant", "content": response})
            if references:
                with st.chat_message("references", avatar="📖"):
                    if len(references) == 1:
                        ref = f"Reference: page {references[0]}"
                    else:
                        ref = f"References: pages {", ".join(references[:-1])}, and {references[-1]}"
                    st.write(ref)
                #st.session_state.messages.append({"role": "assistant", "content": response})
                st.session_state.messages.append({"role": "references", "content": ref})

    if query := st.chat_input("Ask a question about linear algebra."):
        st.session_state.messages.append({"role": "user", "content": query})
        with st.chat_message("user"):
            st.markdown(query)
        #print(query)

        # Retrieve relevant context from the vector database
        retrieved_docs = db_openai.similarity_search(query, k=4)
        context = "\n\n".join(doc.page_content for doc in retrieved_docs)
        references = get_page_numbers([doc.metadata['page'] for doc in retrieved_docs])
        print(references)

        # Build custom prompt
        # Combine message history with the custom prompt as system message
        custom_prompt = (
            "You are an assistant for question-answering tasks in linear algebra. "
            "Use the following pieces of retrieved context to answer the question. "
            "Please use LaTeX formatting for mathematical expressions by writing them between dollar signs."
            "For example, to write a matrix, use $\\begin{pmatrix} a & b \\\\ c & d \\end{pmatrix}$. "
            "If you don't know the answer, say that you don't know. "
            "If the question is not related to linear algebra, politely decline to answer it and put at the end of the repsonse REFUSED=TRUE. "
            "\n\nContext:\n" + context
        )

        # Prepare messages: system prompt + previous messages + latest user query
        messages = [{"role": "system", "content": custom_prompt}]
        messages += [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages if m["role"] != "references"]
        # Overwrite the last user message to ensure it includes the context
        if messages and messages[-1]["role"] == "user":
            messages[-1]["content"] = query


        #with st.chat_message("assistant"):
        stream = llm.chat.completions.create(
            model=st.session_state["openai_model"],
            messages=messages,
            stream=False,
        )
        response = stream.choices[0].message.content
        # Check if the response contains REFUSED=TRUE
        if "REFUSED=TRUE" in response:
            response = response.replace("REFUSED=TRUE", "")
            references = None  # No references to show if refused
        with st.chat_message("assistant"):
            response = st.write_stream(stream_string_data(response))
        st.session_state.messages.append({"role": "assistant", "content": response})
        if references:
            with st.chat_message("references", avatar="📖"):
                if len(references) == 1:
                    ref = f"Reference: page {references[0]}"
                else:
                    ref = f"References: pages {", ".join(references[:-1])}, and {references[-1]}"
                st.write(ref)
            #st.session_state.messages.append({"role": "assistant", "content": response})
            st.session_state.messages.append({"role": "references", "content": ref})
        print(st.session_state.messages)

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

def practice_true_false_questions():
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
            1 for i, q in enumerate(st.session_state.generated_questions)
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
        pdf.cell(0, 10, f"Final Score: {score} / {st.session_state.num_questions_final}", ln=True)
        #for i, q in enumerate()
        for i, q in enumerate(st.session_state.generated_questions):
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
    st.write("# Practise True/False Questions")
    st.write("The system will generate True/False questions about Linear Algebra. You can now choose which topics you want to practice.")
    # Topic selection with radio buttons (max 5 active)
    topics = [
        "Systems of linear equations, Gaussian elimination",
        "Vector equations, Matrix",
        "Solution sets and Linear independence",
        "Linear Transformations, Matrix algebra",
        "The Inverse of a Matrix",
        "Determinants, Perspective projections",
        "Vector Spaces",
        "Eigenvalues and Eigenvectors",
        "Diagonalization",
        "Orthogonality and Symmetric Matrices"
    ]

    # Topic selection UI
    if "topics_submitted" not in st.session_state:
        st.session_state.topics_submitted = False

    if "generated_questions" not in st.session_state:
        st.session_state.generated_questions = None

    if not st.session_state.topics_submitted:
        selected_topics = st.multiselect(
            "Select up to 5 topics to practice:",
            topics,
            max_selections=5
        )
        if len(selected_topics) == 5:
            st.info("Maximum of 5 topics selected.")
        st.session_state.selected_topics = selected_topics
        
        # Slider for number of questions
        num_questions_slider = st.slider(
            "Select the number of questions to practice:",
            min_value=1,
            max_value=10,
            value=len(selected_topics),
            step=1
        )

        # Button to generate questions
        if st.button("Generate Questions"):
            if not selected_topics:
                st.warning("Please select at least one topic.")
            else:
                st.session_state.topics_submitted = True
                st.session_state.selected_topics_final = selected_topics
                st.session_state.num_questions_final = num_questions_slider
        st.stop()
    elif st.session_state.generated_questions is None:
        # Hide topic selection and slider after questions are generated
        with st.spinner("Generating questions, please wait..."):
            num_questions = str(st.session_state.num_questions_final)
            topics_str = ", ".join(st.session_state.selected_topics_final)
            custom_prompt = (
                "You are a tutor for generating True/False statements in Linear Algebra. "
                "Generate exactly " + num_questions + " True/False questions based on the selected topics. "
                "Please format as follows:\n"
                "- Each question should start with 'Q:' followed by the question text.\n"
                "- Each explanation should start with 'E:' followed by the explanation text.\n"
                "- Each answer should start with 'A:' followed by 'True' or 'False'.\n"
                "For example:\n"
                "Q: The determinant of a matrix is always non-negative.\n"
                "E: The determinant can be negative depending on the matrix. For example, $\\begin{pmatrix} 1 & 0 \\\\ 0 & -1 \\end{pmatrix}$.\n"
                "A: False\n"
                "Please use LaTeX formatting for mathematical expressions by writing them between dollar signs."
                "For example, to write a matrix, use $\\begin{pmatrix} a & b \\\\ c & d \\end{pmatrix}$. "
                "\n\nSelected topics:\n" + topics_str
            )
            llm = OpenAI(api_key=OPENAI_API)

            if "openai_model" not in st.session_state:
                st.session_state["openai_model"] = "gpt-3.5-turbo"

            # Use the correct message format for OpenAI
            response = llm.chat.completions.create(
                model=st.session_state["openai_model"],
                messages= [{"role": "system","content": custom_prompt}],
                stream=False,
            )
            response_content = response.choices[0].message.content
            # Process the response to extract questions and answers
            questions = []
            explanations = []
            answers = []
            for line in response_content.split("\n"):
                line = line.strip()
                if line.startswith("Q:"):
                    question = line[2:].strip()
                    questions.append(question)
                elif line.startswith("E:"):
                    explanation = line[2:].strip()
                    explanations.append(explanation)
                elif line.startswith("A:"):
                    answer = line[2:].strip().lower() == "true"
                    answers.append(answer)
            if len(questions) != len(answers) or len(questions) != st.session_state.num_questions_final:	
                st.error("Error: The number of questions and answers do not match the requested number.")
            time.sleep(1)  # Simulate processing time
            # Store generated questions and answers in session state
            st.session_state.generated_questions = [
                {"question": q, "explanation": e, "answer": a} for q, e, a in zip(questions, explanations, answers)
            ]
            print(st.session_state.generated_questions)
            st.session_state.question_index = 0
            st.session_state.submitted = [False] * len(questions)
            st.session_state.user_answers = [None] * len(questions)
            st.session_state.show_score = False
            st.session_state.review_md = None

    # Display all questions with separate True/False buttons
    if st.session_state.generated_questions is not None:
        st.success("Questions generated!")
        st.markdown(
            f"**Selected topics:** {', '.join(st.session_state.selected_topics_final)}  \n"
            f"**Number of questions:** {st.session_state.num_questions_final}"
        )
        st.write("### Answer the following questions:")
        for idx, question_data in enumerate(st.session_state.generated_questions):
            st.write(f"**Question {idx + 1}:** {question_data['question']}")
            col1, col2, col3 = st.columns([1, 1, 1])
            help_key = f"help_active_{idx}"
            with col1:
                if st.button(f"True", key=f"true_btn_{idx}", disabled=st.session_state.submitted[idx]):
                    user_answers = st.session_state.user_answers
                    user_answers[idx] = True
                    st.session_state.user_answers = user_answers
                    submitted = st.session_state.submitted
                    submitted[idx] = True
                    st.session_state.submitted = submitted
                    # Reset help state for this question
                    st.session_state[help_key] = False
            with col2:
                if st.button(f"False", key=f"false_btn_{idx}", disabled=st.session_state.submitted[idx]):
                    user_answers = st.session_state.user_answers
                    user_answers[idx] = False
                    st.session_state.user_answers = user_answers
                    submitted = st.session_state.submitted
                    submitted[idx] = True
                    st.session_state.submitted = submitted
                    # Reset help state for this question
                    st.session_state[help_key] = False
            # Use a session state key to track which help button was pressed
            with col3:
                if st.button("Help", key=f"help_btn_{idx}"):
                    # Set the help key for this question to True, others to False
                    for i in range(len(st.session_state.generated_questions)):
                        st.session_state[f"help_active_{i}"] = (i == idx)
            # Show chat across all columns if help is active for this question
            if st.session_state.get(help_key, False) and not st.session_state.submitted[idx]:
                st.markdown("---")
                chat(question_data)
                st.markdown("---")
            # Show feedback if answered
            if st.session_state.submitted[idx]:
                correct_answer = question_data['answer']
                explanation = question_data['explanation']
                user_answer = st.session_state.user_answers[idx]
                if user_answer == correct_answer:
                    st.success(f"Question {idx + 1}: Correct! 🎉\n\nExplanation: {explanation}")
                else:
                    st.error(f"Question {idx + 1}: Incorrect. The correct answer is {'True' if correct_answer else 'False'}.\n\nExplanation: {explanation}")

        # Optionally, show score or review after all questions are answered
        if all(st.session_state.submitted):
            score = sum(
                1 for i, q in enumerate(st.session_state.generated_questions)
                if st.session_state.user_answers[i] == q["answer"]
            )
            st.info(f"Quiz complete! Your score: {score} / {len(st.session_state.generated_questions)}")

            ## PDF option
            pdf_data = generate_review_pdf()
            st.download_button(
                label="Download Review as PDF",
                data=pdf_data,
                file_name="quiz_review.pdf",
                mime="application/pdf"
            )
            if st.button("Reset and Start Again"):
                for key in [
                    "topics_submitted",
                    "selected_topics",
                    "selected_topics_final",
                    "num_questions_final",
                    "generated_questions",
                    "question_index",
                    "submitted",
                    "user_answers",
                    "show_score",
                    "review_md"
                ]:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
        

page_names_to_funcs = {
    "Main menu": intro,
    "Linear Algebra chat": chat,
    "Practise T/F questions": practice_true_false_questions,
}

demo_name = st.sidebar.selectbox("Select a practice mode:", page_names_to_funcs.keys())
page_names_to_funcs[demo_name]()