import streamlit as st
from groq import Groq
import os
import random

API_KEY = st.secrets.GROQ_API_KEY

def set_model():
    client = Groq(api_key=API_KEY)

    # Set a default model
    if "ai_model" not in st.session_state:
        st.session_state["ai_model"] = "llama-3.1-8b-instant"

    return client

def response_generator(client):
    res = client.chat.completions.create(
        stream = False,
        model = st.session_state["ai_model"],
        messages = [
            {"role": m["role"], "content": m["content"]} for m in st.session_state.messages
        ]
    )
    return res
    
def new_chat():
    st.session_state.messages = []

def init_chat_session():
    if "messages" not in st.session_state:
        st.session_state.messages = []
        content = "Ola, eu sou o chatbot do Lucas. Pergunte-me algo!"
        st.session_state.messages.append({"role": "assistant", "content": content}) #adicionando no histórico de mensagens

def display_chat_history():
    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

def handle_conversation():
    if prompt := st.chat_input("Pergunte algo..."):

        st.chat_message("user").markdown(prompt)

        st.session_state.messages.append({"role": "user", "content": prompt}) #adicionando no histórico de mensagens

        get_chatbot_response(set_model())

        return prompt
    else:
        return None

def handle_page():
    st.markdown("## 🤖CHAT COM IA🤖")
    st.sidebar.title("Disciplinas")
    st.sidebar.markdown("Selecione a disciplina para conversar com o chatbot.")
    with st.sidebar:
        st.markdown("## 🧠 Escolha a disciplina")
        st.selectbox("Disciplinas", ["História"])
        

def get_chatbot_response(client):   
    with st.chat_message("assistant"):
        res = response_generator(client).choices[0].message.content
        st.markdown(res)
    st.session_state.messages.append({"role": "assistant", "content": res}) #adicionando no histórico de mensagens

    return res


handle_page()

init_chat_session()

display_chat_history()

handle_conversation()

