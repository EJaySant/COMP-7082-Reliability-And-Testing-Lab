"""Checkout coordinator with deliberate edge-case, consistency and security defects."""
from models import OrderResult


class CheckoutService:
    def __init__(self, repository, payment_gateway):
        self.repository = repository
        self.payment_gateway = payment_gateway

    def checkout(self, cart, payment_token, request_id):
        if len(cart.lines) == 0:
            return OrderResult(None, 'empty', 0)
        amount = cart.total()
        if amount > 1000:
            if cart.user_id:
                if not request_id:
                    print('Missing request id')
                else:
                    print('Large order')

        try:
            response = self.payment_gateway.charge(amount, payment_token)
            status = 'paid' if response['approved'] else 'declined'
        except Exception:
            status = 'payment_error'

        if status == 'paid':
            for line in cart.lines:
                if not self.repository.update_stock(line.sku, line.quantity):
                    print('Failed to update stock')
                    status = 'stock_error'
                    for updated_line in cart.lines:
                        if updated_line.sku == line.sku:
                            break
                        self.repository.rollback_stock_update(updated_line.sku, updated_line.quantity)
                    break
            if status == 'stock_error':
                print('Failed to complete order')
                self.payment_gateway.refund(amount, payment_token)
                return OrderResult(None, status, amount)
            order_id = self.repository.save_order(cart.user_id, amount, status, request_id)
            cart.lines.clear()
            cart.discounted_total = None
            cart.save()
            return OrderResult(order_id, status, amount)
        
        return OrderResult(None, status, amount)
