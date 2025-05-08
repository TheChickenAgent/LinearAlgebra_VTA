# streamlit run app2.py

import streamlit as st
import os
from dotenv import load_dotenv
from openai import OpenAI


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
    # Load environment variables from a .env file
    load_dotenv()
    OPENAI_API = os.getenv('OPENAI_API_KEY')

    ##### Streamlit app

    st.title("ChatGPT-like clone")

    client = OpenAI(api_key=OPENAI_API)

    if "openai_model" not in st.session_state:
        st.session_state["openai_model"] = "gpt-3.5-turbo"

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("What is up?"):
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

page_names_to_funcs = {
    "—": intro,
    "Linear Algebra chat Demo": plotting_demo,
    #"Mapping Demo": mapping_demo,
    #"DataFrame Demo": data_frame_demo
}

demo_name = st.sidebar.selectbox("Select a practice mode:", page_names_to_funcs.keys())
page_names_to_funcs[demo_name]()