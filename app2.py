# streamlit run app2.py

import streamlit as st
import os
from dotenv import load_dotenv
from openai import OpenAI


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


def plotting_demo():
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

def generate_question():
    st.write("#### Question:")
    st.write("Is the following system of equations consistent?")
    st.write("1. 2x + 3y = 5")
    st.write("2. 4x + 6y = 10")

def sle_practise():
    st.write("# Practise SLE")
    st.write("### The system will generate True/False questions about solving linear systems of equations.")

    generate_question_but = st.button("Generate a question")
    if generate_question_but:
        generate_question()
        true_button = st.button("True")
        false_button = st.button("False")
        submit_button = st.button("Submit")

        if "user_answer" not in st.session_state:
            st.session_state["user_answer"] = None

        if true_button:
            st.session_state["user_answer"] = "True"
        elif false_button:
            st.session_state["user_answer"] = "False"

        if submit_button:
            if st.session_state["user_answer"]:
                st.write(f"You selected: {st.session_state['user_answer']}")
            else:
                st.write("Please select an answer before submitting.")

        #answer = st.radio(
        #    "",
        #    ["True", "False"],
        #    index=None,
        #)
        #if answer:
        #    print(answer)
        

page_names_to_funcs = {
    "Main menu": intro,
    "Linear Algebra chat": plotting_demo,
    "Practise SLE": sle_practise,
}

demo_name = st.sidebar.selectbox("Select a practice mode:", page_names_to_funcs.keys())
page_names_to_funcs[demo_name]()