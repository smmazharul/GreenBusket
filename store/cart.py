from decimal import Decimal
from django.conf import settings
from .models import Product

class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get('cart')
        if not cart:
            cart = self.session['cart'] = {}
        self.cart = cart

    def add(self, product, variant_id=None, quantity=1):
        item_id = f"{product.id}_{variant_id}" if variant_id else str(product.id)
        
        if item_id not in self.cart:
            self.cart[item_id] = {
                'product_id': product.id,
                'variant_id': variant_id,
                'quantity': 0,
                'price': str(product.price)
            }
        
        self.cart[item_id]['quantity'] += int(quantity)
        self.save()

    def update(self, product, variant_id=None, quantity=1):
        item_id = f"{product.id}_{variant_id}" if variant_id else str(product.id)
        if int(quantity) <= 0:
            self.remove(product, variant_id)
        else:
            if item_id in self.cart:
                self.cart[item_id]['quantity'] = int(quantity)
                self.save()

    def remove(self, product, variant_id=None):
        item_id = f"{product.id}_{variant_id}" if variant_id else str(product.id)
        if item_id in self.cart:
            del self.cart[item_id]
            self.save()

    def save(self):
        self.session.modified = True

    def clear(self):
        if 'cart' in self.session:
            del self.session['cart']
            self.save()

    def get_total_price(self):
        return sum(Decimal(item['price']) * item['quantity'] for item in self.cart.values())

    def get_cart_data(self):
        items = []
        for item_id, item_data in self.cart.items():
            try:
                product = Product.objects.get(id=item_data['product_id'])
                items.append({
                    'item_id': item_id,
                    'product_id': product.id,
                    'name': product.name,
                    'price': item_data['price'],
                    'quantity': item_data['quantity'],
                    'image_url': product.image.url if product.image else None,
                })
            except Product.DoesNotExist:
                # If product was deleted, remove it from cart
                pass
        return {
            'items': items,
            'total_items': sum(item['quantity'] for item in self.cart.values()),
            'total_price': str(self.get_total_price())
        }
