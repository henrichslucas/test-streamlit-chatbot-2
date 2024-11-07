from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from langchain_community.embeddings import CohereEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from PyPDF2 import PdfReader

import streamlit as st
import time
import os

PDF_STORAGE_DIR = "uploaded_pdfs"
LLAMA_API_KEY = st.secrets.LLAMA_API_KEY
PINECONE_API_KEY = st.secrets.PINECONE_API_KEY

pc = Pinecone(api_key=PINECONE_API_KEY)
embeddings = CohereEmbeddings(model="embed-english-v3.0", user_agent="langchain")

def init_index():
    index_name = st.session_state.index_name

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

    
    # print(index.describe_index_stats().to_dict())
    while not pc.describe_index(index_name).status['ready']:  
        time.sleep(1)

    return index, index_name

def fix_text(raw_text):
    texto_corrigido = " ".join(raw_text.splitlines())
    texto_corrigido = " ".join(texto_corrigido.split())
    # print(texto_corrigido)
    return texto_corrigido

def process_document(document_binary):
    #Process the document
    os.makedirs(PDF_STORAGE_DIR, exist_ok=True)
    pdf_filename = "document.pdf"
    pdf_path = os.path.join(PDF_STORAGE_DIR, pdf_filename)

    with open(pdf_path, "wb") as f:
        f.write(document_binary.getvalue())

    try:
        final_text = []
        parser = PdfReader(pdf_path)
        number_of_pages = len(parser.pages)
        for page_number in range(number_of_pages):
            page = parser.pages[page_number]
            raw_text = page.extract_text()
            text = fix_text(raw_text)
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=200)
            splits = text_splitter.split_text(text) ##   array com string grandona
            final_text.append(splits)
            print(final_text)
            # page = parser.pages[0]
            # print(parser.pages[1])
            # raw_text = page.extract_text()
            # text = fix_text(raw_text)
        return final_text

    except Exception as e:
        os.remove(pdf_path)
        raise ValueError(f"Error processing file: {str(e)}") from e

def set_form():
    st.markdown("## Correção de questões")
    st.markdown("Insira a questão e a resposta correta.")
    with st.form("form"):
        question = st.text_area("Questão")
        answer = st.text_area("Resposta")
        submit = st.form_submit_button("Enviar")
        if len(question) == 0:
            return "Pergunta não pode ser vazia", False

        return f"Pergunta: {question}, resposta: {answer}", submit

def upload_doc(embeddings):
    document_binary = st.file_uploader(
        label="Carregue um documento PDF",
        type=["pdf"],
        accept_multiple_files=False,
    )

    with st.spinner('Processando documento...'):
        if document_binary is not None:
            # Process the document
            document = process_document(document_binary) # varios arrays com strings

            index, index_name = init_index()

            for doc in document:
                for item in doc:
                    vec_store = PineconeVectorStore.from_texts(
                        texts=[item],
                        embedding=embeddings,
                        index_name=index_name,
                    )

            st.success("Documento processado com sucesso!")
            time.sleep(1)

            # Display the document text
            st.markdown("## Texto do documento adicionado")
            st.markdown(document)

def reset_index(index, index_name):
    if index.describe_index_stats().to_dict()['total_vector_count']>0:
        # # If vector store becomes too big
        print("RESETTING VECTOR STORE")
        delete_response = index.delete(delete_all=True)
        st.warning("Repositório de perguntas reiniciando...")
        time.sleep(5)
        st.success("Repositório de perguntas reiniciado com sucesso!")
        index = pc.Index(index_name)
    else:
        st.warning("Repositório de perguntas já está vazio.")

    
def main():
    index, index_name = init_index()

    with st.sidebar:
        st.button(("Reiniciar repositório de perguntas"), on_click=reset_index, args=(index, index_name))
    #form to insert the corrected question and answer
    submit = False
    question, submit, = set_form()

    ## field to upload the document
    upload_doc(embeddings)

    if submit == True:
        #Salvando a questão e a resposta no banco de dados

        vec_store = PineconeVectorStore.from_texts(
            texts=[question],
            embedding=embeddings,
            index_name=index_name,
        )

        st.success("A questão foi corrigida e salva no banco de dados.")
        time.sleep(1)

main()
