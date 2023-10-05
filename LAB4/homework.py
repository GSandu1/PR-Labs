import socket


class WebScraper:
    def __init__(self, host="localhost", port=8081, buffer_size=4096):
        self.HOST = host
        self.PORT = port
        self.BUFFER_SIZE = buffer_size
        self.pages_content = {}
        self.products = []

    def fetch_page_content(self, path):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.HOST, self.PORT))
            request = f"GET {path} HTTP/1.1\r\nHost: {self.HOST}\r\nConnection: close\r\n\r\n"
            s.sendall(request.encode())

            chunks = []
            while True:
                chunk = s.recv(self.BUFFER_SIZE)
                if not chunk:
                    break
                chunks.append(chunk)

            content = b"".join(chunks).decode("utf-8")
            return content.split("\r\n\r\n", 1)[1]

    def extract_product_links(self, content):
        return [line.split('\'')[1] for line in content.splitlines() if "/product/" in line]

    def extract_product_details(self, content):
        lines = content.splitlines()
        details = {
            "name": next(line for line in lines if '<h1>' in line).replace('<h1>', '').replace('</h1>', '').strip(),
            "author": next(line for line in lines if 'Author:' in line).split(': ')[1].replace('</p>', '').strip(),
            "price": float(next(line for line in lines if 'Price:' in line).split('$')[1].replace('</p>', '').strip()),
            "description": next(line for line in lines if 'Description:' in line).split(': ')[1].replace('</p>', '').strip()
        }
        return details

    def scrape(self):
        home_page_content = self.fetch_page_content("/")
        self.pages_content["/"] = home_page_content
        product_links = self.extract_product_links(home_page_content)

        for path in product_links:
            page_content = self.fetch_page_content(path)
            self.pages_content[path] = page_content
            if "/product/" in path:
                product_details = self.extract_product_details(page_content)
                self.products.append(product_details)

    def display_results(self):
        print("Pages Content:")
        for path, content in self.pages_content.items():
            print(f"Path: {path}\n{content}\n\n{'-' * 50}\n")

        print("Products Details:")
        for product in self.products:
            print(product)


if __name__ == "__main__":
    scraper = WebScraper()
    scraper.scrape()
    scraper.display_results()
