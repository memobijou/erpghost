from product.models import Product
from product.views import ProductListView, ProductCreateView, ProductUpdateView
from django.urls import reverse_lazy


class SingleProductListView(ProductListView):
    queryset = Product.objects.filter(single_product=True)
    template_name = "single_product/product_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Einzelartikel Übersicht"
        return context


class SingleProductCreateView(ProductCreateView):
    def get_form(self, form_class=None):
        form = super().get_form()
        form.single_product = True
        return form

    def form_valid(self, form):
        instance = form.save(commit=False)
        instance.single_product = True
        return super().form_valid(form)
