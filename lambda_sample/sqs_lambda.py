import json
import logging
import utils.log_util as log
import time
import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

SQS_CLIENT = boto3.client('sqs', region_name='ap-northeast-1')
DLQ_URL = 'https://sqs.ap-northeast-1.amazonaws.com/637423206596/test-sqs-dlq'

def send_to_dlq(record, reason):
    body = record.get('body')
    message_id = record.get('messageId')
    SQS_CLIENT.send_message(
        QueueUrl=DLQ_URL,
        MessageBody=body,
        MessageAttributes={
            'originalMessageId': {'DataType': 'String', 'StringValue': message_id},
            'failureReason':     {'DataType': 'String', 'StringValue': reason},
        }
    )
    logger.info(f"[DLQ] Sent messageId={message_id} to DLQ, reason={reason}")

def lambda_handler(event, context):
    records = event.get('Records', [])
    logger.info(f"Received {len(records)} message(s) from SQS")

    log.info(event)

    for record in records:
        message_id   = record.get('messageId')
        receipt      = record.get('receiptHandle')
        body         = record.get('body')
        source_arn   = record.get('eventSourceARN')
        sent_time    = record.get('attributes', {}).get('SentTimestamp')
        receive_count = record.get('attributes', {}).get('ApproximateReceiveCount')

        logger.info(
            f"[SQS Message] "
            f"messageId={message_id} | "
            f"queue={source_arn} | "
            f"sentTimestamp={sent_time} | "
            f"receiveCount={receive_count} | "
            f"body☆☆={body} | "
            f"receiptHandle={receipt}"
        )
        log.info({"内容:": body})

        # try:
        #     time.sleep(100)
        #     raise Exception("测试终止，查看sqs是否清除")
        # except Exception as e:
        #     send_to_dlq(record, str(e))
        #     # 手动删除原队列消息，避免重试
        #     SQS_CLIENT.delete_message(
        #         QueueUrl='https://sqs.ap-northeast-1.amazonaws.com/637423206596/test-sqs',
        #         ReceiptHandle=receipt
        #     )
        #     logger.info(f"[Deleted] messageId={message_id} removed from source queue")

    # Keep running for 10 minutes, logging elapsed time every 5 seconds
    start_time = time.time()
    duration = 1 * 60  # 10 minutes

    while True:
        elapsed = time.time() - start_time
        if elapsed >= duration:
            break
        logger.info(f"[Running] elapsed={elapsed:.1f}s / {duration}s")
        time.sleep(5)

    return {
        'statusCode': 200,
        'body': json.dumps(f"Processed {len(records)} message(s).")
    }
