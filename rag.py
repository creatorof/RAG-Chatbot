import argparse
import chromadb
from dotenv import load_dotenv
import os

from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core import StorageContext
from llama_index.core import SummaryIndex
from llama_index.core.postprocessor import SimilarityPostprocessor
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.vector_stores.chroma import ChromaVectorStore

from ddg_search import ddg_search



def initialize_vector_store(collection_name, path):
    db = chromadb.PersistentClient(path=path)
    chroma_collection = db.get_or_create_collection(collection_name)
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    return vector_store, storage_context


def create_index_from_documents(vector_store, storage_context, documents, chunk_size=500, chunk_overlap=100):
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


def query_with_fallback(query, retriever, response_synthesizer):
    query_engine = RetrieverQueryEngine.from_args(
        retriever=retriever,
        response_synthesizer=response_synthesizer,
        node_postprocessors=[SimilarityPostprocessor(similarity_cutoff=0.5)],
    )
    response = query_engine.query(query)
    response_text = response.response.lower()

    if "context does not provide" in response_text or "empty response" in response_text:
        print("No relevant context found, searching the internet...")
        docs = ddg_search(query)
        index = SummaryIndex.from_documents(docs)
        query_engine = index.as_query_engine()
        response = query_engine.query(query)
    
    return response


