import os
import boto3
from dotenv import load_dotenv

load_dotenv()

SNS_TOPIC_ARN = os.getenv("SNS_TOPIC_ARN")


def notify_failure(message: str):
    print(f"[ALERT] {message}")
    print(f"[DEBUG] SNS_TOPIC_ARN = {SNS_TOPIC_ARN}")

    if not SNS_TOPIC_ARN:
        return

    try:
        sns = boto3.client("sns")
        response = sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=message,
            Subject="Opinion scraper failure",
        )
        print(f"[DEBUG] SNS publish response: {response}")
    except Exception as e:
        print(f"[ALERT] Failed to publish SNS message: {e}")
