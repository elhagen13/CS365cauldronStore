from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import math
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/audit",
    tags=["audit"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.get("/inventory")
def get_inventory():
    get_potion = """SELECT inventory FROM potions"""
    get_ml = """SELECT gold, num_red_ml, num_green_ml, num_blue_ml, num_dark_ml FROM global_inventory"""
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(get_potion))
        glo_invent = connection.execute(sqlalchemy.text(get_ml))
        inventory = glo_invent.first()
        total_ml = inventory.num_red_ml + inventory.num_green_ml + inventory.num_blue_ml + inventory.num_dark_ml

    
        total_potions = 0
        for row in result:
            total_potions += row.inventory
    
    return {"number_of_potions": total_potions, "ml_in_barrels": total_ml, "gold": inventory.gold}

class Result(BaseModel):
    gold_match: bool
    barrels_match: bool
    potions_match: bool

# Gets called once a day
@router.post("/results")
def post_audit_results(audit_explanation: Result):
    """ """
    print(audit_explanation)

    return "OK"
