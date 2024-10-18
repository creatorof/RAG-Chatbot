import argparse
from dotenv import load_dotenv
import os

from llama_index.core import get_response_synthesizer
from llama_index.core import Settings
from llama_index.embeddings.gemini import GeminiEmbedding
from llama_index.llms.gemini import Gemini

from rag import initialize_vector_store, load_index_from_vector_store, configure_retriever, query_with_fallback

def main():
    load_dotenv(dotenv_path='dev.env')
    google_api_key = os.getenv('GOOGLE_API_KEY')
    if google_api_key:
        os.environ["GOOGLE_API_KEY"] = google_api_key
    else:
        raise EnvironmentError("GOOGLE_API_KEY not found in dev.env file")

    Settings.embed_model = GeminiEmbedding()
    Settings.llm = Gemini()

    data_dir = os.getenv('DATA_DIR', './saved_html_pages')
    chroma_db_dir = os.getenv('CHROMA_DB', './chroma_db')

    parser = argparse.ArgumentParser(description="Query a document or fallback to web search.")
    parser.add_argument("query", type=str, help="The query to execute.")
    args = parser.parse_args()

    vector_store, storage_context = initialize_vector_store("saved_pages", chroma_db_dir)
    index = load_index_from_vector_store(vector_store, storage_context)

    retriever = configure_retriever(index)

    response_synthesizer = get_response_synthesizer()
    response = query_with_fallback(args.query, retriever, response_synthesizer)

    print(response)


if __name__ == "__main__":
    main()