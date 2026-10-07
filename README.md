# 🤖 Persistent AI Chatbot

A stateful AI chatbot built using **LangGraph,Langchain, OpenAI, Streamlit, and SQLite** that demonstrates persistent conversational memory, thread-based session management, graph-based orchestration, and real-time response streaming.

Unlike a basic chatbot where conversation history exists only during the current application session, this project uses **LangGraph checkpointing with SQLite** to persist graph state and restore previous conversations using a unique `thread_id` concept.

---

## 🎥 "Persistent AI Chatbot" Demo

Watch the Persistent AI Chatbot demo:
https://youtu.be/aTQn4O8oEmc

## 🎯 Project Objective

The objective of this project is to understand and demonstrate how **stateful GenAI applications** can be built using LangGraph.

The application focuses on an important real-world requirement:

> **How can an AI chatbot remember previous conversations and allow users to create, persist, and switch between multiple conversations?**

The project implements this using:

* LangGraph `StateGraph`
* LangGraph checkpointing
* SQLite persistence
* Unique conversation `thread_id`
* Streamlit UI
* OpenAI chat model
* Real-time response streaming

LangGraph persistence uses checkpoints to save graph state, with a `thread_id` identifying the conversation whose state should be restored.

---

# 🏗️ Architecture

```text
                    ┌─────────────────────────┐
                    │      Streamlit UI       │
                    │                         │
                    │  • Chat Interface       │
                    │  • New Chat             │
                    │  • Conversation Sidebar │
                    │  • Streaming Response   │
                    └────────────┬────────────┘
                                 │
                                 │ User Message
                                 ▼
                    ┌─────────────────────────┐
                    │      LangGraph          │
                    │      Workflow            │
                    │                         │
                    │   START                  │
                    │     │                    │
                    │     ▼                    │
                    │  Chat Node              │
                    │     │                    │
                    │     ▼                    │
                    │     │                    │
                    │    END                   │
                    └────────────┬────────────┘
                                 │
                                 │ Checkpoint
                                 ▼
                    ┌─────────────────────────┐
                    │        SQLite           │
                    │                         │
                    │  Persistent Graph State │
                    │                         │
                    │  thread_id              │
                    │  messages               │
                    │  checkpoints            │
                    └─────────────────────────┘
```

---

# ✨ Key Features

### 1. 💬 Multi-Turn Conversation

The chatbot maintains the context of previous messages within the same conversation.

For example:

```text
User: My name is Prashanth.

AI: Nice to meet you, Prashanth!

User: What is my name?

AI: Your name is Prashanth.
```

The second request is able to use the state persisted from the first interaction.

---

### 2. 💾 Persistent Conversation State

The application uses LangGraph's `SqliteSaver` as the checkpointer.

```python
conn = sqlite3.connect(
    database="ChatHistory",
    check_same_thread=False
)

checkpointer = SqliteSaver(conn)

chat_workflow = graph.compile(
    checkpointer=checkpointer
)
```

The graph state is persisted in SQLite rather than existing only in application memory.

This means previous conversations can be retrieved even after the Streamlit application is restarted.

For local development, SQLite is a useful persistent checkpointer because it does not require a separate database service.

---

# 🧵 Thread-Based Conversation Management

Every conversation is identified using a unique `thread_id`.

Example:

```text
Conversation 1
thread_id = 019abc-123
```

```text
Conversation 2
thread_id = 019abc-456
```

When a message is sent, the thread ID is passed to LangGraph:

```python
CONFIG = {
    "configurable": {
        "thread_id": st.session_state["thread_id"]
    }
}
```

LangGraph uses this identifier to associate the current execution with the appropriate persisted state.

### Why `thread_id` is important

Without a thread identifier, different conversations could not be cleanly separated.

With thread-based persistence:

```text
             LangGraph
                 │
       ┌─────────┴─────────┐
       │                   │
 thread_001            thread_002
       │                   │
       ▼                   ▼
Conversation A        Conversation B
```

Each thread maintains its own conversation state.

---

# 🔄 New Chat Flow

When the user clicks **New Chat**, the application generates a new UUID-based thread ID.

```python
def generate_thread_id():
    return str(uuid7())
```

The application then:

1. Generates a new `thread_id`
2. Sets it as the active conversation
3. Clears the current UI chat history
4. Creates a new conversation entry
5. Starts a fresh LangGraph conversation

The previous conversation is **not deleted**.

It remains persisted in SQLite and can be loaded again from the conversation sidebar.

---

# 🕘 Previous Conversation Retrieval

At application startup, the application reads the saved checkpoints from SQLite.

Conceptually:

```text
SQLite
   │
   ├── thread_001 → Conversation 1
   ├── thread_002 → Conversation 2
   └── thread_003 → Conversation 3
```

The application retrieves:

* `thread_id`
* persisted messages
* first user message

The first user message is used as the conversation title in the Streamlit sidebar.

Example:

