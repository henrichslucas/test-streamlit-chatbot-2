import streamlit as st
from groq import Groq
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.embeddings import CohereEmbeddings

pc = Pinecone(api_key=st.secrets.PINECONE_API_KEY)
embeddings = CohereEmbeddings(model="embed-english-v3.0", user_agent="langchain")

llm = ChatGroq(
        model="mixtral-8x7b-32768",
        temperature=0,
        max_tokens=None,
        timeout=None,
        max_retries=1,
    )

def set_model():
    client = Groq(api_key=st.secrets.GROQ_API_KEY)
    
    # Set a default model
    if "ai_model" not in st.session_state:
        st.session_state["ai_model"] = "llama-3.1-8b-instant"

    return client

def response_generator(client, question, data):
    context = []

    for m in st.session_state.messages:
        context.append({"role": m["role"], "content": m["content"]})

    if data:    
        data = data[0].metadata.get("resposta")

    stream = client.chat.completions.create(
        stream = True,
        model = st.session_state["ai_model"],
        temperature=0.3,
        top_p=0.5,
        messages = [
            {
                "role": "system", "content": f"Você é um assistente escolar com o objetivo de ajudar alunos a sanarem suas dúvidas de forma simples e ágil, com base na resposta providenciada pelo professor. Responda exclusivamente em português brasileiro e use no máximo duas frases para responder. Utilize o contexto da conversa para recapitular perguntas já feitas. {context}. A resposta do professor está a seguir: {data}. Caso esteja vazio, responda com base no seu conhecimento."
            },
            {
                "role": "user",
                "content": f"{question}"
            },
        ]
    )
    return stream
    
def new_chat():
    st.session_state.messages = []
    st.session_state.user_messages = []
    st.session_state.assistant_messages = []

def init_chat_session():
    if "messages" not in st.session_state:
        new_chat()

        content = "Ola, eu sou o assistente escolar do Lucas Henrichs. Pergunte-me algo!"
        st.session_state.messages.append({"role": "assistant", "content": content}) #adicionando no histórico de mensagens
        st.session_state.assistant_messages.append({"role": "assistant", "content": content}) #adicionando no histórico de mensagens do bot

def display_chat_history():
    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

def handle_conversation():
    if prompt := st.chat_input("Pergunte algo..."):

        st.chat_message("user").markdown(prompt)
        user_message = {"role": "user", "content": prompt}

        st.session_state.messages.append(user_message) #adicionando no histórico de mensagens geral
        st.session_state.user_messages.append(user_message) #adicionando no histórico de mensagens do usuário

        get_chatbot_response(set_model())

        return prompt
    else:
        return None

def handle_page():
    st.sidebar.title("Disciplinas")
    st.sidebar.markdown("Selecione a disciplina para conversar com o chatbot.")
    with st.sidebar:
        st.markdown("## 🧠 Escolha a disciplina 🧠")
        st.selectbox("Disciplinas", ["História"])
        st.button(("Iniciar novo chat"), on_click=new_chat)

def write_response(client,data,question):

    stream = response_generator(client, question, data)
    for chunk in stream:
        content = chunk.choices[0].delta.content
        if content is not None:
            yield content
        

def get_chatbot_response(client):   
    docsearch = PineconeVectorStore(index_name=st.session_state.index_name, embedding=embeddings)

    question = st.session_state.user_messages[-1]["content"]

    data = docsearch.search(question,search_type='similarity_score_threshold',k=1, score_threshold=0.8)

    with st.chat_message("assistant"):
        ai_response =  st.write_stream(write_response(client,data,question))
        st.session_state.messages.append({"role": "assistant", "content": ai_response}) #adicionando no histórico de mensagens geral
        st.session_state.assistant_messages.append({"role": "assistant", "content": ai_response})#adicionando no histórico de mensagens do bot

def main():

    handle_page()

    init_chat_session()

    display_chat_history()

    handle_conversation()

main()
