from dotenv import load_dotenv
import os

from rag import initialize_vector_store, create_index_from_documents, load_data

def main():
    load_dotenv(dotenv_path='dev.env')   
    data_dir = os.getenv('DATA_DIR', './saved_html_pages')
    chroma_db_dir = os.getenv('CHROMA_DB', './chroma_db')
    
    docs = load_data(data_dir)
    print("Initializing DB ....")
    vector_store, storage_context = initialize_vector_store("saved_pages", chroma_db_dir)
    print("DB Initilization Ended....")
    print("Creating Document Indexes...")
    index = create_index_from_documents(vector_store, storage_context, docs)
    print("Document Indexes Creation Ended...")

if __name__ == "__main__":
    main()
