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
        SELECT potions.potion_type, potions.name, potions.recipe, 
        potions.price, inventory.total 
        FROM potions
        JOIN(
            SELECT potion_type, SUM(change) AS total
            FROM ledger WHERE potion_type IS NOT NULL
            GROUP BY potion_type
        ) AS inventory ON potions.potion_type = inventory.potion_type
        """
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(sql_to_execute))
        # Can return a max of 20 items.

        return_list = []
        for row in result:
            if row.total > 0:
                return_list.append({
                    "sku": row.potion_type,
                    "name": row.name,
                    "quantity": row.total,
                    "price": row.price,
                    "potion_type": row.recipe
                })
    
    return_list = sorted(return_list, key = lambda inventory : (inventory["price"], -inventory["quantity"]))
    

    return return_list[:6]
