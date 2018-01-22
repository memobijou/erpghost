import pytest
from mixer.backend.django import mixer

pytestmark = pytest.mark.django_db  # verhindert das nix in datenbank geschrieben wird
from django.test import RequestFactory
from django.test import Client


class TestMainView:
    def test_main_get(self):
        client = Client()
        response = client.get("/")
        assert response.status_code == 200, "Status Code should be 200"

# def test_stock_view(self):
# 	order_object = mixer.blend("order.Order")

# 	request = RequestFactory().get("/")
# 	response = ScanOrderTemplateView.as_view()(request, pk=order_object.pk)
# 	assert response.status_code == 200, "should return 200 Status"
