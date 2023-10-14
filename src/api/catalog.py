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
        SELECT potion_type, name, recipe, price, inventory FROM potions
        """
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(sql_to_execute))
        # Can return a max of 20 items.

        return_list = []
        for row in result:
            if row.inventory > 0:
                return_list.append({
                    "sku": row.potion_type,
                    "name": row.name,
                    "quantity": row.inventory,
                    "price": row.price,
                    "potion_type": row.recipe
                })
    
    return_list = sorted(return_list, key = lambda inventory : inventory["quantity"], reverse = True)
    

    return return_list[:6]
