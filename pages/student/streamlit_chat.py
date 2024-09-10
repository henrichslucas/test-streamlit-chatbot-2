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

# def response_generator(client):
#     res = client.chat.completions.create(
#         stream = False,
#         model = st.session_state["ai_model"],
#         messages = [
#             {"role": m["role"], "content": m["content"]} for m in st.session_state.messages
#         ]
#     )
#     return res
    
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
    
    if "index_name" not in st.session_state:
        st.session_state.index_name = "kb-teacher"

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
        

def get_chatbot_response(client):   
    docsearch = PineconeVectorStore(index_name=st.session_state.index_name, embedding=embeddings)

    question = st.session_state.user_messages[-1]["content"]

    prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
                "Voce é um assistente escolar, voltado para o ensino medio. Responda apenas em portugues brasileiro. Use no máximo uma frase para gerar a resposta, você JAMAIS deve ultrapassar uma frase. Use este dado de consulta para basear sua resposta: {data}."
        ),
        ("human", "{input}"),
    ]
    )

    chain = prompt | llm

    data = docsearch.search(question,search_type='similarity_score_threshold',k=1, score_threshold=0.8)

    if "No relevant docs were retrieved" in data or data == []:
        with st.chat_message("assistant"):
            res = "Desculpe, a resposta para essa pergunta nao foi encontrada na base de dados. Peça uma revisão ao professor."
            st.markdown(res)
        st.session_state.messages.append({"role": "assistant", "content": res})
        st.session_state.assistant_messages.append({"role": "assistant", "content": res})
        ai_response = None
    else:
        ai_response = chain.invoke(
            {
                "input": question,
                "data": data[0].metadata['resposta']
            }
        )
        ai_response = ai_response.content
        
        with st.chat_message("assistant"):
            st.markdown(ai_response)
        st.session_state.messages.append({"role": "assistant", "content": ai_response}) #adicionando no histórico de mensagens geral
        st.session_state.assistant_messages.append({"role": "assistant", "content": ai_response})#adicionando no histórico de mensagens do bot

    return ai_response

def main():

    handle_page()

    init_chat_session()

    display_chat_history()

    handle_conversation()

main()
