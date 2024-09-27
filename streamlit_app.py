import streamlit as st

if "role" not in st.session_state:
    st.session_state.role = None
    st.session_state.index_name = "kb-teacher2"


ROLES = [None, "aluno", "professor"]

def login():
    role = st.selectbox("Escolha seu papel", ROLES)

    if st.button("Log in"):
        st.session_state.role = role
        st.rerun()

def logout():
    st.session_state.role = None
    st.rerun()

role = st.session_state.role

logout_page = st.Page(logout, title="Log out", icon=":material/logout:")
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

st.title("FAQ Automatizado")

page_dict = {}
if st.session_state.role in ["professor"]:
    page_dict["teacher"] = teacher_pages
if st.session_state.role in ["aluno"]:
    page_dict["student"] = student_pages

if len(page_dict) > 0:
    pg = st.navigation({"Account": account_pages} | page_dict)
else:
    pg = st.navigation([st.Page(login)])


pg.run()