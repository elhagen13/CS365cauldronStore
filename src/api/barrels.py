from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

class Barrel(BaseModel):
    sku: str

    ml_per_barrel: int
    potion_type: list[int]
    price: int

    quantity: int


@router.post("/deliver")
def post_deliver_barrels(barrels_delivered: list[Barrel]):
    #once delivered, subtract the total dollar amount from coins
    print(barrels_delivered)

    total_expenses = 0
    total_ml = 0

    for barrel in barrels_delivered:
        total_expenses += (barrel.price * barrel.quantity)  
        total_ml += (barrel.ml_per_barrel * barrel.quantity)

    with db.engine.begin() as connection:
        sql_to_execute = f""" 
        UPDATE global_inventory 
        SET gold = gold - {total_expenses},
            num_red_ml = num_red_ml + {total_ml}
         """

        connection.execute(sqlalchemy.text(sql_to_execute))

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    #check to see if number of red potions is less than 10, if so, 
    #buy one
    print(wholesale_catalog)
    
    with db.engine.begin() as connection:
        sql_to_execute = """ 
        SELECT gold, num_red_potions FROM global_inventory
        """

        result = connection.execute(sqlalchemy.text(sql_to_execute))
    first_row = result.first()
    #if your inventory is less than 10 buy a barrel
    if(first_row.num_red_potions < 10) and first_row.gold > wholesale_catalog[0].price:
        quantity = first_row.gold // wholesale_catalog[0].price
        if(quantity > wholesale_catalog[0].quantity):
            quantity = wholesale_catalog[0].quantity
        return [
            {
                "sku": "SMALL_RED_BARREL",
                "quantity": quantity,
            }
        ]
    return []
