from langgraph.graph import StateGraph,START,END
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage,BaseMessage
from typing import TypedDict,Literal,Annotated
from langgraph.checkpoint.sqlite import SqliteSaver ,sqlite3
from langgraph.graph.message import add_messages

#Load the dotenv
load_dotenv()

#LLM object creation
llm_obj = ChatOpenAI()

#Create the state for workflow
class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage],add_messages]

#Creating graph for worklfow
graph = StateGraph(ChatState)

#connection object for sqlite db
conn = sqlite3.connect(database='ChatHistory',check_same_thread=False)

#Creating persisitence in sqlite and passing connection object
checkpointer = SqliteSaver(conn)

#defining the python function 
def chat_node(state: ChatState):
    user_input = state['messages']
    response = llm_obj.invoke(user_input)

    return {'messages':[response]}

#add nodes
graph.add_node('chat_node',chat_node)

#add edges in the graph
graph.add_edge(START,'chat_node')
graph.add_edge('chat_node',END)

chat_workflow = graph.compile(checkpointer=checkpointer)

#print(chat_workflow)
""" CONFIG = {'configurable':{'thread_id':'thread_id_1'}}

resp = chat_workflow.invoke(
                {'messages':HumanMessage(content='What is the capital name you mentioend now?')},
                config=CONFIG
            )
print(f"resp is : {resp}") """

def retrive_unique_thread_ids():
    thread_history = {}

    for checkpoint in checkpointer.list(None):
        channel_values = checkpoint.checkpoint['channel_values']
        if "messages" in channel_values:
            messages = channel_values["messages"]

            first_user_input = next(
                (m.content for m in messages if isinstance(m, HumanMessage)),
                "New Chat"
            )            
        thread_id = checkpoint.config["configurable"]["thread_id"]
        thread_history[thread_id] = first_user_input

    return thread_history
#print(retrive_unique_thread_ids())