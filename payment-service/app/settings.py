from starlette.config import Config
from starlette.datastructures import Secret


try:   
    config = Config(".env")
except FileNotFoundError:
    config = Config()

#DATABASE
DATABASE_URL = config("DATABASE_URL", cast=Secret)
TEST_DATABASE_URL = config("TEST_DATABASE_URL", cast=Secret)


#KAFKA
BOOTSTRAP_SERVER = config("BOOTSTRAP_SERVER", cast=str)
KAFKA_PAYMENT_REQUEST_TOPIC = config("KAFKA_PAYMENT_REQUEST_TOPIC", cast=str)
KAFKA_PAYMENT_RESPONSE_TOPIC = config("KAFKA_PAYMENT_RESPONSE_TOPIC", cast=str)

KAFKA_CONSUMER_GROUP_ID_FOR_PAYMENT_REQUEST = config("KAFKA_CONSUMER_GROUP_ID_FOR_PAYMENT_REQUEST", cast=str)