import streamlit as st
from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from langchain_community.embeddings import CohereEmbeddings
from langchain_groq import ChatGroq

import time

PINECONE_API_KEY = st.secrets.PINECONE_API_KEY
pc = Pinecone(api_key=PINECONE_API_KEY)
embeddings = CohereEmbeddings(model="embed-english-v3.0", user_agent="langchain")
llm = ChatGroq(
        model="mixtral-8x7b-32768",
        temperature=0,
        max_tokens=None,
        timeout=None,
        max_retries=1,
        # other params...
    )

#form for the teacher to insert the corrected question and answer
st.markdown("## Correção de questões")
st.markdown("Insira a questão e a resposta correta.")
with st.form("form"):
    question = st.text_area("Questão")
    answer = st.text_area("Resposta")
    submit = st.form_submit_button("Enviar")

if submit == True:
    #Salvando a questão e a resposta no banco de dados
    index_name = st.session_state.index_name

    #pc.delete_index(index_name)

    if index_name not in pc.list_indexes().names():
        index = pc.create_index(
            name=index_name,
            dimension=1024, # Replace with your model dimensions
            metric="cosine", # Replace with your model metric
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1"
            ) 
        )

    index = pc.Index(index_name)
    while not pc.describe_index(index_name).status['ready']:  
        time.sleep(1)

    docsearch = PineconeVectorStore.from_texts(
        texts=[question],
        embedding=embeddings,
        metadatas=[{"resposta":answer}],
        index_name=index_name,
    )
    st.markdown("A questão foi corrigida e salva no banco de dados.")
    time.sleep(1)
