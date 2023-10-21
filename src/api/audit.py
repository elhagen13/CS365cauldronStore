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
    get_quant = """SELECT type, COALESCE(SUM(change),0) AS total FROM ledger GROUP BY type"""
    total_ml = 0
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(get_quant))
        for row in result:
            if row.type == "gold":
                gold = row.total
            if row.type == "potion":
                potion = row.total
            if row.type == "red_ml" or row.type == "green_ml" or row.type == "blue_ml" or row.type == "dark_ml":
                total_ml += row.total
        
    
    return {"number_of_potions": potion, "ml_in_barrels": total_ml, "gold": gold}

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
