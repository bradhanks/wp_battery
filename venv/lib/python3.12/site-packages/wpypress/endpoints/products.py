import requests

class ProductsEndpoint:
    def __init__(self, client):
        self.client = client
        self.endpoint = f"{self.client.base_url}/wp-json/wc/v3/products"

    def list(self, params=None):
        """List products with optional filters and pagination metadata"""
        headers = self.client.auth.get_headers() if self.client.auth else {}
        response = requests.get(self.endpoint, headers=headers, params=params)
        response.raise_for_status()
        return response.json()

    def get(self, product_id):
        """Get a single product by ID"""
        url = f"{self.endpoint}/{product_id}"
        headers = self.client.auth.get_headers() if self.client.auth else {}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()

    def create(self, name, type='simple', regular_price=None, description='', **kwargs):
        """Create a new product"""
        data = {
            'name': name,
            'type': type,
            'regular_price': str(regular_price),
            'description': description,
        }
        data.update(kwargs)
        headers = {
            'Content-Type': 'application/json'
        }
        if self.client.auth:
            headers.update(self.client.auth.get_headers())

        response = requests.post(self.endpoint, json=data, headers=headers)
        response.raise_for_status()
        return response.json()

    def update(self, product_id, **kwargs):
        """Update an existing product"""
        url = f"{self.endpoint}/{product_id}"
        headers = {
            'Content-Type': 'application/json'
        }
        if self.client.auth:
            headers.update(self.client.auth.get_headers())

        response = requests.put(url, json=kwargs, headers=headers)
        response.raise_for_status()
        return response.json()

    def delete(self, product_id, force=False):
        """Delete a product"""
        url = f"{self.endpoint}/{product_id}"
        headers = self.client.auth.get_headers() if self.client.auth else {}
        params = {'force': 'true' if force else 'false'}
        response = requests.delete(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()

    def isWoocommerce(self):
        """Check if WooCommerce is installed"""
        url = f"{self.client.base_url}/wp-json/wc/v3"
        headers = self.client.auth.get_headers() if self.client.auth else {}
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return True
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return False
            else:
                raise

