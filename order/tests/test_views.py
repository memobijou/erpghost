import pytest
from mixer.backend.django import mixer
pytestmark = pytest.mark.django_db  # verhindert das nix in datenbank geschrieben wird
from django.test import RequestFactory
from order.views import OrderUpdateView, ScanOrderTemplateView
from django.contrib.auth.models import AnonymousUser
from django.test import Client
from django.contrib import auth
from order.forms import OrderForm, ProductOrderFormsetInline
from order.models import Order


class TestScanOrderTemplateView:

	@pytest.fixture(autouse=True)
	def setup(self):
		self.order_object = mixer.blend("order.Order")

	def test_scan_order_get(self):
		client = Client()
		response = client.get("/order/" + str(self.order_object.pk) + "/scan", follow=True)
		assert response.status_code == 200, "Status Code should be 200"

	def test_scan_order_view(self):
		request = RequestFactory().get("/")
		response = ScanOrderTemplateView.as_view()(request, pk=self.order_object.pk)
		assert response.status_code == 200, "should return 200 Status"



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



