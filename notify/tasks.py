from celery import shared_task
import time
from pymongo import MongoClient
from celery import Celery

mongo_client = MongoClient("mongodb://localhost:27017", maxPoolSize=50)
db = mongo_client["zibal_db"]
notification_collection = db["notification"]


@shared_task(
    name="send_notification_task",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    rate_limit="100/m"
)
def send_notification_task(self, payload):
    print('--------------------------------------------------------------------------------------')
    retry_count = payload.get("retry_count", 0)
    message_id = payload.get("messageId")
    channel = payload.get("channel")

    if retry_count > 3:
        update_status(payload["messageId"], "failed")
        print(f"[FAILED] Max retries exceeded for {message_id}")
        return

    try:
        if retry_count > 3:
            update_status(payload["messageId"], "failed")
            print(f"[FAILED] Max retries exceeded for {message_id}")
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
    print(f"SMS to {payload['to']} successfully sent.")
    update_status(payload["messageId"], "success")


def handle_email(payload):
    time.sleep(10)
    print(f"Email to {payload['to']} failed.")
    payload["retry_count"] += 1
    send_notification_task.apply_async(args=[payload], queue="send_notification")


def handle_push(payload):
    time.sleep(10)
    print(f"pushNotification to {payload['to']} successfully sent.")
    update_status(payload["messageId"], "success")


def update_status(message_id, new_status):
    notification_collection.update_one({"messageId": message_id}, {"$set": {"status": new_status}})
