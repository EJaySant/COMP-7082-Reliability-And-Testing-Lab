import pytest

from models import CartLine
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


def test_get_product_returns_seeded_product(repository):
    product = repository.get_product("MOU-01")
    assert product.name == "Wireless mouse"
    assert product.price == pytest.approx(29.95)
    assert product.stock == 20


def test_get_product_returns_none_for_unknown_sku(repository):
    assert repository.get_product("missing") is None


def test_get_product_handles_sql_like_text_as_literal_input(repository):
    assert repository.get_product("MOU-01' OR 1=1 --") is None


def test_saved_cart_is_replaced_instead_of_appended(repository):
    first = [CartLine("MOU-01", "Wireless mouse", 29.95, 2)]
    second = [CartLine("USB-01", "USB cable", 9.99, 1)]
    repository.save_cart("student", first)
    repository.save_cart("student", second)
    assert repository.get_saved_cart("student") == [("USB-01", 1)]


def test_saved_carts_are_isolated_by_user(repository):
    repository.save_cart("alice", [CartLine("USB-01", "USB cable", 9.99, 2)])
    repository.save_cart("bob", [CartLine("MOU-01", "Wireless mouse", 29.95, 1)])
    assert repository.get_saved_cart("alice") == [("USB-01", 2)]
    assert repository.get_saved_cart("bob") == [("MOU-01", 1)]


def test_update_stock_successfully_decrements(repository):
    assert repository.update_stock("MOU-01", 3)
    assert repository.get_product("MOU-01").stock == 17


def test_update_stock_rejects_quantity_exceeding_available_stock(repository):
    assert repository.update_stock("MOU-01", 21) is False
    assert repository.get_product("MOU-01").stock == 20


def test_rollback_stock_update_restores_quantity(repository):
    assert repository.update_stock("USB-01", 4)
    repository.rollback_stock_update("USB-01", 4)
    assert repository.get_product("USB-01").stock == 50


def test_save_order_and_list_orders_are_isolated_by_user(repository):
    first_id = repository.save_order("alice", 10.0, "paid", "req-alice")
    second_id = repository.save_order("bob", 20.0, "paid", "req-bob")
    assert isinstance(first_id, int)
    assert isinstance(second_id, int)
    assert repository.list_orders("alice") == [(first_id, "alice", 10.0, "paid")]
    assert repository.list_orders("bob") == [(second_id, "bob", 20.0, "paid")]