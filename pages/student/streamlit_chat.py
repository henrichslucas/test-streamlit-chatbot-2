import streamlit as st
from groq import Groq
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone
from langchain_community.embeddings import CohereEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings

pc = Pinecone(api_key=st.secrets.PINECONE_API_KEY)
# embeddings = CohereEmbeddings(model="embed-english-v3.0", user_agent="langchain")
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-mpnet-base-v2"
)

def set_model():
    client = Groq(api_key=st.secrets.GROQ_API_KEY)
    if "ai_model" not in st.session_state:
        st.session_state["ai_model"] = "mixtral-8x7b-32768"

    return client

def response_generator(client, question, data):
    context = []

    template = data

    for m in st.session_state.messages:
        context.append({"role": m["role"], "content": m["content"]})

    stream = client.chat.completions.create(
        stream = True,
        model = st.session_state["ai_model"],
        temperature=0.2,
        top_p=0.2,
        messages = [
            {
                "role": "system", "content": f"Você é um assistente escolar com o objetivo de ajudar alunos a sanarem suas dúvidas de forma simples e ágil, com base na resposta providenciada pelo professor. A resposta SEMPRE deve ser colocada entre as tags <response> </response> e nunca pode passar de duas frases. Responda exclusivamente em português brasileiro e NUNCA PASSE de uma frase na resposta. Existe uma regra primordial para gerar as respostas: Ela sempre tem que estar alinhada com o gabarito oficial fornecido pelo professor. Esse gabarito tem diversas questões sorteadas, entao, selecione apenas a questão e resposta relevantes. Caso nao tenha gabarito, diga 'Desculpe, o gabarito ainda não tem essa pergunta corrigida. Solicite ao seu professor!'. O gabarito oficial está a seguir: {template}. Para recapitular perguntas feitas anteriormente, consulte o histórico de mensagens a seguir: {context}."
            },
            {
                "role": "user",
                "content": f"{question}"
            },
        ],
        stop="</response>",
    )
    return stream
    
def new_chat():
    st.session_state.messages = []
    st.session_state.user_messages = []
    st.session_state.assistant_messages = []

    content = "Ola, eu sou o SaberIA. Pergunte-me algo!"
    st.session_state.messages.append({"role": "assistant", "content": content})
    st.session_state.assistant_messages.append({"role": "assistant", "content": content}) 

def init_chat_session():
    if "messages" not in st.session_state:
        new_chat()

def reset_chat():
    new_chat()

def display_chat_history():
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

def handle_conversation():
    if prompt := st.chat_input("Pergunte algo..."):

        st.chat_message("user").markdown(prompt)
        user_message = {"role": "user", "content": prompt}

        st.session_state.messages.append(user_message)
        st.session_state.user_messages.append(user_message)

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
        st.button(("Iniciar novo chat"), on_click=reset_chat)

def write_response(client,data,question):

    stream = response_generator(client, question, data)
    for chunk in stream:
        content = chunk.choices[0].delta.content
        if content is not None:
            if content in {"<response>","<", "response", ">"}:
                content = ""
            yield content

def get_chatbot_response(client):   
    docsearch = PineconeVectorStore(index_name=st.session_state.index_name, embedding=embeddings)

    question = st.session_state.user_messages[-1]["content"]

    raw_data = docsearch.search(question,search_type='similarity_score_threshold',k=10, score_threshold=0.7)
    if len(raw_data) > 0:
        data = raw_data[0].page_content
    else:
        data = ""

    with st.chat_message("assistant"):
        ai_response =  st.write_stream(write_response(client,data,question))
        st.session_state.messages.append({"role": "assistant", "content": ai_response})
        st.session_state.assistant_messages.append({"role": "assistant", "content": ai_response})

def main():

    handle_page()

    init_chat_session()

    display_chat_history()

    handle_conversation()

main()
