from rest_framework.views import APIView
from rest_framework.response import Response
from pymongo import MongoClient
import jdatetime
from bson.objectid import ObjectId
from datetime import datetime
from collections import defaultdict
from math import ceil
from django.conf import settings

mongo_client = MongoClient(settings.MONGO_URI, maxPoolSize=50)
db = mongo_client[settings.MONGO_DB_NAME]
transaction_collection = db["transaction"]
transaction_summary_collection = db["transaction_summary"]


class TransactionInquiryView(APIView):
    def get(self, request):
        t_type = request.GET.get('type')
        if not t_type:
            return Response({"error": "type is mandatory"}, status=400)
        if t_type not in ["count", "amount"]:
            return Response({"error": "type is not valid"}, status=400)

        mode = request.GET.get('mode')
        if not mode:
            return Response({"error": "mode is mandatory"}, status=400)
        if mode not in ["daily", "weekly", "monthly"]:
            return Response({"error": "mode is not valid"}, status=400)

        merchant_id = request.GET.get('merchantId')

        query = {}
        if merchant_id:
            try:
                query["merchantId"] = ObjectId(merchant_id)
            except Exception:
                return Response({"error": "merchantId is not valid"}, status=400)

        cursor = transaction_collection.find(query)

        grouped_data = defaultdict(int)
        for doc in cursor:
            created_at = doc.get("createdAt")
            if not created_at:
                continue
            if isinstance(created_at, dict) and "$date" in created_at:
                created_at = datetime.fromisoformat(created_at["$date"].replace("Z", "+00:00"))
            elif isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at)

            shamsi_date = jdatetime.datetime.fromgregorian(datetime=created_at)

            if mode == "daily":
                key = shamsi_date.strftime("%Y/%m/%d")
            elif mode == "weekly":
                day_of_year = shamsi_date.timetuple().tm_yday
                week_of_year = ceil(day_of_year / 7)
                key = f"هفته {week_of_year} سال {shamsi_date.year}"
            elif mode == "monthly":
                PERSIAN_MONTHS = {
                    1: "فروردین",
                    2: "اردیبهشت",
                    3: "خرداد",
                    4: "تیر",
                    5: "مرداد",
                    6: "شهریور",
                    7: "مهر",
                    8: "آبان",
                    9: "آذر",
                    10: "دی",
                    11: "بهمن",
                    12: "اسفند"
                }
                month_name = PERSIAN_MONTHS[shamsi_date.month]
                key = f"{month_name} {shamsi_date.year}"

            if t_type == "count":
                grouped_data[key] += 1
            elif t_type == "amount":
                grouped_data[key] += doc.get("amount", 0)

        response_data = [{"key": k, "value": v} for k, v in grouped_data.items()]
        return Response(response_data, status=200)


class CachedTransactionInquiryView(APIView):
    def get(self, request):
        t_type = request.GET.get('type')
        if not t_type:
            return Response({"error": "type is mandatory"}, status=400)
        if t_type not in ["count", "amount"]:
            return Response({"error": "type is not valid"}, status=400)

        mode = request.GET.get('mode')
        if not mode:
            return Response({"error": "mode is mandatory"}, status=400)
        if mode not in ["daily", "weekly", "monthly"]:
            return Response({"error": "mode is not valid"}, status=400)

        merchant_id = request.GET.get('merchantId')

        query = {
            "type": t_type,
            "mode": mode,
        }

        if merchant_id:
            query["merchantId"] = merchant_id

        cursor = transaction_summary_collection.find(query)
        data = [{"key": doc["key"], "value": doc["value"]} for doc in cursor]

        return Response(data, status=200)
