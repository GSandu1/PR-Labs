import http.server
import socketserver
import re
import json
from jinja2 import Template


class Product:
    def __init__(self, name, author, price, description):
        self.name = name
        self.author = author
        self.price = price
        self.description = description


class CartItem:
    def __init__(self, product):
        self.product = product


class Cart:
    def __init__(self):
        self.items = []

    def add_item(self, item):
        self.items.append(item)

    def remove_item(self, index):
        if 0 <= index < len(self.items):
            del self.items[index]

    def get_total_cost(self):
        return sum(item.product.price for item in self.items)


class Templates:
    def __init__(self, products):
        self.products = products
        self.home = self._get_home_template()
        self.about = self._get_about_template()
        self.cart = self._get_cart_template()
        self.product = self._get_product_template()

    def _get_home_template(self):
        return Template("""
        <h1> home page</h1>
        <h2>Products</h2>
        {% for product in products %}
            <p><a href='/product/{{ loop.index }}'>{{ product.name }}</a> - Price: ${{ product.price }} <a href='/add_to_cart/{{ loop.index }}'>Add to Cart</a></p>
        {% endfor %}
        """)

    def _get_about_template(self):
        return Template("""
        <h1>About our store:</h1>
        <a href="/">Go back</a>
        <p>Rap never die</p>
        """)

    def _get_cart_template(self):
        return Template("""
        <h1>Your Cart</h1>
        <a href="/">Go back</a>
        {% if cart.items %}
            <ul>
            {% for item in cart.items %}
                <li>{{ item.product.name }} - Price: ${{ item.product.price }} <a href='/remove_from_cart/{{ loop.index }}'>Remove</a></li>
            {% endfor %}
            </ul>
            <p>Total Cost: ${{ cart.get_total_cost() }}</p>
        {% else %}
            <p>Your cart is empty</p>
        {% endif %}
        """)

    def _get_product_template(self):
        return Template("""
        <h1>{{ product.name }}</h1>
        <a href="/">Go back</a>
        <p>Author: {{ product.author }}</p>
        <p>Price: ${{ product.price }}</p>
        <p>Description: {{ product.description }}</p>
        """)


class RequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, templates, cart, **kwargs):
        self.templates = templates
        self.cart = cart
        super().__init__(*args, **kwargs)

    def do_GET(self):
        if self.path == '/':
            self._render(200, self.templates.home.render(products=self.templates.products))
        elif self.path == '/about':
            self._render(200, self.templates.about.render())
        elif self.path == '/cart':
            self._render(200, self.templates.cart.render(cart=self.cart))
        elif re.match(r'/product/\d+', self.path):
            product_id = int(self.path.split('/')[-1]) - 1
            if 0 <= product_id < len(self.templates.products):
                self._render(200, self.templates.product.render(product=self.templates.products[product_id]))
            else:
                self._render(404, "Product not found")
        elif re.match(r'/add_to_cart/\d+', self.path):
            product_id = int(self.path.split('/')[-1]) - 1
            if 0 <= product_id < len(self.templates.products):
                self.cart.add_item(CartItem(self.templates.products[product_id]))
                self._redirect('/cart')
            else:
                self._render(404, "Product not found")
        elif re.match(r'/remove_from_cart/\d+', self.path):
            item_id = int(self.path.split('/')[-1]) - 1
            self.cart.remove_item(item_id)
            self._redirect('/cart')
        else:
            self._render(404, "Page not found")

    def _render(self, status_code, content):
        self.send_response(status_code)
        self.end_headers()
        self.wfile.write(content.encode())

    def _redirect(self, location):
        self.send_response(302)
        self.send_header('Location', location)
        self.end_headers()


def load_products(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        products_data = json.load(file)
    return [Product(**data) for data in products_data]


def run_server(port, handler):
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"port {port}")
        httpd.serve_forever()


if __name__ == "__main__":
    products = load_products('products.json')
    cart = Cart()
    templates = Templates(products)
    handler = lambda *args, **kwargs: RequestHandler(*args, templates=templates, cart=cart, **kwargs)
    run_server(8081, handler)
