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

KAFKA_NOTIFICATION_TOPIC = config("KAFKA_NOTIFICATION_TOPIC", cast=str)
KAFKA_USER_REQUEST_TOPIC = config("KAFKA_USER_REQUEST_TOPIC", cast=str)

KAFKA_CONSUMER_GROUP_ID_FOR_NOTIFICATION = config("KAFKA_CONSUMER_GROUP_ID_FOR_NOTIFICATION", cast=str)


# SMTP CONFIG
SMTP_SERVER = config("SMTP_SERVER", cast=str)
SMTP_PORT = config("SMTP_PORT", cast=int)
SMTP_USERNAME = config("SMTP_USERNAME", cast=str)
SMTP_PASSWORD = config("SMTP_PASSWORD", cast=str)