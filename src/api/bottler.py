from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db


router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)

class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int

@router.post("/deliver")
def post_deliver_bottles(potions_delivered: list[PotionInventory]):
    #the result of going barrel to bottle
    #update, +bottles, -ml
    sql_to_execute = """ 
        UPDATE global_inventory 
        SET num_red_potions = num_red_potions + :quant
        """ 
    parameters = {'quant' : potions_delivered[0].quantity}

    print(potions_delivered)

    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(sql_to_execute, **parameters))

    return "OK"

# Gets called 4 times a day
@router.post("/plan")
def get_bottle_plan():
    sql_to_execute = """
        SELECT num_red_ml FROM global_inventory
    """
    remove_ml = """
        UPDATE global_inventory
        SET num_red_ml = num_red_ml - (100 * :quant)
    """
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.txt(sql_to_execute))
        first_row = result.first()

        #how many red potions can be made
        quant = first_row.num_red_ml // 100
        parameters = {'quant' : quant}
        connection.execute(sqlalchemy.txt(remove_ml), **parameters)


    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    # Initial logic: bottle all barrels into red potions.

    return [
            {
                "potion_type": [100, 0, 0, 0],
                "quantity": quant,
            }
        ]
