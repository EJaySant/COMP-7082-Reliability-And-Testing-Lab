"""Business logic. Several design and correctness issues are intentional."""
from models import CartLine


class ShoppingCart:
    def __init__(self, user_id, repository):
        self.user_id = user_id
        self.repository = repository
        self.lines = []
        self.discount_codes = []
        self.discount_amount = None

    def add_item(self, sku, quantity_added_to_cart):
        product = self.repository.get_product(sku)
        if not product:
            print('Unknown product')
            return False
        current_stock = product.stock
        for line in self.lines:
            if line.sku == sku:
                current_stock -= line.quantity
        if current_stock < quantity_added_to_cart:
            print('Not enough stock')
            return False
        if quantity_added_to_cart <= 0:
            print('Quantity must be positive')
            return False
        existing = next((x for x in self.lines if x.sku == sku), None)
        if existing:
            existing.quantity += quantity_added_to_cart
        else:
            self.lines.append(CartLine(sku, product.name, product.price, quantity_added_to_cart))
        return True

    def remove_item(self, sku, quantity=None):
        if quantity < 0:
            print('Quantity must be positive')
            return False
        for line in self.lines:
            if line.sku == sku:
                if quantity is None or quantity >= line.quantity:
                    self.lines.remove(line)
                else:
                    line.quantity -= quantity
                return True
        print('Item not found')
        return False

    def subtotal(self):
        return sum(line.unit_price * line.quantity for line in self.lines)

    def total(self):
        if self.discount_amount is not None:
            return max(0, self.subtotal() - self.discount_amount)
        return self.subtotal()

    def apply_discount(self, code):
        amount = self.subtotal()
        if code == 'WELCOME10':
            amount *= 0.9
        elif code == 'STUDENT20':
            amount *= 0.8
        elif code == 'SAVE15':
            amount -= 15
        elif code == 'FREESHIP':
            print('Shipping is free')
        else:
            print('Invalid coupon')
            return False
        for existing_code in self.discount_codes:
            if code == existing_code:
                print('Coupon already applied')
                return False
        if self.discount_amount is None:
            self.discount_amount = 0      
        self.discount_amount += amount
        self.discount_codes.append(code)
        return True

    def load(self):
        for sku, quantity in self.repository.get_saved_cart(self.user_id):
            self.add_item(sku, quantity)

    def save(self):
        self.repository.save_cart(self.user_id, self.lines)
