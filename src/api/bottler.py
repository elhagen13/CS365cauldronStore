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
    dictionary = {"red_ml" : 0, "green_ml" : 0, "blue_ml" : 0, "dark_ml" : 0}

    sql_to_execute = """ 
            INSERT INTO transactions (description) VALUES 
            ('Mixed potions') RETURNING id
            """
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(sql_to_execute))
            
        id = result.first().id


    for potion in potions_delivered:
        dictionary["red_ml"] += (potion.potion_type[0] * potion.quantity)
        dictionary["green_ml"] += (potion.potion_type[1] * potion.quantity)
        dictionary["blue_ml"] += (potion.potion_type[2] * potion.quantity)
        dictionary["dark_ml"] += (potion.potion_type[3] * potion.quantity)

        sql_to_execute = """SELECT potion_type FROM potions WHERE recipe = :recipe"""
        with db.engine.begin() as connection:
            potion_name = connection.execute(sqlalchemy.text(sql_to_execute), [{"recipe" : potion.potion_type}]).first().potion_type
        
        sql_to_execute = """ 
        INSERT INTO ledger (transaction_id, type, potion_type, change) VALUES
        (:id, 'potion', :potion_type, :total_mixed)
        """
        with db.engine.begin() as connection:
            connection.execute(sqlalchemy.text(sql_to_execute), [{"id": id, 
            "potion_type": potion_name, "total_mixed": potion.quantity}])
            

    for color in dictionary:
        if dictionary[color] > 0:
            sql_to_execute = """INSERT INTO ledger (transaction_id, type, change) VALUES
            (:id, :color, :ml)"""

            with db.engine.begin() as connection:
                connection.execute(sqlalchemy.text(sql_to_execute), 
                [{"id": id, "color": color, "ml": - 1 * dictionary[color]}])

    return "OK"

# Gets called 4 times a day
@router.post("/plan")
def get_bottle_plan():
    sql_to_execute = """SELECT 
    SUM(CASE WHEN type = 'red_ml' THEN change ELSE 0 END) AS num_red_ml, 
    SUM(CASE WHEN type = 'green_ml' THEN change ELSE 0 END) AS num_green_ml,
    SUM(CASE WHEN type = 'blue_ml' THEN change ELSE 0 END) AS num_blue_ml,
    SUM(CASE WHEN type = 'dark_ml' THEN change ELSE 0 END) AS num_dark_ml
    FROM ledger
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
    sql_to_execute = """SELECT potion_type, recipe, desired_inventory FROM potions"""
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(sql_to_execute))

        dictionary = {}
        for row in result:
            sql_to_execute = """SELECT COALESCE(SUM(change), 0) AS total FROM ledger WHERE potion_type = :potion_type"""
            total = connection.execute(sqlalchemy.text(sql_to_execute), 
                                       [{"potion_type" : row.potion_type}])
            inventory = total.first()
            dictionary[row.potion_type] = {
                'wanted': row.desired_inventory - inventory.total,
                'recipe': row.recipe
            }
    
    sorted_list = dict(sorted(dictionary.items(), key = lambda quantity : quantity[1]["wanted"], reverse = True))
    print(sorted_list)
    return sorted_list
