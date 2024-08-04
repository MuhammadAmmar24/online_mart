from aiokafka import AIOKafkaProducer
from app import settings

async def kafka_producer():

    producer = AIOKafkaProducer(bootstrap_servers=settings.BOOTSTRAP_SERVER)
    await producer.start()

    try:
        yield producer
    
    finally:
        await producer.stop()

