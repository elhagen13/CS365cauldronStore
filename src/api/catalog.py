from fastapi import APIRouter
import sqlalchemy
from src import database as db

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """
    with db.engine.begin() as connection:
        sql_to_execute = """
            SELECT num_red_potions FROM global_inventory
        """
        result = connection.execute(sqlalchemy.txt(sql_to_execute))
        first_row = result.first()
        quant = first_row.num_red_potions

    # Can return a max of 20 items.
    return [
            {
                "sku": "RED_POTION_0",
                "name": "red potion",
                "quantity": quant,
                "price": 50,
                "potion_type": [100, 0, 0, 0],
            }
        ]