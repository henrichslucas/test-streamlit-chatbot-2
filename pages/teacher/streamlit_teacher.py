from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from langchain_community.embeddings import CohereEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from PyPDF2 import PdfReader

import streamlit as st
import time
import os
import hmac

PDF_STORAGE_DIR = "uploaded_pdfs"
LLAMA_API_KEY = st.secrets.LLAMA_API_KEY
PINECONE_API_KEY = st.secrets.PINECONE_API_KEY

pc = Pinecone(api_key=PINECONE_API_KEY)
#embeddings = CohereEmbeddings(model="embed-english-v3.0", user_agent="langchain")
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-mpnet-base-v2"
)

def check_password() -> bool:
    """
    Checks if the user entered the correct password.

    Returns:
        bool: True if the password is correct, False otherwise.
    """
    st.session_state.TEACHER_PASSWD = ""

    def password_entered() -> None:
        """Validates the entered password and updates the session state."""
        if hmac.compare_digest(st.session_state["TEACHER_PASSWD"], st.secrets["TEACHER_PASSWD"]):
            st.session_state["password_correct"] = True
            del st.session_state["TEACHER_PASSWD"]
        else:
            st.session_state["password_correct"] = False

    if st.session_state.get("password_correct", False):
        return True

    st.markdown("# 🖥️🔒 Area do professor")
    st.markdown("Essa página é exclusiva dos professores.")

    st.text_input(
        "Insira o código de segurança:", type="password", on_change=password_entered, key="TEACHER_PASSWD"
    )

    if "password_correct" not in st.session_state:
        return False

    if not st.session_state["password_correct"]:
        st.error("Incorrect password!")
        return False

    return True

def init_index():
    index_name = st.session_state.index_name
    
    if index_name not in pc.list_indexes().names():
        if st.session_state.index_name == "tcc-vectorstore-cohere":
            # Cohere index
            index = pc.create_index(
                name=index_name,
                dimension=1024, # Replace with your model dimensions
                metric="cosine", # Replace with your model metric
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-east-1"
                ) 
            )
        else:
            # HuggingFace index
            index = pc.create_index(
                name=index_name,
                dimension=768, # Replace with your model dimensions
                metric="cosine", # Replace with your model metric
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-east-1"
                ) 
            )
    index = pc.Index(index_name)
    placeholder = st.empty()
    with placeholder.container():
        st.warning("Aguarde enquanto o repositório de perguntas está sendo carregado...")
    while not pc.describe_index(index_name).status['ready']:  
        time.sleep(1)
    placeholder.empty()

    return index, index_name

def fix_text(raw_text):
    texto_corrigido = " ".join(raw_text.splitlines())
    texto_corrigido = " ".join(texto_corrigido.split())
    return texto_corrigido

def process_document(document_binary):
    with st.spinner('Processando documento...'):

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
                splits = text_splitter.split_text(text)
                final_text.append(splits)

            return final_text

        except Exception as e:
            os.remove(pdf_path)
            raise ValueError(f"Error processing file: {str(e)}") from e

def handle_form(submit, index_name, index):
    st.markdown("## Correção de questões")
    st.markdown("Insira a questão e a resposta correta.")

    form = st.form("form", clear_on_submit=True)
    with form:
        question = st.text_area("Questão")
        answer = st.text_area("Resposta")
        submit = st.form_submit_button("Enviar")
        if len(question) == 0:
            return "Pergunta não pode ser vazia", False, False
        
    if submit == True:
            
        formatted_template = f"Pergunta: {question} resposta: {answer}"

        vec_store = PineconeVectorStore.from_texts(
            texts=[formatted_template],
            embedding=embeddings,
            index_name=index_name,
        )

        placeholder = st.empty()
        with placeholder.container():
            st.warning("Aguarde enquanto o repositório de perguntas está sendo atualizado...")
            
        while index.describe_index_stats().to_dict()['total_vector_count'] == 0:
            time.sleep(1)
        placeholder.empty()

        st.success("A questão foi corrigida e salva no banco de dados.")

def upload_doc(embeddings, index, index_name):
    with st.form("upload_form", clear_on_submit=True):

        document_binary = st.file_uploader(
            label="Carregue um documento PDF",
            type=["pdf"],
            accept_multiple_files=False,
        )

        file_submitted = st.form_submit_button("Clique aqui para enviar o PDF")

        # Traduzindo o botão de upload
        st.html(
            """
            <style>
            [data-testid='stForm'] [data-testid='stBaseButton-secondary'] {
            text-indent: -9999px;
            line-height: 0;
            }

            [data-testid='stForm'] [data-testid='stBaseButton-secondary']::after {
            line-height: initial;
            content: "Clique aqui para carregar um documento PDF";
            text-indent: 0;
            }
            </style>
            """
        )

        if file_submitted and (document_binary is not None):
        
            document = process_document(document_binary)
            
            for doc in document:
                for item in doc:
                    vec_store = PineconeVectorStore.from_texts(
                        texts=[item],
                        embedding=embeddings,
                        index_name=index_name,
                    )

            placeholder = st.empty()
            with placeholder.container():
                st.success("Documento processado com sucesso!")
                st.warning("Aguarde enquanto o repositório de perguntas está sendo carregado...")

            while index.describe_index_stats().to_dict()['total_vector_count'] == 0:
                time.sleep(1)
            placeholder.empty()
            
            placeholder = st.empty()
            with placeholder.container():
                st.success("Repositório de perguntas carregado com sucesso!")
                time.sleep(5)
            placeholder.empty()

            return True
                
        else:
            print("No document uploaded")
            return False

def reset_index(index, index_name):
    placeholder = st.empty()
    if index.describe_index_stats().to_dict()['total_vector_count']>0:
        delete_response = index.delete(delete_all=True)
        
        with placeholder:   
            st.warning("Repositório de perguntas reiniciando...")
            while index.describe_index_stats().to_dict()['total_vector_count'] != 0:
                time.sleep(1)
            st.success("Repositório de perguntas reiniciado com sucesso!")
            time.sleep(5)
        placeholder.empty()
        index = pc.Index(index_name)
    else:
        with placeholder:
            st.warning("Repositório de perguntas já está vazio.")
            time.sleep(5)
        placeholder.empty()
    
def main():
    if not check_password():
        st.stop()
    else:
        index, index_name = init_index()

        with st.sidebar:
            st.button(("Reiniciar repositório de perguntas"), on_click=reset_index, args=(index, index_name))

        submit = False
        handle_form(submit, index_name, index)

        upload_doc(embeddings, index, index_name)

        # Mostrando conteúdo do repositório
        index_list = []
        for ids in index.list():
            for id in ids:
                index_list.append(id)

        container = st.container(border=True)
        container.write("Documentos salvos:")
        with container:
            if len(index_list) != 0 or index.describe_index_stats().to_dict()['total_vector_count'] != 0:
                for id in index_list:
                    reg = index.query(id=id, top_k=1, include_metadata=True)['matches']
                    if reg is not None or len(reg) != 0:
                        reg = reg[0]['metadata']['text']
                        st.markdown(f"""
                            #### código do gabarito: 
                            {id}   
                        """)
                        st.markdown(f"""
                            #### gabarito: 
                            {reg}
                        """)

                        st.divider()


main()
