from product.models import Product
from product.views import ProductListView, ProductCreateView, ProductUpdateView, ProductListBaseView
from django.urls import reverse_lazy


class SingleProductListView(ProductListBaseView):
    queryset = Product.objects.filter(single_product=True)
    template_name = "single_product/product_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Einzelartikel Übersicht"
        return context

    def dispatch(self, request, *args, **kwargs):
        if self.request.GET.get("clear_filter", "") or "" == "1":
            filter_values = {"single_product_q": None, "single_product_ean": None, "single_product_sku": None,
                             "single_product_title": None, "single_product_manufacturer": None,
                             "single_product_brandname": None, "single_product_part_number": None,
                             "single_product_short_description": None, "single_product_long_description": None,
                             "single_product_order_by_amount": None}
            print(f"bibi: {filter_values}")
            for name, value in filter_values.items():
                request.session[name] = value
        return super().dispatch(request, *args, **kwargs)

    def set_filter_and_search_values_in_context(self, q, ean, sku, title, manufacturer, brandname, part_number,
                                                short_description, long_descripton, order_by_amount):
        self.context = {"single_product_q": q, "single_product_ean": ean, "single_product_sku": sku,
                        "single_product_title": title, "single_product_manufacturer": manufacturer,
                        "single_product_brandname": brandname, "single_product_part_number": part_number,
                        "single_product_short_description": short_description,
                        "single_product_long_description": long_descripton,
                        "single_product_order_by_amount": order_by_amount}
        print("UND ???????")
        return self.context

    def get_value_from_GET_or_session(self, value, request):
        get_value = request.GET.get(value)
        if get_value is not None:
            request.session[f"single_product_{value}"] = get_value.strip()
            return get_value
        else:
            if request.GET.get("q") is None:
                return request.session.get(f"single_product_{value}", "") or ""
            else:
                request.session[f"single_product_{value}"] = ""
                return ""


class SingleProductCreateView(ProductCreateView):
    def get_form(self, form_class=None):
        form = super().get_form()
        form.single_product = True
        return form

    def form_valid(self, form):
        instance = form.save(commit=False)
        instance.single_product = True
        return super().form_valid(form)
