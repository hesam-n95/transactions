from celery import shared_task
import time
from pymongo import MongoClient
import logging
from django.conf import settings


logger = logging.getLogger('notify')

mongo_client = MongoClient(settings.MONGO_URI, maxPoolSize=50)
db = mongo_client[settings.MONGO_DB_NAME]
notification_collection = db["notification"]


@shared_task(
    name="send_notification_task",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    soft_time_limit=300,
    time_limit=600
)
def send_notification_task(self, payload):
    retry_count = payload.get("retry_count", 0)
    message_id = payload.get("messageId")
    channel = payload.get("channel")
    logger.info(f"Processing notification: messageId={message_id}")

    try:
        if retry_count > 3:
            update_status(message_id, "failed")
            return

        # Channel dispatch
        if channel == "sms":
            handle_sms(payload)
        elif channel == "email":
            handle_email(payload)
        elif channel == "pushNotification":
            handle_push(payload)
    except Exception as exc:
        payload["retry_count"] = retry_count + 1
        raise self.retry(exc=exc, countdown=60 * payload["retry_count"])


def handle_sms(payload):
    time.sleep(10)
    logger.info(f"SMS to {payload['to']} successfully sent.")
    update_status(payload["messageId"], "success")


def handle_email(payload):
    time.sleep(10)
    logger.info(f"Email to {payload['to']} failed.")
    payload["retry_count"] += 1
    send_notification_task.apply_async(args=[payload], queue="send_notification")


def handle_push(payload):
    time.sleep(10)
    logger.info(f"push notification to {payload['to']} successfully sent.")
    update_status(payload["messageId"], "success")


def update_status(message_id, new_status):
    notification_collection.update_one({"messageId": message_id}, {"$set": {"status": new_status}})
