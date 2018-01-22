from django.shortcuts import render
from django.views.generic import ListView
from .models import Column


# Create your views here.


class ColumnListView(ListView):
    def get_queryset(self):
        queryset = Column.objects.all()
        # queryset = filter_queryset_from_request(self.request, Sku)
        # print("CHECK FOR EMPTY" + str(queryset))

        return queryset


def get_context_data(self, *args, **kwargs):
    context = super(ColumnListView, self).get_context_data(*args, **kwargs);
    # context["test"] = hallo()

    set_field_names_onview(context["object_list"], context)

    set_paginated_queryset_onview(context["object_list"], self.request, 15, context)

    return context
