# signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import Expense
from django.db import transaction
import requests

@receiver(post_save, sender=Expense)
def trigger_extraction_view(sender, instance, created, **kwargs):
    if instance.extracted:
        print("Extraction already done. Skipping signal.")
        return

    def send_extraction_request():
        try:
            expense_id = instance.id
            url = f"{settings.BASE_URL}/expenses/extract-ml/{expense_id}/"
            print(f"Calling URL: {url}")
            response = requests.get(url)
            if response.status_code == 200:
                print("Successfully called extraction view.")
            else:
                print(f"Failed to call extraction view. Status code: {response.status_code}")
        except Exception as e:
            print(f"Error calling extraction view: {e}")

    transaction.on_commit(send_extraction_request)
