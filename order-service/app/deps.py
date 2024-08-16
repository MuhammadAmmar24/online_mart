from sqlmodel import Session
from aiokafka import AIOKafkaProducer
from app.db_engine import engine
from app import settings




def get_session():
    with Session(engine) as session:
        yield session


async def kafka_producer():

    producer = AIOKafkaProducer(bootstrap_servers=settings.BOOTSTRAP_SERVER)
    await producer.start()

    try:
        yield producer
    
    finally:
        await producer.stop()
