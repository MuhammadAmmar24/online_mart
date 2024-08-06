from fastapi import HTTPException
from sqlmodel import Session, select, asc

from app.models.inventory_model import InventoryItem, InventoryItemUpdate


# Add a new Inventory Item
def add_inventory_item(inventory_item_data: InventoryItem, session: Session) -> InventoryItem:
    try:
        session.add(inventory_item_data)
        session.commit()
        session.refresh(inventory_item_data)
        return inventory_item_data
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    

# Get all Inventory Items
def get_all_inventory_items(session: Session) -> list[InventoryItem]:
    all_inventory_items = session.exec(select(InventoryItem).order_by(asc(InventoryItem.id))).all()
    if not all_inventory_items:
        raise HTTPException(status_code=404, detail="No Inventory Item Found")
    return all_inventory_items


# Get Inventory Item by id
def get_inventory_item_by_id(id: int, session: Session) -> InventoryItem:
    inventoryItem = session.exec(select(InventoryItem).where(InventoryItem.id == id)).one_or_none()
    if inventoryItem is None:
        raise HTTPException(status_code=404, detail=f"No Inventory Item found with the id: {id}")
    return inventoryItem


# Get Inventory Item by product_id
def get_inventory_item_by_product_id(product_id: int, session: Session) -> InventoryItem | None:
    inventory_item = session.exec(select(InventoryItem).where(InventoryItem.product_id == product_id)).one_or_none()
    return inventory_item


# Update Inventory Item by id
def update_inventory_item(id: int, to_update_inventory_data: InventoryItemUpdate, session: Session) -> InventoryItem:

     # 1. Get the inventoryItem 
    inventoryItem = get_inventory_item_by_id(id,session)
    
    # 2. Upload the Invetory Item   
    hero_data = to_update_inventory_data.model_dump(exclude_unset=True)
    inventoryItem.sqlmodel_update(hero_data)
    session.add(inventoryItem)
    session.commit()
    session.refresh(inventoryItem)
    return inventoryItem


# Delete Inventory Item by id
def delete_inventory_item_by_id(id: int, session: Session) -> dict:
     # 1. Get the inventoryItem 
    inventoryItem = get_inventory_item_by_id(id,session)

    # 2. Delete the inventoryItem
    session.delete(inventoryItem)
    session.commit()

    return {"message": "Inventory Item Deleted Successfully"}




# Check if inventory item exists or not
def validate_id(id: int, session: Session) -> InventoryItem | None:
    inventory = session.exec(select(InventoryItem).where(InventoryItem.id == id)).one_or_none()
    return inventory
