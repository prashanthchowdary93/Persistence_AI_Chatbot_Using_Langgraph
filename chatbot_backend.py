from langgraph.graph import StateGraph,START,END
from langchain_openai import ChatOpenAI,OpenAIEmbeddings
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage,BaseMessage
from typing import TypedDict,Literal,Annotated
from langgraph.checkpoint.sqlite import SqliteSaver ,sqlite3
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode,tools_condition
from langchain_core.tools import tool
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_community.vectorstores import Chroma

#Load the dotenv
load_dotenv()

#EMbeddings loading
embeddings = OpenAIEmbeddings()

vector_db = Chroma(
    persist_directory="./employee_db",
    embedding_function=embeddings
)

#LLM object creation
llm_obj = ChatOpenAI()

#Tools creation

#Tool 1 Searchtool
search_tool = DuckDuckGoSearchResults()

#Tool 2 calculator
@tool
def calculator_tool(first_num: float , second_num: float , operation:str) -> dict:
    """
    This tools provides the result of two number based on the provided operation
    Allowed operations are add, subtract, product, division
    """
    if operation  == "add":
        result = first_num + second_num
    if operation  == "subtract":
            result = first_num - second_num
    if operation  == "product":
            result = first_num * second_num 
    if operation  == "division":
            result = first_num / second_num 

    return {'first_num':first_num,'second_num':second_num,'operator':operation,'result':result}

@tool
def rag_retrieval(query: str) -> str:
    """
    Search the uploaded document for information.

    Use this tool whenever the user asks questions about
    uploaded documents from the chatbot.
    """

    docs = vector_db.similarity_search(
        query,
        k=4
    )

    if not docs:
        return "No relevant documents found."

    context = "\n\n".join(
        doc.page_content
        for doc in docs
    )

    return context

#tools list
tool_list = [search_tool,calculator_tool,rag_retrieval]

#binding tools
llm_obj_with_tools = llm_obj.bind_tools(tool_list)

#creating tool node which acts as HOST of all tools in langgraph
#toolnode = tool_node(['search_tool','calculator_tool'])
toolnode = ToolNode([search_tool, calculator_tool,rag_retrieval])

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
    response = llm_obj_with_tools.invoke(user_input)

    return {'messages':[response]}

#add nodes
graph.add_node('chat_node',chat_node)
graph.add_node('tools',toolnode)

#add edges in the graph
graph.add_edge(START,'chat_node')
graph.add_conditional_edges('chat_node',tools_condition)
graph.add_edge('tools','chat_node')

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