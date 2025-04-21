from bson import ObjectId
from rest_framework.views import APIView
from rest_framework.response import Response
from pymongo import MongoClient
from uuid import uuid4
from datetime import datetime
from notify.tasks import send_notification_task
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
        data = request.data
        channels = data.get("channels", [])
        message = data.get("message")

        if not isinstance(channels, list) or not channels:
            return Response({"error": "channels must be a non-empty list"}, status=400)

        if not message:
            return Response({"error": "message is mandatory"}, status=400)

        valid_channels = ["email", "sms", "bot"]

        enriched_channels = []
        for item in channels:
            channel = item.get("channel")
            to = item.get("to")
            if not channel:
                return Response({"error": "channel is mandatory"}, status=400)
            elif channel not in valid_channels:
                return Response({"error": "channel is mandatory"}, status=400)
            elif not to:
                return Response({"error": "to is mandatory"}, status=400)
            else:
                enriched_channels.append({
                    "channel": channel,
                    "to": to,
                    "status": "pending"
                })

        message_id = str(uuid4())
        creation_time = datetime.utcnow()

        db_payload = {
            "messageId": message_id,
            "message": message,
            "channels": enriched_channels,
            "creationDateTime": creation_time
        }

        notification_collection.insert_one(db_payload)

        for item in enriched_channels:
            task_payload = {
                "channel": item["channel"],
                "to": item["to"],
                "message": message,
                "messageId": message_id,
                "creationDateTime": creation_time,
                "retry_count": 0
            }
            safe_payload = convert_objectid_to_str(task_payload)
            send_notification_task.apply_async(args=[safe_payload], queue="send_notification")

        return Response({"messageId": message_id}, status=202)



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
            doc_dict = {}
            for key, value in doc.items():
                if isinstance(value, ObjectId):
                    doc_dict[key] = str(value)
                else:
                    doc_dict[key] = value
            output.append(doc_dict)

        return Response(output, status=200)
