import pytest
from mixer.backend.django import mixer

pytestmark = pytest.mark.django_db  # verhindert das nix in datenbank geschrieben wird
from django.test import RequestFactory
from order.views import OrderUpdateView, ScanOrderUpdateView
from django.contrib.auth.models import AnonymousUser
from django.test import Client
from django.contrib import auth
from order.forms import OrderForm, ProductOrderFormsetInline
from order.models import Order
from django.utils import timezone
import pytz


class TestScanOrderTemplateView:

    # @pytest.fixture(autouse=True)
    # def setup(self):
    # 	self.order_object = mixer.blend("order.Order")

    def test_scan_order_get(self):
        order_object = mixer.blend("order.Order")

        client = Client()
        response = client.get("/order/" + str(order_object.pk) + "/scan", follow=True)
        assert response.status_code == 200, "Status Code should be 200"

    def test_scan_order_view(self):
        order_object = mixer.blend("order.Order")

        request = RequestFactory().get("/")
        response = ScanOrderUpdateView.as_view()(request, pk=order_object.pk)
        assert response.status_code == 200, "should return 200 Status"

    def test_scan_order_view_POST_change_confirmed_from_none_to_true(self):
        product = mixer.blend("product.Product")
        order_object = mixer.blend("order.Order", products=product)

        data = {"confirmed": 1, "product_id": product.pk}
        request = RequestFactory().post("/", data=data)
        response = ScanOrderUpdateView.as_view()(request, pk=order_object.pk)
        assert response.status_code == 302, "should redirect to GET page so should be 302 status"
        order_object.refresh_from_db()
        updated_product_order = order_object.productorder_set.all()[0]
        assert updated_product_order.confirmed == 1, "Should be confirmed with value 1"

    def test_post_product_on_order_with_request_to_url(self):
        order_object = mixer.blend("order.Order", confirmed=None, delivery_date=timezone.now())

        before_value = order_object.confirmed
        order_object.confirmed = True
        order_object.save()
        order_object.refresh_from_db()
        after_value = order_object.confirmed

        assert before_value != after_value, "Should not be the same as before after updated"

        data = {}
        client = Client()
        response = client.get("/order/" + str(order_object.pk) + "/scan/", follow=True)
        assert response.status_code == 200, "Status Code of scan order after update should be 200"

        data = {"confirmed": True}
        response = client.post("/order/" + str(order_object.pk) + "/scan/", data, follow=True)
        assert response.status_code == 200, "Status Code of scan order after update should be 200"


# from selenium import webdriver

class TestOrderProductView:
    # def setup_method(self):
    # 	self.browser = webdriver.Firefox()

    # def teardown_method(self):
    # 	self.browser.quit()

    def test_order_update_view(self):
        obj = mixer.blend("order.Order")
        request = RequestFactory().get("/order")
        testUser = mixer.blend("auth.User", username="test", password="test")

        request.user = testUser
        response = OrderUpdateView.as_view()(request, pk=1)
        assert response.status_code == 200, "Should be 200 Status"

    def test_get(self):
        client = Client()
        # here was can assume `request.user` is the AnonymousUser
        # or I can use `c.login(..)` to log someone in

        response = client.get("/order/1/edit")

        assert response.status_code == 301, "Should be 301 Status"

    def test_order_update_view_post_method(self):
        obj = mixer.blend("order.Order")
        obj.status = "INITSTATUS"
        product_obj = mixer.blend("product.Product")
        testUser = mixer.blend("auth.User", username="test", password="test")
        data = {"delivery_date": "15/12/2017", "ordernumber": 213435453, "status": "UPDATEDSTATUS",
                'productorder_set-TOTAL_FORMS': '1',
                'productorder_set-INITIAL_FORMS': '0',
                'productorder_set-MIN_NUM_FORMS': '0',
                'productorder_set-MAX_NUM_FORMS': '1000',
                'productorder_set-0-product': 1,
                'productorder_set-0-amount': 20,
                }
        assert obj.products.count() == 0, "There should be no products before request"
        request = RequestFactory().post('/', data=data)
        request.user = testUser
        response = OrderUpdateView.as_view()(request, pk=obj.pk)
        obj.refresh_from_db()
        assert obj.products.count() == 1, "There should be one products after response"

        assert response.status_code == 302, "should redirect to success page"
        assert obj.status == "UPDATEDSTATUS", "Should be updated"
