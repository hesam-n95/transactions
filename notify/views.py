from bson import ObjectId
from rest_framework.views import APIView
from rest_framework.response import Response
from pymongo import MongoClient
from uuid import uuid4
from datetime import datetime
from notify.tasks import send_notification_task  # Celery task
import time
import logging

mongo_client = MongoClient("mongodb://localhost:27017", maxPoolSize=50)
db = mongo_client["zibal_db"]
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

        validate_time = time.time()
        print(f"Validation time: {validate_time - start_time:.4f} seconds")

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
        mongo_end = time.time()
        print(f"MongoDB insert time: {mongo_end - mongo_start:.4f} seconds")

        # Add retry_count for Celery
        payload["retry_count"] = 0
        safe_payload = convert_objectid_to_str(payload)

        task_start = time.time()
        send_notification_task.apply_async(args=[safe_payload], queue="send_notification")
        task_end = time.time()
        print(f"Celery task enqueue time: {task_end - task_start:.4f} seconds")

        total_time = time.time() - start_time
        print(f"Total request processing time: {total_time:.4f} seconds")

        return Response({"messageId": message_id}, status=202)


class NotificationInquiry(APIView):
    def get(self, request):

        messageid = request.GET.get('messageId')

        query = {}

        if messageid:
            query["messageId"] = messageid

        cursor = notification_collection.find(query)
        return Response(cursor, status=200)
