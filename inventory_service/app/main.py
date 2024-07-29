from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from typing import Annotated, AsyncGenerator
from sqlmodel import Session, SQLModel

from app import settings
from app.db_engine import engine
from app.deps import get_session
from app.models.inventory_model import InventoryItem
from app.crud.inventory_crud import add_inventory_item, get_all_inventory_items, get_inventory_item_by_id, delete_inventory_item_by_id

def create_db_and_tables() -> None:
    print(f"In create_db function...   engine is {engine}")
    SQLModel.metadata.create_all(engine)
    print("Completed create_db function...")
    


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    print("Inventory Service Starting...")
    create_db_and_tables()
    print("DB done Successfully!")
    yield
    print("Inventory Service Closing...")


app = FastAPI(
    lifespan=lifespan,
    title="Inventory Service",
    version="0.0.1",
)



@app.get('/')
def start():
    return {"message": "Inventory Service"}

@app.post('/inventory', response_model=InventoryItem)
def call_add_inventory_item( 
    inventory_item: InventoryItem, 
    session: Annotated[Session, Depends(get_session)]):
    new_inventory_item = add_inventory_item(inventory_item, session)
    return new_inventory_item



@app.get('/inventory/all', response_model=list[InventoryItem])
def call_get_all_inventory_items(session: Annotated[Session, Depends(get_session)]):
    return  get_all_inventory_items(session)


@app.get('/inventory/{item_id}', response_model=InventoryItem)
def call_get_inventory_item_by_id(item_id: int, 
                             session: Annotated[Session, Depends(get_session)]):
    try:
        return  get_inventory_item_by_id(inventory_item_id=item_id, session=session)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    


@app.delete('/inventory/{item_id}', response_model=dict)
def call_delete_inventory_item_by_id(item_id: int, 
                             session: Annotated[Session, Depends(get_session)]):
    try:
        return  delete_inventory_item_by_id(inventory_item_id=item_id, session=session)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

# @app.patch('/inventory/{id}', response_model=InventoryItem)
# def call_update_product(id: int,
#                               product: InventoryItemUpdate,
#                              session: Annotated[Session, Depends(get_session)]):
#     try:
#         return  update_product(id=id, to_update_product_data=product, session=session)
#     except HTTPException as e:
#         raise e
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
      