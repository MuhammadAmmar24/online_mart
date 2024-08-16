from sqlmodel import Session, select, asc
from fastapi import HTTPException
from app.models.notification_model import Notification

def add_notification(notification: Notification, session: Session):
    try:
        session.add(notification)
        session.commit()
        session.refresh(notification)
        return notification
    except Exception as e:  
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    

def get_all_notifications(session: Session):
    all_notifications = session.exec(select(Notification).order_by(asc(Notification.id)))
    if all_notifications is None:
        raise HTTPException(status_code=404, detail="No Notification Found")    
    return all_notifications

def get_notification_by_id(notification_id: int, session: Session):
    notification = session.exec(select(Notification).where(Notification.id == notification_id)).one_or_none()
    if notification is None:
        raise HTTPException(status_code=404, detail=f"No Notification found with the id : {notification_id}")
    return notification

def update_notification_status(notification_id: int, status: str, session: Session):
    
    notification = get_notification_by_id(notification_id, session)
    if notification:
        notification.status = status
        session.commit()
        session.refresh(notification)
    return notification
