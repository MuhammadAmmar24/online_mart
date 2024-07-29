from aiokafka import AIOKafkaConsumer
import json
from app.models.product_model import Product, ProductUpdate
from app.crud.product_crud import add_product
from app.deps import get_session
from app.protobuf import product_pb2

async def consume_products(topic, bootstrap_servers, group_id):

    consumer = AIOKafkaConsumer(
        topic, 
        bootstrap_servers=bootstrap_servers,
        group_id=group_id,
        auto_offset_reset='earliest'
    )

    await consumer.start()

    try:
        async for msg in consumer:
            print(f"Received message on topic: {msg.topic}")
            print(f"Consumed Message Value: {msg.value}")
            

            product = product_pb2.Product()
            new_product = product.ParseFromString(msg.value)
            print(f"\n\n Consumed Product: {new_product}")

    finally:
        await consumer.stop()
