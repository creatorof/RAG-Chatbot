import bs4
from urllib.request import urlopen as request
from bs4 import BeautifulSoup as soup
from bs4 import SoupStrainer as strainer
import os
import argparse


default_class_name = 'md-content'
default_urls = ['https://docs.llamaindex.ai/en/v0.10.22/understanding/using_llms/using_llms/',
        'https://docs.llamaindex.ai/en/v0.10.22/understanding/loading/loading/',
        'https://docs.llamaindex.ai/en/v0.10.22/understanding/loading/llamahub/',
        'https://docs.llamaindex.ai/en/v0.10.22/understanding/indexing/indexing/',
        'https://docs.llamaindex.ai/en/v0.10.22/understanding/storing/storing/',
        'https://docs.llamaindex.ai/en/v0.10.22/understanding/querying/querying/',
        'https://docs.llamaindex.ai/en/v0.10.22/understanding/tracing_and_debugging/tracing_and_debugging/',]
save_dir = "saved_html_pages"


def count_existing_docs(save_dir):
    if not os.path.exists(save_dir):
        return 0  

    return len([file for file in os.listdir(save_dir) if file.endswith(".html")])

def save_to_local(page_soup, file_name, save_dir):
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    file_path = os.path.join(save_dir, file_name)
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(str(page_soup))


def scrap_data(urls, save_dir, class_name, element):
    item_cells = strainer(element, attrs={"class": class_name})
    last_index = count_existing_docs(save_dir)
    for idx, url in enumerate(urls):
        client = request(url)
        page_html = client.read()
        page_soup = soup(page_html, 'html.parser', parse_only=item_cells)

        file_name = f"page_{last_index + idx+1}.html"
        save_to_local(page_soup, file_name, save_dir)

        client.close()


def main():
    parser = argparse.ArgumentParser(description="Scrape and save HTML content from URLs.")
    
    parser.add_argument('-u', '--url', type=str, nargs='*',
                        help='URLs to scrape. If not provided, default URLs will be used.')
    
    parser.add_argument('-c', '--class_name', type=str, nargs='*',
                        help='class name of the web page to scrape. If not provided, default class name will be used.')
    
    parser.add_argument('-e', '--element', type=str, nargs='*',
                        help='element of the web page to scrape. If not provided, div will be used.')

    args = parser.parse_args()

    urls = args.url if args.url else default_urls

    class_name = args.class_name if args.class_name else default_class_name

    element = args.element if args.element else "div"

    scrap_data(urls, save_dir, class_name, element)

if __name__ == "__main__":
    main()