```text
My Conversations

┌─────────────────────────────┐
│ Explain LangGraph           │
│ What is RAG?                │
│ How does persistence work?  │
└─────────────────────────────┘
```

When the user selects a conversation, the corresponding `thread_id` is used to retrieve the persisted state.

---

# ⚡ Real-Time Streaming

The application supports streaming responses instead of waiting for the complete LLM response.

The frontend uses:

```python
st.write_stream(ai_only_stream())
```

The streaming function receives LangGraph message chunks:

```python
for message_chunk, metadata in chat_workflow.stream(
    {"messages": [HumanMessage(content=user_input)]},
    config=CONFIG,
    stream_mode="messages",
):
    ...
```

The application filters AI-generated chunks and yields their content:

```python
if isinstance(message_chunk, AIMessage):
    yield message_chunk.content
```

Conceptually:

```text
LLM generates:

"LangGraph"
      ↓
" is"
      ↓
" a"
      ↓
" framework"
      ↓
...

Streamlit displays:

LangGraph is a framework...
```

This provides a more responsive ChatGPT-style user experience.

---

# 🧠 LangGraph Workflow

The core workflow is represented as a graph.

```text
        START
          │
          ▼
     ┌──────────┐
     │ Chat Node│
     └────┬─────┘
          │
          ▼
         END
```

The graph state contains the conversation messages:

```python
class ChatState(TypedDict):
    messages: Annotated[
        list[BaseMessage],
        add_messages
    ]
```

The `add_messages` reducer allows new messages to be added to the existing state rather than replacing the entire message history.

---

# 🔑 Core LangGraph Concepts Demonstrated

This project demonstrates several important LangGraph concepts:

| Concept                   | Implementation        |
| ------------------------- | --------------------- |
| Graph-based orchestration | `StateGraph`          |
| State management          | `ChatState`           |
| Message state             | `messages`            |
| State reducer             | `add_messages`        |
| Persistence               | `SqliteSaver`         |
| Conversation isolation    | `thread_id`           |
| State retrieval           | `get_state()`         |
| Checkpoint retrieval      | `checkpointer.list()` |
| Streaming                 | `stream()`            |
| UI streaming              | `st.write_stream()`   |
| Frontend state            | `st.session_state`    |

---

# 🛠️ Technology Stack

### AI / GenAI

* **OpenAI**
* **LangChain**
* **LangGraph**

### Backend / Workflow

* **Python**
* **LangGraph StateGraph**
* **SQLite**
* **LangGraph SqliteSaver**

### Frontend

* **Streamlit**

### State & Persistence

* SQLite
* LangGraph Checkpointing
* Thread-based conversation management

---

# 📁 Project Structure

```text
Persistence_Chatbot_Using_Langgraph/
│
├── chatbot_backend.py
│
├── streamlit_frontend.py
│
├── ChatHistory
│
├── requirements.txt
│
├── .env
│
└── README.md
```

> File names may vary depending on the current version of the project.

---

# ⚙️ Installation

## 1. Clone the Repository

```bash
git clone https://github.com/prashanthchowdary93/Persistence_Chatbot_Using_Langgraph.git
```

```bash
cd Persistence_Chatbot_Using_Langgraph
```

---

## 2. Create a Virtual Environment

```bash
python -m venv .venv
```

Activate it on Windows:

```bash
.venv\Scripts\activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Configure Environment Variables

Create a `.env` file:

```env
OPENAI_API_KEY=your_openai_api_key
```

Do **not** commit the `.env` file to GitHub.

Add it to `.gitignore`:

```text
.env
.venv/
__pycache__/
*.pyc
```

---

# ▶️ Running the Application

Start the Streamlit application:

```bash
streamlit run streamlit_frontend.py
```

The application will open in the browser.

---

# 🧪 Example Usage

### Conversation 1

```text
User:
My name is Alex and I am learning LangGraph.

AI:
Nice to meet you Alex! LangGraph is useful for...

User:
What am I learning?

AI:
You are learning LangGraph.
```

Now click:

```text
New Chat
```

A new `thread_id` is generated.

The new conversation starts independently.

---

### Returning to the Previous Conversation

Select the previous conversation from the sidebar.

The application:

```text
Sidebar conversation
        ↓
thread_id
        ↓
LangGraph get_state()
        ↓
SQLite checkpoint
        ↓
Previous messages
        ↓
Display conversation
```

This demonstrates how persisted graph state can be restored based on a conversation thread.

---

# 💡 Why LangGraph Instead of a Simple LLM Call?

A simple implementation could look like:

```python
response = llm.invoke(user_input)
```

However, real-world GenAI applications often require more than a single LLM call.

For example:

```text
User Request
     │
     ▼
   Agent
     │
     ├── Tool
     │
     ├── Retrieval
     │
     ├── Human Approval
     │
     └── Another Agent
```

LangGraph provides a structured way to represent these workflows as graphs with explicit state and execution paths.

This project focuses on one of the fundamental building blocks of agentic applications:


---

## Author ##
```
Prashanth Chowdary Rimmalapudi
```
