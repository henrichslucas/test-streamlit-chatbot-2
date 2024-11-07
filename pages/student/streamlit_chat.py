import streamlit as st
from groq import Groq
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone
from langchain_community.embeddings import CohereEmbeddings

pc = Pinecone(api_key=st.secrets.PINECONE_API_KEY)
embeddings = CohereEmbeddings(model="embed-english-v3.0", user_agent="langchain")


def set_model():
    client = Groq(api_key=st.secrets.GROQ_API_KEY)
    
    # Set a default model
    if "ai_model" not in st.session_state:
        st.session_state["ai_model"] = "mixtral-8x7b-32768"

    return client


def sort_question_answer(data):
    full_data = []

    for d in data:
        full_data.append(str(d))
  
    return full_data

def response_generator(client, question, data):
    context = []

    template = sort_question_answer(data)
    #print(template)

    for m in st.session_state.messages:
        context.append({"role": m["role"], "content": m["content"]})

    stream = client.chat.completions.create(
        stream = True,
        model = st.session_state["ai_model"],
        temperature=0.1,
        top_p=0.2,
        messages = [
            {
                "role": "system", "content": f"Você é um assistente escolar com o objetivo de ajudar alunos a sanarem suas dúvidas de forma simples e ágil, com base na resposta providenciada pelo professor. A resposta SEMPRE deve ser colocada entre as tags <response> </response>'. Responda exclusivamente em português brasileiro e NUNCA PASSE DE uma frase na resposta. Todo o conteudo corrigido pelo professor está a seguir: {template}. Voce tambem pode utilizar o historico da conversa para responder perguntas, desde que elas estejam de acordo com o conteudo corrigido. Aqui esta o historico:{context}. Nao se esqueca de ser educado e prestativo com o aluno, e nunca adicione comentarios adicionais. Nunca escreva as tags <response>, apenas o que estiver entre elas. Caso o conteudo corrigido esteja vazio, responda com 'Desculpe, o repositório esta sem conteudos atualmente, peça para seu professor adicionar algum gabarito!'"
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

def init_chat_session():

    new_chat()

    content = "Ola, eu sou o SaberIA. Pergunte-me algo!"
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
        st.button(("Iniciar novo chat"), on_click=init_chat_session)

def write_response(client,data,question):

    stream = response_generator(client, question, data)
    for chunk in stream:
        content = chunk.choices[0].delta.content
        if content is not None:
            content = content.replace("<response>", "")
            yield content

def get_chatbot_response(client):   
    docsearch = PineconeVectorStore(index_name=st.session_state.index_name, embedding=embeddings)

    question = st.session_state.user_messages[-1]["content"]

    retriever = docsearch.as_retriever(
        search_type="mmr",
        search_kwargs={'k': 1000, 'lambda_mult': 0.25}
    )
    
    data = retriever.invoke(question)

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
