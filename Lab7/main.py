# import bs4
# import requests
# import json
# import pika
#
# def fetch_stored_urls():
#     try:
#         with open("urls_db.json", "r", encoding="utf-8") as file:
#             return json.load(file)
#     except FileNotFoundError:
#         return []
#
# def scrape_and_queue_urls(base_url, pages_limit=None, starting_page=1):
#     accumulated_urls = set(fetch_stored_urls())
#
#     for current_page in range(starting_page, starting_page + pages_limit if pages_limit else 1):
#         page_response = requests.get(base_url.format(current_page))
#
#         if page_response.status_code == 200:
#             page_soup = bs4.BeautifulSoup(page_response.text, "html.parser")
#             item_links = page_soup.select(".block-items__item__title")
#
#             for item in item_links:
#                 item_href = item.get("href")
#                 if item_href and "/booster/" not in item_href:
#                     complete_url = "https://999.md" + item_href
#                     accumulated_urls.add(complete_url)
#                     enqueue_url(complete_url)
#
#         else:
#             print(f"Page retrieval failed. Status code: {page_response.status_code}")
#
#     urls_list = list(accumulated_urls)
#     with open("urls_db.json", "w", encoding="utf-8") as file:
#         json.dump(urls_list, file, indent=4, ensure_ascii=False)
#
#     return urls_list
#
# def enqueue_url(resource_url):
#     queue_connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
#     queue_channel = queue_connection.channel()
#
#     queue_channel.queue_declare(queue='resource_queue')
#
#     queue_channel.basic_publish(exchange='', routing_key='resource_queue', body=resource_url)
#
#     queue_connection.close()
#
# if __name__ == "__main__":
#     scraped_urls = scrape_and_queue_urls("https://m.999.md/ro/list/phone-and-communication/fax", pages_limit=2)
#     print(f"Scraped {len(scraped_urls)} URLs.")
#
import requests
import json
from bs4 import BeautifulSoup
import pika

def fetch_stored_urls(file_path="urls_db.json"):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return []

def enqueue_url(resource_url, queue_name='resource_queue', host='localhost'):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host))
    channel = connection.channel()
    channel.queue_declare(queue=queue_name)
    channel.basic_publish(exchange='', routing_key=queue_name, body=resource_url)
    connection.close()

def scrape_and_queue_urls(base_url, queue_name='resource_queue', pages_limit=None, starting_page=1):
    accumulated_urls = set(fetch_stored_urls())

    page_format = base_url + "?page={}"
    for current_page in range(starting_page, starting_page + (pages_limit or 1)):
        response = requests.get(page_format.format(current_page))
        if response.ok:
            soup = BeautifulSoup(response.text, "html.parser")
            for item in soup.select(".block-items__item__title[href]"):
                item_href = item['href']
                if "/booster/" not in item_href:
                    complete_url = "https://999.md" + item_href
                    accumulated_urls.add(complete_url)
                    enqueue_url(complete_url, queue_name)
        else:
            print(f"Failed to retrieve page {current_page}: {response.status_code}")

    with open("urls_db.json", "w", encoding="utf-8") as file:
        json.dump(list(accumulated_urls), file, indent=4, ensure_ascii=False)

    return list(accumulated_urls)

if __name__ == "__main__":
    scraped_urls = scrape_and_queue_urls("https://m.999.md/ro/list/phone-and-communication/fax", pages_limit=2)
    print(f"Scraped {len(scraped_urls)} URLs.")
