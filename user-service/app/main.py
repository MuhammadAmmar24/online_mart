import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import Session, SQLModel
from typing import Annotated, AsyncGenerator
from aiokafka import AIOKafkaProducer
import asyncio

from app import settings
from app.db_engine import engine
from app.deps import get_session, kafka_producer
from app.models.user_model import UserModel, UserUpdate, TokenData
from app.crud.user_crud import get_all_users, get_user_by_id, validate_email, validate_id
from app.auth import create_jwt_token, get_secret_from_kong


from app.kafka.producers.user_producer import produce_message
from app.kafka.consumers.user_consumer import consume_users
from app.kafka.consumers.user_request_consumer import consume_user_request


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)
    logger.info("Database tables created successfully")


@asynccontextmanager
async def lifespan(app: FastAPI)-> AsyncGenerator[None, None]:
    logger.info("User Service Starting...")
    create_db_and_tables()
    task = asyncio.create_task(consume_users(
        settings.KAFKA_USER_TOPIC, 
        settings.BOOTSTRAP_SERVER, 
        settings.KAFKA_CONSUMER_GROUP_ID_FOR_USER
        ))
    asyncio.create_task(consume_user_request(
        settings.KAFKA_USER_REQUEST_TOPIC, 
        settings.BOOTSTRAP_SERVER, 
        settings.KAFKA_CONSUMER_GROUP_ID_FOR_USER_REQUEST
        ))

    yield
    logger.info("User Service Closing...")



app = FastAPI(
    lifespan=lifespan,
    title="User Service",
    version="0.0.1",
)



@app.get('/')
def start():
    return {"message": "User Service"}



@app.post("/generate-token/")
async def generate_token(data: TokenData, consumer_id: str):
    secret = get_secret_from_kong(consumer_id)
    payload = {"iss": data.iss}
    token = create_jwt_token(payload, secret)
    return {"token": token}


@app.post('/user', response_model=UserModel)
async def call_add_user(
    user: UserModel, 
    session: Annotated[Session, Depends(get_session)], 
    producer: Annotated[AIOKafkaProducer, Depends(kafka_producer)]):

    existing_user_id = validate_id(user.user_id, session)

    if existing_user_id:
        raise HTTPException(status_code=400, detail=f"User with ID {user.user_id} already exists")
    
    existing_user_email = validate_email(user.user_id, user.email, session)


    if existing_user_email:
        raise HTTPException(status_code=400, detail=f"User with ID Email {user.email} already exists")
    

    # user.password = hash_password(user.password)

    logger.info(f"Producing message for user")
    await produce_message(user, producer, "create")

    return user



@app.get('/user/all', response_model=list[UserModel])
def call_get_all_users(session: Annotated[Session, Depends(get_session)]):
    return get_all_users(session)



@app.get('/user/{id}', response_model=UserModel)
def call_get_user_by_id(id: int, session: Annotated[Session, Depends(get_session)]):
    return get_user_by_id(id=id, session=session)



@app.patch('/user/{id}', response_model=UserModel)
async def call_update_user(id: int, user: UserUpdate, session: Annotated[Session, Depends(get_session)],producer: Annotated[AIOKafkaProducer, Depends(kafka_producer)]):

    logger.info(f"User id {id} User Update: {user}")

    existing_user = call_get_user_by_id(id, session)

    logger.info(f"Existing User: {existing_user}")

        # Only update the fields that are not None (i.e., provided in the request)
    if user.email != "string":
        logger.info(f"User Email is not none : {user.email}")
        existing_user.email = user.email
    if user.password != "string":
        existing_user.password = user.password
    if user.full_name != "string":
        existing_user.full_name = user.full_name
    if user.address != "string":
        logger.info(f"User Address is not none : {user.address}")
        existing_user.address = user.address

    logger.info(f"Updated User: {existing_user}")
    await produce_message(existing_user, producer, "update")
     
    return existing_user



@app.delete('/user/{id}', response_model=dict)
async def call_delete_user_by_id(id: int, session: Annotated[Session, Depends(get_session)],producer: Annotated[AIOKafkaProducer, Depends(kafka_producer)]):

    
    user = call_get_user_by_id(id, session)
    await produce_message(user, producer, "delete")

    return {"deleted_id": id}
