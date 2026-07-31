import streamlit as st
from chatbot_backend import chat_workflow
from langchain_core.messages import HumanMessage

if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []

for message in st.session_state['chat_history']:
    with st.chat_message(message['role']):
        st.text(message['content'])


user_input = st.chat_input('Type here..')
thread_id = 1
if user_input:
    st.session_state['chat_history'].append({'role':'user','content':user_input})
    with st.chat_message('user'):
        st.text(user_input)
    CONFIG = {'configurable':{'thread_id':thread_id}}
    resp = chat_workflow.invoke({'messages':HumanMessage(content=user_input)},config=CONFIG)

    st.session_state['chat_history'].append({'role':'assistant','content':resp['messages'][-1].content})
    with st.chat_message('assistant'):
        st.text(resp['messages'][-1].content)