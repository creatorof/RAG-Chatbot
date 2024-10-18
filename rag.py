import argparse
import chromadb
from dotenv import load_dotenv
import os


from llama_index.core import get_response_synthesizer
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
from llama_index.core import StorageContext
from llama_index.core import SummaryIndex
from llama_index.core import Settings
from llama_index.core.agent import ReActAgent
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.postprocessor import SimilarityPostprocessor
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.tools import FunctionTool, QueryEngineTool
from llama_index.embeddings.gemini import GeminiEmbedding
from llama_index.llms.gemini import Gemini
from llama_index.vector_stores.chroma import ChromaVectorStore
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from ddg_search import ddg_search



def initialize_vector_store(collection_name, path):
    db = chromadb.PersistentClient(path=path)
    chroma_collection = db.get_or_create_collection(collection_name)
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    return vector_store, storage_context


def create_index_from_documents(vector_store, storage_context, documents, chunk_size=500, chunk_overlap=100):
    Settings.embed_model = GeminiEmbedding()
    Settings.llm = Gemini()
    text_splitter = SentenceSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    index = VectorStoreIndex.from_documents(
        documents, storage_context=storage_context, text_splitter=text_splitter
    )
    return index


def load_index_from_vector_store(vector_store, storage_context, chunk_size=500, chunk_overlap=100):
    text_splitter = SentenceSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    index = VectorStoreIndex.from_vector_store(
        vector_store, storage_context=storage_context, text_splitter=text_splitter
    )
    return index


def load_data(directory, required_exts=[".html"]):
    reader = SimpleDirectoryReader(input_dir=directory, required_exts=required_exts)
    return reader.load_data()


def configure_retriever(index, top_k=3):
    retriever = VectorIndexRetriever(index=index, similarity_top_k=top_k)
    return retriever

def build_query_engine(chroma_db_dir):
    Settings.embed_model = GeminiEmbedding()
    Settings.llm = Gemini()
    vector_store, storage_context = initialize_vector_store("saved_pages", chroma_db_dir)
    index = load_index_from_vector_store(vector_store, storage_context)

    retriever = configure_retriever(index)
    response_synthesizer = get_response_synthesizer()

    query_engine = RetrieverQueryEngine.from_args(
        retriever=retriever,
        response_synthesizer=response_synthesizer,
        node_postprocessors=[SimilarityPostprocessor(similarity_cutoff=0.5)],
    )
    return query_engine


def chatbot_agent(chroma_db_dir):
    def search_tool(query):
        docs = ddg_search(query)
        index = SummaryIndex.from_documents(docs)
        query_engine = index.as_query_engine()
        response = query_engine.query(query)
        return response

    def email_tool(subject, body, recipient):
        sender = os.getenv('EMAIL_SENDER')
        message = Mail(
            from_email=sender,
            to_emails=recipient,
            subject=subject,
            html_content=body)
        try:
            sg = SendGridAPIClient(os.getenv('EMAIL_API_KEY'))
            response = sg.send(message)
            print(response.status_code)
            if response.status_code == 202:
                return f"Successfully sent email to {recipient}"
        except Exception as e:
            print(e)
            return "Email sending failed"
        
    search_tool = FunctionTool.from_defaults(fn=search_tool)
    email_tool = FunctionTool.from_defaults(fn=email_tool)
    query_engine = build_query_engine(chroma_db_dir)
    llama_tool = QueryEngineTool.from_defaults(
        query_engine,
        name="llama_index",
        description="A RAG engine with some basics about llama Index library",
    )
    
    agent = ReActAgent.from_tools([search_tool, email_tool, llama_tool],llm=Gemini(), verbose=True)
    return agent



