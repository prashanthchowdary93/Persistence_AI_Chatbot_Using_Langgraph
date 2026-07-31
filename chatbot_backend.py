from langgraph.graph import StateGraph,START,END
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage,BaseMessage
from typing import TypedDict,Literal,Annotated
from langgraph.checkpoint.memory import InMemorySaver 
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

#Creating persisitence in memory object
checkpointer = InMemorySaver()

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

