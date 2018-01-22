import pytest
from mixer.backend.django import mixer

pytestmark = pytest.mark.django_db  # verhindert das nix in datenbank geschrieben wird
from django.test import Client
from django.test import RequestFactory
from stock.views import StockListView, StockCreateView
from stock.models import Stock


class TestStockView:

    def test_stock_get(self):
        # stock_object = mixer.blend("stock.Stock")

        client = Client()
        response = client.get("/stock/")
        assert response.status_code == 200, "Status Code should be 200"

    def test_stock_view(self):
        # order_object = mixer.blend("order.Order")

        request = RequestFactory().get("/")
        response = StockListView.as_view()(request)
        assert response.status_code == 200, "should Status_code 200"

    def test_stock_create_get(self):
        # stock_object = mixer.blend("stock.Stock")

        client = Client()
        response = client.get("/stock/create", follow=True)
        assert response.status_code == 200, "Status Code should be 200"

    def test_stock_create_view(self):
        # order_object = mixer.blend("order.Order")

        request = RequestFactory().get("/")
        response = StockCreateView.as_view()(request)
        assert response.status_code == 200, "should Status_code 200"

    def test_stockdocument_detail_get(self):
        stockdocument_object = mixer.blend("stock.Stockdocument")

        client = Client()
        response = client.get("/stock/document/" + str(stockdocument_object.pk), follow=True)
        assert response.status_code == 200, "Status Code should be 200"

    def test_stockdocument_detail_view(self):
        stockdocument_object = mixer.blend("stock.Stockdocument")

        request = RequestFactory().get("/")
        response = StockCreateView.as_view()(request)
        assert response.status_code == 200, "should Status_code 200"

# def test_get_csv_on_detail(self):
# 	stockdocument_object = mixer.blend("stock.Stockdocument", document="test.csv")
# 	assert stockdocument_object.document == None, "should Status_code 200"
