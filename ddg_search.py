from duckduckgo_search import DDGS
from llama_index.readers.web import SimpleWebPageReader


def ddg_search(query):
    results = DDGS().text(query, max_results=3)
    urls = []
    for result in results:
        url = result['href']
        urls.append(url)

    docs = get_page(urls)
    return docs

def get_page(urls):
    reader = SimpleWebPageReader()
    documents = reader.load_data(urls)
    return documents