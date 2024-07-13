from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from typing import Annotated, AsyncGenerator
from sqlmodel import Session, SQLModel
from app import settings
from app.db_engine import engine
from app.deps import get_session
from app.models.order_model import Order, OrderUpdate
from app.crud.order_crud import add_order, get_all_orders, get_order_by_id, delete_order_by_id, update_order

def create_db_and_tables() -> None:
    print(f"In create_db function...   engine is {engine}")
    SQLModel.metadata.create_all(engine)
    print("Completed create_db function...")

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    print("Order Service Starting...")
    create_db_and_tables()
    print("DB done Successfully!")
    yield
    print("Order Service Closing...")

app = FastAPI(
    lifespan=lifespan,
    title="Order Service",
    version="0.0.1",
)

@app.get('/')
def start():
    return {"message": "Order Service"}

@app.post('/order', response_model=Order, status_code=201)
def call_add_order(order: Order, session: Annotated[Session, Depends(get_session)]):
    try:
        new_order = add_order(order, session)
        return new_order
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/order/all', response_model=list[Order])
def call_get_all_order(session: Annotated[Session, Depends(get_session)]):
    try:
        return get_all_orders(session)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/order/{order_id}', response_model=Order)
def call_get_order_by_id(order_id: int, session: Annotated[Session, Depends(get_session)]):
    try:
        return get_order_by_id(order_id=order_id, session=session)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete('/order/{order_id}', response_model=dict)
def call_delete_order_by_id(order_id: int, session: Annotated[Session, Depends(get_session)]):
    try:
        return delete_order_by_id(order_id=order_id, session=session)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.patch('/order/{order_id}', response_model=Order)
def call_update_order(order_id: int, order: OrderUpdate, session: Annotated[Session, Depends(get_session)]):
    try:
        return update_order(order_id=order_id, to_update_order_data=order, session=session)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
