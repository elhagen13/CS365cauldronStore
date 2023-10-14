from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db
from collections import OrderedDict


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
    dark_quant = 0

    for potion in potions_delivered:
        red_quant += (potion.potion_type[0] * potion.quantity)
        green_quant += (potion.potion_type[1] * potion.quantity)
        blue_quant += (potion.potion_type[2] * potion.quantity)
        dark_quant += (potion.potion_type[3] * potion.quantity)

        sql_to_execute = """UPDATE potions 
                            SET inventory = inventory + :quantity
                            WHERE recipe = :recipe"""
        
        with db.engine.begin() as connection:
            connection.execute(sqlalchemy.text(sql_to_execute), [{"quantity": potion.quantity, "recipe": potion.potion_type}])

    sql_to_execute = """ 
        UPDATE global_inventory 
        SET num_red_ml = num_red_ml - :red_quant,
            num_green_ml = num_green_ml - :green_quant,
            num_blue_ml = num_blue_ml - :blue_quant,
            num_dark_ml = num_dark_ml - :dark_quant
        """ 

    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(sql_to_execute), [{"red_quant": red_quant, "green_quant": green_quant,
                                                             "blue_quant": blue_quant, "dark_quant": dark_quant}])

    return "OK"

# Gets called 4 times a day
@router.post("/plan")
def get_bottle_plan():
    sql_to_execute = """
        SELECT num_red_ml, num_green_ml, num_blue_ml, num_dark_ml FROM global_inventory
    """
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(sql_to_execute))
        first_row = result.first()
    #returns a dictionary of potions with their quantity
    #goal is to go down, 
    red = first_row.num_red_ml
    green = first_row.num_green_ml
    blue = first_row.num_blue_ml
    dark = first_row.num_dark_ml

    priority_list = get_priority()

    return_list = []
    
    for potion in priority_list:
        quantity = min(priority_list[potion]["wanted"], get_quant(priority_list[potion]["recipe"], red, green, blue, dark))
        #mix as many bottles as you can
        red = red - (quantity * priority_list[potion]["recipe"][0])
        green = green - (quantity * priority_list[potion]["recipe"][1])
        blue = blue - (quantity * priority_list[potion]["recipe"][2])
        dark = dark - (quantity * priority_list[potion]["recipe"][3])
        
        if quantity > 0:
            return_list.append({
            "potion_type": priority_list[potion]["recipe"],
            "quantity": quantity,
        })

    return return_list

def get_quant(recipe: list[int], red: int, green: int, blue: int, dark: int):
    #the number of potions that can be made from current inventory
    array = []
    if recipe[0] != 0:
        array.append(red // recipe[0])
    if recipe[1] != 0:
        array.append(green // recipe[1])
    if recipe[2] != 0:
        array.append(blue // recipe[2])
    if recipe[3] != 0:
        array.append(dark // recipe[3])

    quant = min(array)
    return quant
    
    
def get_priority():
    sql_to_execute = """SELECT * FROM potions"""
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(sql_to_execute))
    

    dictionary = {}
    for row in result:
        dictionary[row.potion_type] = {
            'wanted': row.desired_inventory - row.inventory,
            'recipe': row.recipe
        }
    
    sorted_list = dict(sorted(dictionary.items(), key = lambda quantity : quantity[1]["wanted"], reverse = True))
    print(sorted_list)
    return sorted_list
