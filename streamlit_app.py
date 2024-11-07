import streamlit as st
import hmac

if "role" not in st.session_state:
    st.session_state.role = None
    st.session_state.index_name = "kb-teacher2"
    
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

def check_password() -> bool:
    """
    Checks if the user entered the correct password.

    Returns:
        bool: True if the password is correct, False otherwise.
    """
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
        if not check_password():
            st.stop()
        else:
            page_dict["teacher"] = teacher_pages
    if st.session_state.role in ["aluno"]:
        page_dict["student"] = student_pages

    if len(page_dict) > 0:
        pg = st.navigation({"Account": account_pages} | page_dict)
    else:
        pg = st.navigation([st.Page(login)])
        
    pg.run()

main()