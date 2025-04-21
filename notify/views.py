from bson import ObjectId
from rest_framework.views import APIView
from rest_framework.response import Response
from pymongo import MongoClient
from uuid import uuid4
from datetime import datetime
from notify.tasks import send_notification_task  # Celery task
import time
import logging
from django.conf import settings

mongo_client = MongoClient(settings.MONGO_URI, maxPoolSize=50)
db = mongo_client[settings.MONGO_DB_NAME]
notification_collection = db["notification"]


def convert_objectid_to_str(obj):
    if isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, dict):
        return {k: convert_objectid_to_str(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_objectid_to_str(i) for i in obj]
    return obj


logger = logging.getLogger(__name__)


class SendNotificationView(APIView):
    def post(self, request):
        start_time = time.time()

        data = request.data
        channel = data.get("channel")
        to = data.get("to")
        message = data.get("message")

        if not channel:
            return Response({"error": "channel is mandatory"}, status=400)
        if channel not in ["email", "sms", "pushNotification"]:
            return Response({"error": "channel is not valid"}, status=400)

        if not to:
            return Response({"error": "to is mandatory"}, status=400)

        if not message:
            return Response({"error": "message is mandatory"}, status=400)

        message_id = str(uuid4())
        payload = {
            "channel": channel,
            "to": to,
            "message": message,
            "creationDateTime": datetime.utcnow(),
            "status": "pending",
            "messageId": message_id
        }

        mongo_start = time.time()
        notification_collection.insert_one(payload)

        # Add retry_count for Celery
        payload["retry_count"] = 0
        safe_payload = convert_objectid_to_str(payload)

        task_start = time.time()
        try:
            send_notification_task.apply_async(args=[safe_payload], queue="send_notification")

            return Response({"messageId": message_id}, status=202)
        except:
            return Response({"error": "internal error"}, status=500)


class NotificationInquiry(APIView):
    def get(self, request):

        messageid = request.GET.get('messageId')

        query = {}

        if messageid:
            query["messageId"] = messageid

        cursor = notification_collection.find(query)
        notification_list = list(cursor)
        output = []
        for doc in notification_list:
            # Convert ObjectId to string
            doc_dict = {}
            for key, value in doc.items():
                if isinstance(value, ObjectId):
                    doc_dict[key] = str(value)
                else:
                    doc_dict[key] = value
            output.append(doc_dict)

        return Response(output, status=200)
