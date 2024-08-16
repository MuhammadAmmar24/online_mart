from sqlmodel import Session, select, asc
from app.models.payment_model import Payment
from datetime import datetime
from fastapi import HTTPException

def create_payment(payment: Payment, session: Session):
    session.add(payment)
    session.commit()
    session.refresh(payment)
    return payment


def get_all_payments(session: Session):
    all_payments = session.exec(select(Payment).order_by(asc(Payment.id))).all()
    if not all_payments:
        raise HTTPException(status_code=404, detail="No Payment Record Found")
    return all_payments

def get_payment_by_id(payment_id: int, session: Session ):
    payment =  session.exec(select(Payment).where(Payment.id == payment_id)).one_or_none()
    if payment is None:
        raise HTTPException(status_code=404, detail=f"No Payment Record found with the id: {payment_id}")
    return payment

def get_payment_by_order_id(order_id: int, session: Session):
    payment = session.query(Payment).filter(Payment.order_id == order_id).first()
    if payment is None:
        raise HTTPException(status_code=404, detail=f"No Payment Record found with the order id: {order_id}")
    return payment


def update_payment(payment_id: int, payment_data: Payment, session: Session):
    payment = get_payment_by_id(payment_id, session)  # Retrieve existing payment from the database
    
    # Update only the fields that are present in payment_data, excluding the 'id' field
    hero_data = payment_data.model_dump(exclude_unset=True, exclude={"id"})
    
    for key, value in hero_data.items():
        setattr(payment, key, value)
    
    session.add(payment)
    session.commit()
    session.refresh(payment)
    return payment



def delete_payment(session: Session, payment_id: int):
    payment = get_payment_by_id(session, payment_id)
    if payment:
        session.delete(payment)
        session.commit()
    return payment
