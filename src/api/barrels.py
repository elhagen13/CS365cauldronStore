from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

barrels_to_be_delivered = 0

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
    total_red_ml = 0
    total_green_ml = 0
    total_blue_ml = 0

    for barrel in barrels_delivered:
        total_expenses += barrel.price
        if barrel.potion_type == [1, 0, 0, 0]:
            total_red_ml += barrel.ml_per_barrel
        elif barrel.potion_type == [0, 1, 0, 0]:
            total_green_ml += barrel.ml_per_barrel
        elif barrel.potion_type == [0, 0, 1, 0]:
            total_blue_ml += barrel.ml_per_barrel

    with db.engine.begin() as connection:
        sql_to_execute = f""" 
        UPDATE global_inventory 
        SET gold = gold - {total_expenses},
            num_red_ml = num_red_ml + {total_red_ml},
            num_green_ml = num_green_ml + {total_green_ml},
            num_blue_ml = num_blue_ml + {total_blue_ml}
         """

        connection.execute(sqlalchemy.text(sql_to_execute))

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    #check to see if number of red potions is less than 10, if so, 
    #buy one
    print(wholesale_catalog)
    catalog = {}
    for barrel in wholesale_catalog:
        catalog[barrel.sku] = barrel.price
    
    with db.engine.begin() as connection:
        sql_to_execute = """ 
        SELECT gold, num_red_potions, num_green_potions, num_blue_potions FROM global_inventory
        """
        result = connection.execute(sqlalchemy.text(sql_to_execute))
    first_row = result.first()

    gold = first_row.gold
    return_list = []
    priority_list = get_priority()


    for color in priority_list:
        if color == "red_potion":
            sku = get_size(gold, first_row.num_red_potions, color)
        elif color == "green_potion":
            sku = get_size(gold, first_row.num_green_potions, color)
        elif color == "blue_potion":
            sku = get_size(gold, first_row.num_blue_potions, color)
        
        gold -= catalog.get(sku, 0)
        if sku != None:
            return_list.append({
                "sku": sku,
                "quantity": 1,
            })
    return return_list

     
#what size of potion should be bought      
def get_size(gold: int, inventory: int, type_potion: str):
    if type_potion == "red_potion":
        if gold >= 500 and inventory < 100:
            return "LARGE_RED_BARREL"
        elif gold >= 250 and inventory < 25:
            return "MEDIUM_RED_BARREL"
        elif gold >= 100 and inventory < 10:
            return "SMALL_RED_BARREL"
    elif type_potion == "green_potion":
        if gold >= 400 and inventory < 100:
            return "LARGE_GREEN_BARREL"
        elif gold >= 250 and inventory < 25:
            return "MEDIUM_GREEN_BARREL"
        elif gold >= 100 and inventory < 10:
            return "SMALL_GREEN_BARREL"
    elif type_potion == "blue_potion":
        if gold >= 600 and inventory < 100:
            return "LARGE_BLUE_BARREL"
        elif gold >= 300 and inventory < 25:
            return "MEDIUM_BLUE_BARREL"
        elif gold >= 120 and inventory < 10:
            return "SMALL_BLUE_BARREL"
    return 

#decides the priority of the potions, which one should be bought first
def get_priority():
    sql_to_execute = """SELECT num_red_potions, num_green_potions, num_blue_potions FROM global_inventory"""
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(sql_to_execute))
    first_row = result.first()
    
    if(first_row.num_red_potions <= first_row.num_green_potions and first_row.num_red_potions <= first_row.num_blue_potions):
        priority1 = "red_potion"
        if(first_row.num_green_potions <= first_row.num_blue_potions):
            priority2 = "green_potion"
            priority3 = "blue_potion"
        else:
            priority2 = "blue_potion"
            priority3 = "green_potion"
    elif(first_row.num_green_potions <= first_row.num_red_potions and first_row.num_green_potions <= first_row.num_blue_potions):
        priority1 = "green_potion"
        if(first_row.num_red_potions <= first_row.num_blue_potions):
            priority2 = "red_potion"
            priority3 = "blue_potion"
        else:
            priority2 = "blue_potion"
            priority3 = "red_potion"
    else:
        priority1 = "blue_potion"
        if(first_row.num_red_potions <= first_row.num_green_potions):
            priority2 = "red_potion"
            priority3 = "green_potion"
        else:
            priority2 = "green_potion"
            priority3 = "red_potion"
       
    return [priority1, priority2, priority3]

