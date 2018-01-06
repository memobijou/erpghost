import pytest
from mixer.backend.django import mixer
pytestmark = pytest.mark.django_db  # verhindert das nix in datenbank geschrieben wird
from django.test import Client
from django.test import RequestFactory
from stock.views import StockListView
from stock.models import Stock, Stockdocument


class TestStockModels:
	def test_fetching_all_stocks(self):
			objs = []
			mixer_obj = mixer.blend("stock.Stock")
			mixer_obj2 = mixer.blend("stock.Stock")
			objs.append(mixer_obj)
			objs.append(mixer_obj2)
			stocks = Stock.objects.all()
			assert len(objs) == len(stocks), "stocks should be same length as mixed Stocks" 

	def test_fetching_all_stocklists(self):
			objs = []
			mixer_obj = mixer.blend("stock.Stockdocument")
			mixer_obj2 = mixer.blend("stock.Stockdocument")
			objs.append(mixer_obj)
			objs.append(mixer_obj2)
			stockdocuments = Stockdocument.objects.all()
			assert len(objs) == len(stockdocuments), "stockdocuments should be same length as mixed Stockdocument.objects.all()" 
