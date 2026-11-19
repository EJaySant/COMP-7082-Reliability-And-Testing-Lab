"""Two simple smoke tests"""
import pytest
from setup_db import initialize
from repository import StoreRepository
from cart import ShoppingCart

@pytest.fixture
def db(tmp_path):
    path = tmp_path / "test.db"
    initialize(str(path))
    return str(path)

@pytest.fixture
def repository(db):
    return StoreRepository(db)

def test_seed_product(repository):
    assert repository.get_product('MOU-01').name == 'Wireless mouse'


def test_cart_adds_valid_item(repository):
    cart = ShoppingCart('student', repository)
    assert cart.add_item('USB-01', 2)
    assert len(cart.lines) == 1

