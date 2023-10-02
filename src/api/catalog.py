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
        SELECT num_red_potions FROM global_inventory
        """
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(sql_to_execute))
    first_row = result.first()
    # Can return a max of 20 items.
    if(first_row.num_red_potions == 0):
        return []
    return [
            {
                "sku": "red_potion",
                "name": "red potion",
                "quantity": first_row.num_red_potions,
                "price": 50,
                "potion_type": [100, 0, 0, 0],
            }
        ]