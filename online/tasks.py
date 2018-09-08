from Crypto.Cipher import AES
from celery import shared_task
import mws
import os
from xml.etree import ElementTree as Et
from datetime import datetime, timedelta
import time
from adress.models import Adress
from contact.models import Contact
from customer.models import Customer
from mission.models import Mission, ProductMission
from online.amazon import OrderMws
from online.ebay import Ebay
from product.models import Product
from online.models import Channel
from sku.models import Sku
import csv
from io import StringIO
import requests
import json
from client.models import Client
import base64


def decrypt_encrypted_string(encrypted_string):
    enc_key = os.environ.get("enc_key")
    print(enc_key)
    iv456 = "randomtask123456"
    aes_object = AES.new(enc_key, AES.MODE_CFB, iv456)
    encrypted_bytes = encrypted_string.encode("ISO-8859-1")
    password = aes_object.decrypt(encrypted_bytes)
    return password


@shared_task
def online_task():
    # save_amazon_orders()
    # save_ebay_orders()
    print("ONLINE CRONJOB AMAZON EBAY")


def save_amazon_orders():
    clients = Client.objects.filter(apidata__name__iexact="Amazon.de")
    for client in clients:
        amazon_api_data = client.apidata_set.filter(name="Amazon.de").first()

        if amazon_api_data is not None:
            access_key = decrypt_encrypted_string(amazon_api_data.access_key_encrypted)
            secret_key = decrypt_encrypted_string(amazon_api_data.secret_key_encrypted)
            account_id = decrypt_encrypted_string(amazon_api_data.account_id_encrypted)
            order_instance = OrderMws(access_key, secret_key, account_id, amazon_api_data)
            orders = order_instance.fetch_orders()
            print(f'Celery Task has run - Aufträge: {len(orders)}')


def save_ebay_orders():
    clients = Client.objects.filter(apidata__name__iexact="Ebay")
    for client in clients:
        ebay_api_data = client.apidata_set.filter(name="Ebay").first()

        if ebay_api_data is not None:
            ebay_instance = Ebay(client, ebay_api_data)
            ebay_instance.fetch_orders()
            print(f'Celery Task has run - Ebay')
