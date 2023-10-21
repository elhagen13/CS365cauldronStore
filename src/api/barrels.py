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
    
    with db.engine.begin() as connection:
        sql_to_execute = """ 
        INSERT INTO transactions (description) VALUES 
        (:description) RETURNING id
        """
        result = connection.execute(sqlalchemy.text(sql_to_execute), 
        [{"description" : "Purchased barrels"}])
            
        id = result.first().id

    for barrel in barrels_delivered:
        print(barrel)
        total_expenses += (barrel.price * barrel.quantity)
        if barrel.potion_type == [1,0,0,0]:
            ml = "red_ml"
        elif barrel.potion_type == [0,1,0,0]:
            ml = "green_ml"
        elif barrel.potion_type == [0,0,1,0]:
            ml = "blue_ml"
        elif barrel.potion_type == [0,0,0,1]:
            ml = "dark_ml"
            
        with db.engine.begin() as connection:
            sql_to_execute = """ 
            INSERT INTO ledger (transaction_id, type, change) VALUES
            (:id, :barrel_type, :quantity)
            """
            connection.execute(sqlalchemy.text(sql_to_execute), [{"id": id, 
                "barrel_type": ml, "quantity": barrel.ml_per_barrel * barrel.quantity}])
    

    with db.engine.begin() as connection:
        sql_to_execute =""" 
        INSERT INTO ledger (transaction_id, type, change) VALUES (:id, 'gold', :change)
        """
        connection.execute(sqlalchemy.text(sql_to_execute), [{"id": id, "change" : -1 * total_expenses}])

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    #check to see if number of red potions is less than 10, if so, 
    #buy one
    print(wholesale_catalog)
    catalog = {}
    for barrel in wholesale_catalog:
        catalog[barrel.sku] = barrel
    
    with db.engine.begin() as connection:
        sql_to_execute = """ 
        SELECT COALESCE(SUM(change), 0) AS total_gold FROM ledger WHERE type = 'gold'
        """
        result = connection.execute(sqlalchemy.text(sql_to_execute))
        first_row = result.first()

    gold = first_row.total_gold
    print(gold)
    return_list = []
    priority_list = get_priority()
    print(priority_list)

    for color in priority_list:
        sku = get_size(gold, priority_list[color], color, catalog)
        if sku != None:
            quantity = get_quant(gold, priority_list[color], sku, catalog)
            if(quantity != 0): 
                gold -= (catalog[sku].price * quantity)
                return_list.append({
                    "sku": sku,
                    "quantity": quantity
                })
    
    
    return return_list

     
#what size of potion should be bought      
def get_size(gold: int,  ml: int, type_potion: str, catalog: dict):
    print("type potion: "+ type_potion + "\nml: ", ml)
    if type_potion == "red":
        if "LARGE_RED_BARREL" in catalog and gold >= catalog["LARGE_RED_BARREL"].price:
            return "LARGE_RED_BARREL"
        elif "MEDIUM_RED_BARREL" in catalog and gold >= catalog["MEDIUM_RED_BARREL"].price:
            return "MEDIUM_RED_BARREL"
        elif "SMALL_RED_BARREL" in catalog and gold >= catalog["SMALL_RED_BARREL"].price:
            return "SMALL_RED_BARREL"
    elif type_potion == "green":
        if "LARGE_GREEN_BARREL" in catalog and gold >= catalog["LARGE_GREEN_BARREL"].price:
            return "LARGE_GREEN_BARREL"
        elif "MEDIUM_GREEN_BARREL" in catalog and gold >= catalog["SMALL_GREEN_BARREL"].price:
            return "MEDIUM_GREEN_BARREL"
        elif "SMALL_GREEN_BARREL" in catalog and gold >= catalog["SMALL_GREEN_BARREL"].price:
            return "SMALL_GREEN_BARREL"
    elif type_potion == "blue":
        if "LARGE_BLUE_BARREL" in catalog and gold >= catalog["LARGE_BLUE_BARREL"].price:
            return "LARGE_BLUE_BARREL"
        elif "MEDIUM_BLUE_BARREL" in catalog and gold >= catalog["MEDIUM_BLUE_BARREL"].price:
            return "MEDIUM_BLUE_BARREL"
        elif "SMALL_BLUE_BARREL" in catalog and gold >= catalog["SMALL_BLUE_BARREL"].price:
            return "SMALL_BLUE_BARREL"
    elif type_potion == "dark":
        if "LARGE_DARK_BARREL" in catalog and gold >= catalog["LARGE_DARK_BARREL"].price:
            return "LARGE_DARK_BARREL"
        elif "MEDIUM_DARK_BARREL" in catalog and gold >= catalog["MEDIUM_DARK_BARREL"].price:
            return "MEDIUM_DARK_BARREL"
        elif "SMALL_DARK_BARREL" in catalog and gold >= catalog["SMALL_DARK_BARREL"].price:
            return "SMALL_DARK_BARREL"
    return 

def get_quant(gold: int, ml: int, sku: str, catalog: dict):
    if gold < 10000:
        return 1
    desired_ml = 20000 - ml
    total = desired_ml // catalog[sku].ml_per_barrel
    return min(total, catalog[sku].quantity)
    

#decides the priority of the potions, which one should be bought first
def get_priority():
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

    dictionary = {"red": first_row.num_red_ml, "green": first_row.num_green_ml, "blue": first_row.num_blue_ml, 
                  "dark": first_row.num_dark_ml}
    
    sorted_list = dict(sorted(dictionary.items(), key = lambda color : color[1]))
    print(sorted_list)

    return sorted_list

