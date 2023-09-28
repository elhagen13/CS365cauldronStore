from fastapi import APIRouter
import sqlalchemy
from src import database as db

router = APIRouter()

@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    with db.engine.begin() as connection:
        sql_to_execute = """ 
            SELECT num_red_potions FROM global_inventory
            """

        result = connection.execute(sqlalchemy.txt(sql_to_execute))
        first_row = result.first()

        # Can return a max of 20 items.

        return [
                {
                    "sku": "RED_POTION_0",
                    "name": "red potion",
                    "quantity": first_row.num_red_potions,
                    "price": 50,
                    "potion_type": [100, 0, 0, 0],
                }
            ]
