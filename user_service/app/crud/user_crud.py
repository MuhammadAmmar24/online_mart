from fastapi import HTTPException
from sqlmodel import Session, select, asc

from app.models.user_model import UserModel, UserUpdate

# Add a new User
def add_user(user_data, session: Session) -> UserModel:
    try:
        session.add(user_data)
        session.commit()
        session.refresh(user_data)
        return user_data
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    
# Get all Users
def get_all_users(session: Session) -> list[UserModel]:
    all_users = session.exec(select(UserModel).order_by(asc(UserModel.user_id)))
    if all_users is None:
        raise HTTPException(status_code=404, detail="No User Found")
    return all_users

# Get User by id
def get_user_by_id(id: int, session: Session) -> UserModel:
    user = session.exec(select(UserModel).where(UserModel.user_id == id)).one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail=f"No User found with the id : {id}")
    return user

# Update User by id
def update_user(id: int, to_update_user_data: UserUpdate, session: Session) -> UserModel:

    # 1. Get the User 
    user = get_user_by_id(id,session)
    
    # 2. Upload the User
    hero_data = to_update_user_data.model_dump(exclude_unset=True)
    user.sqlmodel_update(hero_data)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


# Delete User by id
def delete_user_by_id(id: int, session: Session) -> dict:
    user = get_user_by_id(id, session)
    session.delete(user)
    session.commit()
    return {"message": "User Deleted Successfully"}

# Check if user exists or not
def validate_id(id: int, session: Session) -> UserModel | None:
    user = session.exec(select(UserModel).where(UserModel.user_id == id)).one_or_none()
    if not user:
        return None  
    return user
