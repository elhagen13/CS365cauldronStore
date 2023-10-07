from fastapi import APIRouter
import sqlalchemy
from src import database as db

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """
    sql_to_execute = """ 
        SELECT num_red_potions, num_green_potions, num_blue_potions FROM global_inventory
        """
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(sql_to_execute))
    first_row = result.first()
    # Can return a max of 20 items.

    return_list = []
    if(first_row.num_red_potions != 0):
        return_list.append({
            "sku": "red_potion",
            "name": "red potion",
            "quantity": first_row.num_red_potions,
            "price": 50,
            "potion_type": [100, 0, 0, 0]
        })
    if(first_row.num_green_potions != 0):
        return_list.append({
            "sku": "green_potion",
            "name": "green potion",
            "quantity": first_row.num_green_potions,
            "price": 50,
            "potion_type": [0, 100, 0, 0]
        })
    if(first_row.num_blue_potions != 0):
        return_list.append({
            "sku": "blue_potion",
            "name": "blue potion",
            "quantity": first_row.num_blue_potions,
            "price": 50,
            "potion_type": [0, 0, 100, 0]
        })

    return return_list
