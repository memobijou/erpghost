import pytest
from mixer.backend.django import mixer
pytestmark = pytest.mark.django_db  # verhindert das nix in datenbank geschrieben wird
from django.test import Client
from django.test import RequestFactory
from stock.views import StockListView
from stock.models import Stock
from stock.forms import StockdocumentForm

class TestStockForm:

	def test_upload_form_stock_for_empty_validation(self):
		data = {}
		form = StockdocumentForm(data)
		assert form.is_valid() is False, 'Should be False if Form is empty'

