import logging
from aiokafka import AIOKafkaProducer
from app.protobuf.payment_proto import payment_pb2
from app import settings

logger = logging.getLogger(__name__)

async def produce_message_to_order(payment):
    logger.info(f"Producing payment response message for order: {payment.order_id}")
    producer = AIOKafkaProducer(bootstrap_servers=settings.BOOTSTRAP_SERVER)
    await producer.start()

    try:
        response = payment_pb2.Payment(
            id=payment.id,
            order_id=payment.order_id,
            amount=payment.amount,
            status=payment.status,
        )
        serialized_response = response.SerializeToString()

        logger.info(f"Producing payment response message for order serialized response: {serialized_response}")
        await producer.send_and_wait(
            topic=settings.KAFKA_PAYMENT_RESPONSE_TOPIC, 
            value=serialized_response, 
            key=payment.status.encode('utf-8'),
        )
        logger.info(f"Payment response message produced for order: {payment.order_id}")
    except Exception as e:
        logger.error(f"Failed to produce payment response message: {str(e)}")
        raise RuntimeError(f"Failed to produce payment response message: {str(e)}")
    finally:
        await producer.stop()
