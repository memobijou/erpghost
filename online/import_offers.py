from celery import Task
from online.forms import ImportForm
from django.views import View
from celery.result import AsyncResult
from erpghost import app
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
import csv
from django.shortcuts import render, get_object_or_404
from celery import shared_task
from online.models import Offer


class AmazonImportOffersTask(Task):
    ignore_result = True

    def __init__(self, arg):
        self.result = arg
        print(f"before run: {self.result}")

    def run(self):
        print(f"in celery run: {self.result}")
        self.get_amazon_offers()

    def get_amazon_offers(self):
        bulk_instances = []
        count = 0
        for row in self.result:
            if count == 0:
                count = count + 1
                continue
            offer = Offer.objects.filter(sku=row[0], asin=row[1]).first()
            if offer is None:
                if row[3] is not None and row[3] != "":
                    offer = Offer(sku=row[0], asin=row[1], amount=row[3])
                    bulk_instances.append(offer)
            else:
                if row[3] is not None and row[3] != "":
                    offer.amount = row[3]
                    offer.save()
        Offer.objects.bulk_create(bulk_instances)


class ImportOffersView(View):
    template_name = "online/import_offers.html"

    def __init__(self):
        super().__init__()
        self.form = None
        self.context = {}
        self.result = None
        self.header = None

    def dispatch(self, request, *args, **kwargs):
        self.form = self.get_form()
        self.context = self.get_context()
        profile = request.user.profile
        if profile is not None and profile.celery_import_task_id is not None:
            result = AsyncResult(request.user.profile.celery_import_task_id, app=app)
            print(result.status)
            print(f"baby 3: {result.status}")
            if result.status == "SUCCESS":
                request.user.profile.celery_import_task_id = None
                request.user.profile.save()
                messages.success(request, "Aufträge wurden erfolgreich importiert")
                return HttpResponseRedirect(reverse_lazy("online:import_offers"))
            if result.status == "PENDING":
                self.context["still_pending"] = True
        print("But why !?")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.context)

    def get_form(self):
        if self.request.method == "POST":
            print("waaaas?")
            return ImportForm(self.request.POST, self.request.FILES)
        else:
            return ImportForm()

    def post(self, request, *args, **kwargs):
        self.fetch_amazon_offers()
        if self.result is not None:
            print(f"HELLLOOO")
            response = amazon_offers_import_task.delay(self.result)
            print(f"baby: {response.status}")
            print(f"baby: {response.id}")
            self.request.user.profile.celery_import_task_id = response.id
            self.request.user.profile.save()
        return HttpResponseRedirect(reverse_lazy("online:import_offers"))

    def get_context(self):
        self.context = {"title": "Angebote importieren", "form": self.form}
        return self.context

    def fetch_amazon_offers(self):
        if self.form.is_valid() is True:
            import_file = self.form.cleaned_data.get("import_file")
            print(f"banana: {import_file.name}")
            file_ending = import_file.name.split(".")[-1]
            print(file_ending)

            if file_ending.lower() == "csv":
                from io import TextIOWrapper
                data = TextIOWrapper(import_file.file, encoding="latin1")
                self.result = self.get_csv_content(data)
                print(f"babo: {self.result}")

            if file_ending.lower() == "txt":
                from io import TextIOWrapper
                data = TextIOWrapper(import_file.file, encoding="utf-8")
                file_reader = csv.reader(data, delimiter='\t')
                self.result = list(file_reader)


@shared_task
def amazon_offers_import_task(arg_list):
    amazon_import_instance = AmazonImportOffersTask(arg_list)
    amazon_import_instance.run()
