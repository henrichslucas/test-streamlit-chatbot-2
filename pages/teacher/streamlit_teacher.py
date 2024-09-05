import streamlit as st
from pinecone import Pinecone, ServerlessSpec
#from llama_index.embeddings.cohere import CohereEmbedding
from langchain_groq import ChatGroq
from langchain_ollama import OllamaEmbeddings
import uuid




PINECONE_API_KEY ="241a18ba-a13e-4c33-9ab0-a405c14e4a4b"
pc = Pinecone(api_key=PINECONE_API_KEY)
index_name = "quickstart"

def handle_embedding(text_to_embed):
    embed = OllamaEmbeddings(
        model="llama3.1"
    )

    vectors = []
    dimension = 3

    vector = embed.embed_query(text_to_embed)
    vectors.append(vector[:dimension])

    return vectors, dimension

def handle_pinecone(vectors, answer, vec_dimension):
    pc.delete_index(index_name)

    if index_name not in pc.list_indexes().names():
        pc.create_index(
            name=index_name,
            dimension=vec_dimension, # Replace with your model dimensions
            metric="cosine", # Replace with your model metric
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1"
            ) 
        )

    index = pc.Index(index_name)
    data = []
    vec_id = uuid.uuid4()


    data.append({"id":f"vec_{vec_id}", "values": vectors[0], "metadata": {"answer": answer}})
    print(data)
    index.upsert(
        data,
        namespace="example-namespace1"
    )

    st.markdown("## Questão corrigida com sucesso!")
    st.markdown("A questão foi corrigida e salva no banco de dados.")

    return index

#     # print(index.describe_index_stats())
#     query_results1 = index.query(
#     namespace="example-namespace1",
#     vector=[1.0, 1.5],
#     top_k=3,
#     include_values=True
# )
#     print(query_results1)

#form for the teacher to insert the corrected question and answer
st.markdown("## Correção de questões")
st.markdown("Insira a questão e a resposta correta.")
with st.form("form"):
    question = st.text_area("Questão")
    answer = st.text_area("Resposta")
    submit = st.form_submit_button("Enviar")

if submit == True:
    embedded_data, vector_dimension = handle_embedding(question)
    pc_index = handle_pinecone(embedded_data, answer, vector_dimension)
    res = pc_index.fetch(["vec_1"])#['metadata'] # resposta
    st.markdown(res)
    #st.markdown(res[0]['metadata']['answer'])
    #pc_index.fetch(["vec_1"])['values'] # pergunta embedada