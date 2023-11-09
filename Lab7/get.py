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
    worker_threads = [Thread(target=consume_queue, args=(i,)) for i in range(10)]
    for thread in worker_threads:
        thread.start()
    for thread in worker_threads:
        thread.join()
