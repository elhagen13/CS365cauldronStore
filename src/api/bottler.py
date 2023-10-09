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
    print(potions_delivered)
    red_quant = 0
    green_quant = 0
    blue_quant = 0

    for potion in potions_delivered:
        print(potion)
        if potion.potion_type == [100, 0, 0, 0]:
            red_quant = potion.quantity
        elif potion.potion_type == [0, 100, 0, 0]:
            green_quant = potion.quantity
        elif potion.potion_type == [0, 0, 100, 0]:
            blue_quant = potion.quantity

    print(red_quant , ' ' ,  green_quant , ' ' , blue_quant)

    sql_to_execute = f""" 
        UPDATE global_inventory 
        SET num_red_potions = num_red_potions + {red_quant},
            num_red_ml = num_red_ml - (100 * {red_quant}),
            num_green_potions = num_green_potions + {green_quant},
            num_green_ml = num_green_ml - (100 * {green_quant}),
            num_blue_potions = num_blue_potions + {blue_quant},
            num_blue_ml = num_blue_ml - (100 * {blue_quant})
        """ 

    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(sql_to_execute))

    return "OK"

# Gets called 4 times a day
@router.post("/plan")
def get_bottle_plan():
    sql_to_execute = """
        SELECT num_red_potions, num_green_potions, num_blue_potions, num_red_ml, num_green_ml, num_blue_ml FROM global_inventory
    """
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(sql_to_execute))
    first_row = result.first()
    #how many red potions can be made
    quant_red = first_row.num_red_ml // 100
    quant_green = first_row.num_green_ml // 100
    quant_blue = first_row.num_blue_ml // 100

    if quant_red + first_row.num_red_ml > 100:
        quant_red = 100 - first_row.num_red_ml
    if quant_green + first_row.num_green_ml > 100:
        quant_green = 100 - first_row.num_green_ml
    if quant_blue + first_row.num_blue_ml > 100:
        quant_blue = 100 - first_row.num_blue_ml
        
    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    # Initial logic: bottle all barrels into red potions.
    return_list = []
    if quant_red != 0:
        return_list.append({
            "potion_type": [100, 0, 0, 0],
            "quantity": quant_red,
        })
    if quant_green != 0:
        return_list.append({
            "potion_type": [0, 100, 0, 0],
            "quantity": quant_green,
        })
    if quant_blue != 0:
        return_list.append({
            "potion_type": [0, 0, 100, 0],
            "quantity": quant_blue,
        })
    return return_list
    
    
 