import streamlit as st
import hmac

if "role" not in st.session_state:
    st.session_state.role = None
    # st.session_state.index_name = "tcc-vectorstore-cohere"
    st.session_state.index_name = "tcc-vectorstore-huggingface"
    
st.session_state.TEACHER_PASSWD = ""

ROLES = [None, "aluno", "professor"]

def login():
    role = st.selectbox("Escolha sua função", ROLES)

    if st.button("Acessar"):
        st.session_state.role = role
        st.rerun()

def logout():
    st.session_state.role = None
    for key in st.session_state.keys():
        st.session_state.pop(key)
    st.rerun()

def main():
    role = st.session_state.role

    logout_page = st.Page(logout, title="Deslogar", icon=":material/logout:")
    #settings = st.Page("settings.py", title="Settings")

    student_1 = st.Page(
        "pages/student/streamlit_chat.py",
        title="Area do aluno",
        icon=":material/help:",
        default=(role == "aluno"),
    )

    teacher_1 = st.Page(
        "pages/teacher/streamlit_teacher.py",
        title="Area do professor",
        icon=":material/healing:",
        default=(role == "professor"),
    )

    account_pages = [logout_page]
    student_pages = [student_1]
    teacher_pages = [teacher_1]

    st.title("SaberIA", anchor=False)

    title_alignment= """
        <style>
        #saberia {
            text-align: center;
            font-size: 50px;
        }
        </style>
    """
    st.markdown(title_alignment, unsafe_allow_html=True)

    page_dict = {}
    if st.session_state.role in ["professor"]:
        page_dict["Professor"] = teacher_pages
    if st.session_state.role in ["aluno"]:
        page_dict["Aluno"] = student_pages
        
    if len(page_dict) > 0:
        pg = st.navigation( pages={"":account_pages} | page_dict, )
    else:
        pg = st.navigation([st.Page(login)])
        
    pg.run()

main()