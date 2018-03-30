from celery import shared_task
import requests
from io import BytesIO
from django.core.files import File
from product.models import Product


@shared_task
def upload_images_to_matching_products_task(product_list):
    for ean, title, image_url in product_list:
        if image_url == "":
            continue
        product_object = Product.objects.filter(ean=ean, title=title).first()
        if product_object:
            response = requests.get(image_url)
            if response.status_code == 200:
                image = BytesIO(requests.get(image_url).content)
                product_object.main_image.save("img", File(image))
                print(product_object.main_image)
