import streamlit as st
import os
import pickle
import re


DATA_DIR = "user-testing/data/"


def list_pickle_files(directory):
    return [f for f in os.listdir(directory) if f.endswith('.pkl')]

def load_conversation(filepath):
    with open(filepath, "rb") as f:
        data = pickle.load(f)
        return data
    
def read_questions_answers():
    # Split out True/False questions
    exam_questions_TF = []
    exam_answers_TF = []

    with open('exams/together2.tex', 'r', encoding='utf-8') as file:
        tex_content = file.read()
        questions, answers = extract_question_answer(tex_content)
        #print(f"Total Questions: {len(questions)}")
        #print(f"Total Answers: {len(answers)}\n")
        if len(questions) != len(answers):
            print("Warning: The number of questions and answers do not match!")
        for idx, (q, a) in enumerate(zip(questions, answers), 1):
            #print(f"Question {idx}:\n{q}\n")
            #print(f"Answer {idx}:\n{a}\n")
            exam_questions_TF.append(q)
            exam_answers_TF.append(a)
    return exam_questions_TF, exam_answers_TF

def extract_question_answer(tex_content):
    # Extract content within the enumerate environment
    enum_match = re.search(r'\\begin{enumerate}(.*?)\\end{enumerate}', tex_content, re.DOTALL)
    if not enum_match:
        return [], []
    enum_content = enum_match.group(1)

    # Find all questions (\item ... \begin{solutionorbox})
    question_blocks = re.findall(
        r'\\item(.*?)(?=\\begin{solutionorbox})',
        enum_content, re.DOTALL
    )

    # Find all answers (\begin{solutionorbox} ... \end{solutionorbox})
    answer_blocks = re.findall(
        r'\\begin{solutionorbox}\[[^\]]*\]\s*(.*?)\\end{solutionorbox}',
        enum_content, re.DOTALL
    )
    questions = [q.strip() for q in question_blocks]
    answers = [a.strip() for a in answer_blocks]
    return questions, answers



############# STREAMLIT APP #############
st.title("Conversation Viewer")

files = list_pickle_files(DATA_DIR)
selected_file = st.selectbox("Select a conversation file", files)
if selected_file:
    data = load_conversation(os.path.join(DATA_DIR, selected_file))
    question = data.get("selected_question", "No question selected")
    selected_question_number = int(question[1:]) - 1  # Convert Q1 to index 0
    questions, _ = read_questions_answers()
    question = questions[selected_question_number]

    # Remove LaTeX bold formatting
    question = question.replace("\\textbf{always}", "*always*")  
    question = question.replace("\\textbf{Every}", "*Every*")
    question = question.replace("\\textbf{any}", "*any*")
    question = question.replace("\\textbf{rotation}", "*rotation*")
    question = question.replace("\\textbf{distinct}", "*distinct*")

    st.write(f"### Q{selected_question_number+1}: {question}")
    conversation = data.get("messages", [])

    st.subheader("Conversation")
    for message in conversation:
        role = message.get("role", "unknown")
        content = message.get("content", "")
        if role == "user":
            with st.chat_message("user"):
                st.markdown(content)
        elif role == "assistant":
            with st.chat_message("assistant"):
                content = content.replace("\\$", "$")
                st.markdown(content)
        else:
            with st.chat_message("system"):
                st.markdown(content)
    st.write("END OF CONVERSATION")