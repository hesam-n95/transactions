from django.core.management.base import BaseCommand
from pymongo import MongoClient
import jdatetime
from datetime import datetime
from collections import defaultdict
from math import ceil
from django.conf import settings
import logging

logger = logging.getLogger('cache')

PERSIAN_MONTHS = {
    1: "فروردین", 2: "اردیبهشت", 3: "خرداد", 4: "تیر",
    5: "مرداد", 6: "شهریور", 7: "مهر", 8: "آبان",
    9: "آذر", 10: "دی", 11: "بهمن", 12: "اسفند"
}

mongo_client = MongoClient(settings.MONGO_URI, maxPoolSize=50)
db = mongo_client[settings.MONGO_DB_NAME]
transaction_collection = db["transaction"]
transaction_summary_collection = db["transaction_summary"]

class Command(BaseCommand):
    help = "Aggregate transaction data and store in transaction_summary collection"

    def handle(self, *args, **kwargs):

        # Clear previous cache
        transaction_summary_collection.delete_many({})

        cursor = transaction_collection.find({})
        summaries = {
            "daily": defaultdict(int),
            "weekly": defaultdict(int),
            "monthly": defaultdict(int)
        }
        amount_summaries = {
            "daily": defaultdict(int),
            "weekly": defaultdict(int),
            "monthly": defaultdict(int)
        }

        for doc in cursor:
            created_at = doc.get("createdAt")
            if isinstance(created_at, dict) and "$date" in created_at:
                created_at = datetime.fromisoformat(created_at["$date"].replace("Z", "+00:00"))
            elif isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at)

            shamsi_date = jdatetime.datetime.fromgregorian(datetime=created_at)
            day_key = shamsi_date.strftime("%Y/%m/%d")
            week_key = f"هفته {ceil(shamsi_date.timetuple().tm_yday / 7)} سال {shamsi_date.year}"
            month_key = f"{PERSIAN_MONTHS[shamsi_date.month]} {shamsi_date.year}"
            merchant = str(doc.get("merchantId"))

            for mode, key in [("daily", day_key), ("weekly", week_key), ("monthly", month_key)]:
                summaries[mode][(key, merchant)] += 1
                amount_summaries[mode][(key, merchant)] += doc.get("amount", 0)

        # Insert into cache collection
        for mode in summaries:
            for (key, merchantId), count in summaries[mode].items():
                amount = amount_summaries[mode][(key, merchantId)]
                transaction_summary_collection.insert_one({
                    "mode": mode,
                    "type": "count",
                    "key": key,
                    "value": count,
                    "merchantId": merchantId
                })
                transaction_summary_collection.insert_one({
                    "mode": mode,
                    "type": "amount",
                    "key": key,
                    "value": amount,
                    "merchantId": merchantId
                })

        logger.info("Cached summaries saved to 'transaction_summary'")
        self.stdout.write(self.style.SUCCESS("Cached summaries saved to 'transaction_summary'"))
