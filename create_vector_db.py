from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from dotenv import load_dotenv
import tempfile

load_dotenv()

def create_doc_embeddings(loader:bytes):

    #loader = PyPDFLoader("paper2_SL.pdf")
    #documents = loader.load()
    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".pdf"
    ) as temp_file:

        temp_file.write(loader)
        temp_file_path = temp_file.name
    
    loader = PyPDFLoader(temp_file_path)

    documents = loader.load()

    print("Number of documents:", len(documents))

    if documents:
        print("First document content length:", len(documents[0].page_content))
        print("First document content:", documents[0].page_content[:500])

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )

    chunks = splitter.split_documents(documents)

    embeddings = OpenAIEmbeddings()

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory="./employee_db"
    )

    print("Vector DB created.")