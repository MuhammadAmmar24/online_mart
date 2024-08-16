from fastapi import HTTPException
from sqlmodel import Session, select, asc
from datetime import datetime

from app.models.order_model import OrderModel,  OrderUpdate


# Add a new Order
def add_order(order_data: OrderModel, session: Session) -> OrderModel:
    try:
        session.add(order_data)
        session.commit()
        session.refresh(order_data)
        return order_data
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# Get all Orders
def get_all_orders(session: Session) -> list[OrderModel]:
    all_orders = session.exec(select(OrderModel).order_by(asc(OrderModel.id))).all()
    if all_orders is None:
        raise HTTPException(status_code=404, detail="No Order Found")
    return all_orders


# Get Order by id
def get_order_by_id(id: int, session: Session) -> OrderModel:
    order = session.exec(select(OrderModel).where(OrderModel.id == id)).one_or_none()
    if order is None:
        return None
    return order


# Delete Order by id
def delete_order_by_id(id: int, session: Session) -> dict:
    # 1. Get the Order
    order = get_order_by_id(id, session)

    # 2. Delete the Order
    session.delete(order)
    session.commit()

    return {"message": "Order Deleted Successfully"}


# Update Order by id
def update_order(id: int, to_update_order_data: OrderUpdate, session: Session) -> OrderModel:
    # 1. Get the Order
    order = get_order_by_id(id, session)

    # 2. Update the Order
    order_data = to_update_order_data.dict(exclude_unset=True)
    for key, value in order_data.items():
        setattr(order, key, value)
    # order.updated_at = datetime.utcnow()
    session.add(order)
    session.commit()
    session.refresh(order)
    return order


# Check if order exists or not
def validate_order_id(id: int, session: Session) -> OrderModel | None:
    order = session.exec(select(OrderModel).where(OrderModel.id == id)).one_or_none()
    if not order:
        return None
    return order
 

# Update Order Status
def update_order_status(id: int, status: str, session: Session) -> OrderModel:
    order = get_order_by_id(id, session)
    order.status = status
    session.add(order)
    session.commit()
    session.refresh(order)
    return order

# Add a new OrderItem
def add_order_item(order_item_data, session: Session) :
    try:
        session.add(order_item_data)
        session.commit()
        session.refresh(order_item_data)
        return order_item_data
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
