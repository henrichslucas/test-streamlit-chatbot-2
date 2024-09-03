import streamlit as st

#form for the teacher to insert the corrected question and answer
st.markdown("## Correção de questões")
st.markdown("Insira a questão e a resposta correta.")
with st.form("form"):
    question = st.text_area("Questão")
    answer = st.text_area("Resposta")
    submit = st.form_submit_button("Enviar")

