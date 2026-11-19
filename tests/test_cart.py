import pytest

from cart import ShoppingCart
from checkout import CheckoutService
from repository import StoreRepository
from setup_db import initialize


@pytest.fixture
def db(tmp_path):
    path = tmp_path / "test.db"
    initialize(str(path))
    return str(path)


@pytest.fixture
def repository(db):
    return StoreRepository(db)


@pytest.fixture
def cart(repository):
    return ShoppingCart("student", repository)


def test_add_item_stores_name_price_and_quantity(cart):
    assert cart.add_item("MOU-01", 2)
    assert len(cart.lines) == 1
    assert cart.lines[0].name == "Wireless mouse"
    assert cart.lines[0].unit_price == 29.95
    assert cart.lines[0].quantity == 2


@pytest.mark.parametrize("quantity", [0, -1, -100])
def test_add_item_rejects_non_positive_quantities(cart, quantity):
    assert not cart.add_item("MOU-01", quantity)
    assert cart.lines == []


def test_add_duplicate_product_merges_quantity(cart):
    assert cart.add_item("MOU-01", 3)
    assert cart.add_item("MOU-01", 2)
    assert len(cart.lines) == 1
    assert cart.lines[0].quantity == 5


def test_add_duplicate_product_cannot_exceed_available_stock(cart):
    assert cart.add_item("MOU-01", 12)
    assert not cart.add_item("MOU-01", 9)
    assert cart.lines[0].quantity == 12


def test_remove_item_supports_partial_and_full_removal(cart):
    cart.add_item("USB-01", 5)
    assert cart.remove_item("USB-01", 2)
    assert cart.lines[0].quantity == 3
    assert cart.remove_item("USB-01", 5)
    assert cart.lines == []


@pytest.mark.parametrize("quantity", [-1, -20])
def test_remove_item_rejects_negative_quantities(cart, quantity):
    cart.add_item("USB-01", 3)
    assert not cart.remove_item("USB-01", quantity)
    assert cart.lines[0].quantity == 3


def test_subtotal_is_sum_of_line_totals(cart):
    cart.add_item("USB-01", 2)
    assert cart.subtotal() == pytest.approx(19.98)


def test_duplicate_coupon_is_rejected(cart):
    cart.add_item("USB-01", 1)
    assert cart.apply_discount("SAVE15")
    assert cart.apply_discount("SAVE15") is False
    assert cart.discount_codes == ["SAVE15"]


def test_invalid_discount_is_rejected(cart):
    cart.add_item("USB-01", 1)
    assert cart.apply_discount("NOT-A-COUPON") is False
    assert cart.discount_amount is None


class FakePaymentGateway:
    def __init__(self, approved=True, raises=False):
        self.approved = approved
        self.raises = raises
        self.calls = []
        self.refunds = []

    def charge(self, amount, payment_token):
        self.calls.append((amount, payment_token))
        if self.raises:
            raise RuntimeError("gateway unavailable")
        return {"approved": self.approved}

    def refund(self, amount, payment_token):
        self.refunds.append((amount, payment_token))


def test_checkout_rejects_empty_cart(repository):
    cart = ShoppingCart("student", repository)
    gateway = FakePaymentGateway()
    result = CheckoutService(repository, gateway).checkout(cart, "tok_test", "req-1")
    assert result.status == "empty"
    assert result.order_id is None
    assert gateway.calls == []


def test_checkout_declined_payment_does_not_create_order_or_change_stock(repository):
    cart = ShoppingCart("student", repository)
    cart.add_item("MOU-01", 2)
    gateway = FakePaymentGateway(approved=False)
    result = CheckoutService(repository, gateway).checkout(cart, "tok_test", "req-2")
    assert result.status == "declined"
    assert result.order_id is None
    assert repository.get_product("MOU-01").stock == 20
    assert cart.lines


def test_unavailable_stock_refunds_and_rolls_back_previous_updates(db, repository):
    cart = ShoppingCart("student", repository)
    cart.add_item("MOU-01", 1)
    cart.add_item("USB-01", 1)
    with repository.connect() as conn:
        conn.execute("UPDATE products SET stock = 0 WHERE sku = 'USB-01'")

    gateway = FakePaymentGateway(approved=True)
    result = CheckoutService(repository, gateway).checkout(cart, "tok_test", "req-3")
    assert result.status == "stock_error"
    assert result.order_id is None
    assert gateway.refunds
    assert repository.get_product("MOU-01").stock == 20
    assert repository.get_product("USB-01").stock == 0


def test_unexpected_payment_error_is_handled_without_stock_or_order_changes(repository):
    cart = ShoppingCart("student", repository)
    cart.add_item("USB-01", 1)
    gateway = FakePaymentGateway(raises=True)
    result = CheckoutService(repository, gateway).checkout(cart, "tok_test", "req-4")
    assert result.status == "payment_error"
    assert result.order_id is None
    assert repository.get_product("USB-01").stock == 50