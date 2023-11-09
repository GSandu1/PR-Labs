# import pika
# import bs4
# import requests
# from threading import Thread, Lock
# from tinydb import TinyDB
#
# storage_db = TinyDB('storage_db.json', indent=4, ensure_ascii=False, encoding='utf-8')
# data_access_lock = Lock()
#
# def fetch_and_store(ch, method_frame, header_frame, body_content, worker_id):
#     try:
#         resource_url = body_content.decode()
#
#         site_response = requests.get(resource_url)
#
#         if site_response.status_code == 200:
#             content_soup = bs4.BeautifulSoup(site_response.text, "html.parser")
#             heading = content_soup.find('header', {"class": "adPage__header"}).text.strip()
#
#             price_tag = content_soup.find('span', {"class": "adPage__content__price-feature__prices__price__value"})
#             price_text = price_tag.text.strip() if price_tag else "Unavailable"
#
#             currency_tag = content_soup.find('span', {"class": "adPage__content__price-feature__prices__price__currency"})
#             currency_text = currency_tag.text.strip() if currency_tag else ""
#
#             description_tag = content_soup.find('div', {"class": "adPage__content__description grid_18", "itemprop": "description"})
#             description_text = description_tag.text.strip() if description_tag else "No description"
#
#             data_record = {
#                 "heading": heading,
#                 "cost": price_text + currency_text,
#                 "details": description_text,
#             }
#
#             with data_access_lock:
#                 storage_db.insert(data_record)
#
#             print(f"Worker {worker_id} has processed: {resource_url}")
#
#         else:
#             print(f"Worker {worker_id} could not process {resource_url}. Status code: {site_response.status_code}")
#     except Exception as error:
#         print(f"Worker {worker_id} encountered an error with {resource_url}: {error}")
#
# def worker_process(worker_num):
#     queue_connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
#     queue_channel = queue_connection.channel()
#     queue_channel.queue_declare(queue='resource_queue')
#
#     queue_channel.basic_consume(queue='resource_queue', on_message_callback=lambda channel, method, properties, body: fetch_and_store(channel, method, properties, body, worker_num), auto_ack=True)
#     queue_channel.start_consuming()
#
# if __name__ == "__main__":
#     worker_count = 7
#     print(f'Starting {worker_count} workers for URL processing.')
#
#     worker_threads = []
#
#     for worker_index in range(worker_count):
#         thread = Thread(target=worker_process, args=(worker_index,))
#         thread.start()
#         worker_threads.append(thread)
#
#     for thread in worker_threads:
#         thread.join()
#
#

import requests
from bs4 import BeautifulSoup
from threading import Thread, Lock
from tinydb import TinyDB
import pika

storage_db = TinyDB('storage_db.json', indent=4, ensure_ascii=False, encoding='utf-8')
data_access_lock = Lock()

def process_url(resource_url, worker_id):
    try:
        response = requests.get(resource_url)
        if response.ok:
            soup = BeautifulSoup(response.text, "html.parser")
            header = soup.find('header', {"class": "adPage__header"})
            price_value = soup.find('span', {"class": "adPage__content__price-feature__prices__price__value"})
            price_currency = soup.find('span', {"class": "adPage__content__price-feature__prices__price__currency"})
            description = soup.find('div', {"class": "adPage__content__description"})

            heading = header.get_text(strip=True) if header else "No heading"
            price = price_value.get_text(strip=True) if price_value else "No price"
            currency = price_currency.get_text(strip=True) if price_currency else ""
            details = description.get_text(strip=True) if description else "No description"

            with data_access_lock:
                storage_db.insert({"heading": heading, "cost": price + ' ' + currency, "details": details})
            print(f"Worker {worker_id} processed: {resource_url}")
        else:
            print(f"Worker {worker_id} failed with {resource_url}: {response.status_code}")
    except Exception as e:
        print(f"Worker {worker_id} encountered an error with {resource_url}: {e}")

def consume_queue(worker_id, queue_name='resource_queue', host='localhost'):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host))
    channel = connection.channel()
    channel.queue_declare(queue=queue_name)
    for method_frame, properties, body in channel.consume(queue_name):
        process_url(body.decode(), worker_id)
        channel.basic_ack(method_frame.delivery_tag)

if __name__ == "__main__":
    worker_threads = [Thread(target=consume_queue, args=(i,)) for i in range(7)]
    for thread in worker_threads:
        thread.start()
    for thread in worker_threads:
        thread.join()
