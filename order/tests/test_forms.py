import pytest
from order.forms import OrderForm, ProductOrderFormsetInline

pytestmark = pytest.mark.django_db  # verhindert das nix in datenbank geschrieben wird
from mixer.backend.django import mixer
from django.test import RequestFactory


class TestOrderForm:
    def test_order_form_for_empty_validation(self):
        data = {}
        form = OrderForm(data)
        assert form.is_valid() is False, 'Should be False if Form is empty'

    def test_product_order_inline_formset_callable(self):
        obj = mixer.blend("order.Order")
        product_obj = mixer.blend("product.Product")
        request = RequestFactory().get("/order")
        formset = ProductOrderFormsetInline({
            'productorder_set-TOTAL_FORMS': '1',
            'productorder_set-INITIAL_FORMS': '0',
            'productorder_set-MIN_NUM_FORMS': '0',
            'productorder_set-MAX_NUM_FORMS': '1000',
            'productorder_set-0-product': 1,
            'productorder_set-0-amount': 20,
        }, instance=obj)
        assert formset.is_valid() is True, "formset should be Valid"
