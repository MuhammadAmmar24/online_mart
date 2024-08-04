from fastapi import HTTPException
from sqlmodel import Session, select, asc

from app.models.inventory_model import InventoryItem


# Add a new Inventory to the database
def add_inventory_item(inventory_item_data: InventoryItem, session: Session) -> InventoryItem:
    print("Adding inventory to the Database")
    session.add(inventory_item_data)
    session.commit()
    session.refresh(inventory_item_data)
    return inventory_item_data
    

# Get all Inventory from the database
def get_all_inventory_items(session: Session) -> list[InventoryItem]:
    all_InventoryItems = session.exec(select(InventoryItem).order_by(asc(InventoryItem.id)))
    if all_InventoryItems is None:
        raise HTTPException(status_code=404, detail="No Inventory Item Found")
    return all_InventoryItems


# Get an Inventory by ID 
def get_inventory_item_by_id(inventory_item_id: int, session: Session) -> InventoryItem:
    inventory_item = session.exec(select(InventoryItem).where(InventoryItem.id == inventory_item_id)).one_or_none()
    if InventoryItem is None:
        raise HTTPException(status_code=404, detail=f"No Inventory item found with the id : {inventory_item_id}")
    return inventory_item
    

# Delete Inventory by ID
def delete_inventory_item_by_id(inventory_item_id: int, session: Session) -> dict:

    # 1. Get the InventoryItem 
    inventory_item = get_inventory_item_by_id(inventory_item_id,session)
    
    # 2. Delete the InventoryItem
    session.delete(inventory_item)
    session.commit()
    return {"message": "Inventory Item Deleted Successfully"}


# # Update InventoryItem by id
# def update_InventoryItem(InventoryItem_id: int, to_update_InventoryItem_data: InventoryItemUpdate, session: Session) -> InventoryItem:

#     # 1. Get the InventoryItem 
#     InventoryItem = get_InventoryItem_by_id(InventoryItem_id,session)
    
#     # 2. Upload the InventoryItem
#     hero_data = to_update_InventoryItem_data.model_dump(exclude_unset=True)
#     InventoryItem.sqlmodel_update(hero_data)
#     session.add(InventoryItem)
#     session.commit()
#     session.refresh(InventoryItem)
#     return InventoryItem


