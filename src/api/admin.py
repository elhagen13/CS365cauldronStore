from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.post("/reset")
def reset():
    """
    Reset the game state. Gold goes to 100, all potions are removed from
    inventory, and all barrels are removed from inventory. Carts are all reset.
    """
    sql_to_execute = """
    TRUNCATE customer;
    TRUNCATE ledger;
    TRUNCATE orders;
    TRUNCATE transactions;
    """
    insert_into = """INSERT INTO ledger (type, change) VALUES
    ('gold', 100)"""
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(sql_to_execute))
        connection.execute(sqlalchemy.text(insert_into))

    return "OK"


@router.get("/shop_info/")
def get_shop_info():
    """ """
    # TODO: Change me!
    return {
        "shop_name": "wizard-stuff",
        "shop_owner": "Ella Hagen",
    }

