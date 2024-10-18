import streamlit as st
from dotenv import load_dotenv
import os


from rag import initialize_vector_store, load_index_from_vector_store, configure_retriever, chatbot_agent, create_index_from_documents, load_data

def initialize_app():
    load_dotenv(dotenv_path='dev.env')
    st.sidebar.write("Environment variables loaded.")
    data_dir = os.getenv('DATA_DIR', './saved_html_pages')
    chroma_db_dir = os.getenv('CHROMA_DB', './chroma_db')
    if not chroma_db_dir:
        st.sidebar.warning("Chroma DB Directory not detected.")

    st.sidebar.write("DB Directory detected.")
    vector_store, storage_context = initialize_vector_store("saved_pages", chroma_db_dir)
    st.sidebar.write("Store Initialized")
    docs = load_data(data_dir)
    st.sidebar.write("Data Loaded")
    index = create_index_from_documents(vector_store, storage_context, docs)
    st.sidebar.write("Index created from document")
    return chroma_db_dir


def chatbot_app():
    st.title("Chatbot")

    if "setup_done" not in st.session_state:
        st.sidebar.write("Running initial setup...")
        chroma_db_dir = initialize_app()
        st.session_state.setup_done = True
        st.session_state.chroma_db_dir = chroma_db_dir
        st.session_state.chat_agent = chatbot_agent(chroma_db_dir)
        st.session_state.chat_history = []  
    st.write("### Chat")
    user_query = st.text_input("You:", key="user_input", placeholder="Enter your message...")

    if st.button("Send", key="send_button"):
        if user_query:
            st.session_state.chat_history.append({"role": "user", "message": user_query})

            with st.spinner("Generating response..."):
                try:
                    response = st.session_state.chat_agent.chat(user_query)

                    st.session_state.chat_history.append({"role": "bot", "message": response})
                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            st.warning("Please enter a query.")

    for chat in st.session_state.chat_history:
        if chat["role"] == "user":
            st.write(f"**You:** {chat['message']}")
        else:
            st.write(f"**Bot:** {chat['message']}")

    st.write(" " * 10)  


if __name__ == "__main__":
    chatbot_app()