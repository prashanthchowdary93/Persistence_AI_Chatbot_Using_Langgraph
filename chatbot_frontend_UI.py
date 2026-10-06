import streamlit as st
from chatbot_backend import chat_workflow,retrive_unique_thread_ids
from langchain_core.messages import HumanMessage,AIMessage,ToolMessage
from langchain_core.utils.uuid import uuid7
from create_vector_db import create_doc_embeddings

##########################Utility functions#######################################
def generate_thread_id():
    thread_id = str(uuid7())
    return thread_id

def reset_session():
    thread_id = generate_thread_id()
    st.session_state['thread_id'] = thread_id
    st.session_state['chat_history'] = []
    add_thread_history(st.session_state['thread_id'],'New Chat')
    st.session_state['chat_history'] = []

def add_thread_history(thread_id,title):
    if thread_id not in st.session_state['thread_history']:
     #st.session_state['thread_history'].append(thread_id) 
     st.session_state["thread_history"][thread_id] = title

def load_conversations(thread_id):
    #CONFIG = {'configurable':{'thread_id':thread_id}}     
    #return chat_workflow.get_state(config=CONFIG).values['messages']
    state = chat_workflow.get_state(config={'configurable': {'thread_id': thread_id}})
    # Check if messages key exists in state values, return empty list if not
    return state.values.get('messages', [])
#########################Utility functions######################################## 

#############Setting up the Session###############################################
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []

if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()

if 'thread_history' not in st.session_state:
    st.session_state['thread_history'] = retrive_unique_thread_ids()      

add_thread_history(st.session_state['thread_id'],'New Chat')

#############Setting up the Session###############################################  
# 
#
# ============================ Sidebar ============================
st.sidebar.title("LangGraph PDF Chatbot")


uploaded_pdf = st.sidebar.file_uploader("Upload a PDF for this chat", type=["pdf"])

if uploaded_pdf is not None:
    #print(f"Uploaded doc name is : {uploaded_pdf.name} and size is : {uploaded_pdf.size}")
    create_doc_embeddings(uploaded_pdf.getvalue())
# ============================ Main Layout ========================
st.title("Multi Utility Chatbot")   

##################Adding side bars################################################

st.sidebar.title('Langgraph Chatbot')

if st.sidebar.button('New Chat'):
    reset_session()

st.sidebar.header('My Conversations')   

#for thread_id in st.session_state['thread_history']:
for thread_id, title in st.session_state["thread_history"].items():
    if st.sidebar.button(title, key=thread_id):
        st.session_state['thread_id'] = thread_id
        conv_messages = load_conversations(thread_id)        
        temp_msg = []
        for msg in conv_messages:
            if isinstance(msg,HumanMessage):
                role = 'user'
            elif isinstance(msg, AIMessage):
                role = "assistant"
            else:
                continue    
            temp_msg.append({'role':role,'content':msg.content})       
        st.session_state['chat_history'] = temp_msg
##################Adding side bars################################################


#############Displaying previous messages#########################################
for message in st.session_state['chat_history']:
    with st.chat_message(message['role']):
        st.text(message['content'])
#############Displaying previous messages#########################################


####################User Input and Invoke function################################
user_input = st.chat_input('Type here..')
#thread_id = 1
if user_input:
    if st.session_state["thread_history"][st.session_state["thread_id"]] == "New Chat":
      title = user_input[:40]  # first 40 characters
      st.session_state["thread_history"][st.session_state["thread_id"]] = title
    st.session_state['chat_history'].append({'role':'user','content':user_input})
    with st.chat_message('user'):
        st.text(user_input)
    #CONFIG = {'configurable':{'thread_id':st.session_state['thread_id']}}
    CONFIG = {'configurable':{'thread_id':st.session_state['thread_id']},
              'metadata':
              {
                  'thread_id':st.session_state['thread_id']
              },
              'run_name':'chat_turn'}
    #resp = chat_workflow.invoke({'messages':HumanMessage(content=user_input)},config=CONFIG)

    
    with st.chat_message('assistant'):
        def ai_only_stream():
            try:
                for message_chunk, metadata in chat_workflow.stream(
                    {"messages": [HumanMessage(content=user_input)]},
                    config=CONFIG,
                    stream_mode="messages",
                ):
                    print(type(message_chunk), message_chunk)

                    if isinstance(message_chunk, AIMessage):
                        yield message_chunk.content

            except Exception as e:
                print("STREAM ERROR:", e)
                raise e

        ai_message = st.write_stream(ai_only_stream())
    st.session_state['chat_history'].append({'role':'assistant','content':ai_message})
####################User Input and Invoke function###################################    