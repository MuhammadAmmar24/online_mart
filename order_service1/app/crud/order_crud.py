from fastapi import HTTPException
from sqlmodel import Session, select, asc

from app.models.order_model import Order, OrderUpdate


# Create a new order
def add_order(order_data: Order, session: Session) -> Order:
    try:
        session.add(order_data)
        session.commit()
        session.refresh(order_data)
        return order_data
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    
 
# Get all orders
def get_all_orders(session: Session) -> list[Order]:
    try:
        all_orders = session.exec(select(Order).order_by(asc(Order.order_id))).all()
        if not all_orders:
            raise HTTPException(status_code=404, detail="No Order Found")
        return all_orders
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# Get order by id
def get_order_by_id(order_id: int, session: Session) -> Order:
    try:
        order = session.exec(select(Order).where(Order.order_id == order_id)).one_or_none()
        if order is None:
            raise HTTPException(status_code=404, detail=f"No Order found with the id: {order_id}")
        return order
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    

# Delete order by id
def delete_order_by_id(order_id: int, session: Session) -> dict:
    try:
        order = get_order_by_id(order_id, session)
        session.delete(order)
        session.commit()
        return {"message": "Order Deleted Successfully"}
    except HTTPException as e:
        raise e
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# Update Order by id
def update_order(order_id: int, to_update_order_data: OrderUpdate, session: Session) -> Order:

    # 1. Get the order 
    order = get_order_by_id(order_id,session)
    
    # 2. Upload the order
    hero_data = to_update_order_data.model_dump(exclude_unset=True)
    order.sqlmodel_update(hero_data)
    session.add(order)
    session.commit()
    session.refresh(order)
    return order

