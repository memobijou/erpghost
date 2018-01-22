import pytest
from order.models import Order
from mixer.backend.django import mixer

pytestmark = pytest.mark.django_db


class TestOrderModel:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.mixer_objects = []
        for i in range(10):
            mixer_obj = mixer.blend("order.Order")
            self.mixer_objects.append(mixer_obj)

    def test_fetching_all_orders(self):
        orders = Order.objects.all()
        assert len(self.mixer_objects) == len(orders), "orders should be same length as mixed orders"

    def test_fetching_all_products_from_order(self):
        order_object = self.mixer_objects[0]
        products = order_object.products.all()
        assert products != None, "products should be initialized"
