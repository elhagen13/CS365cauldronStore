from fastapi import APIRouter, Depends, Request, HTTPException, FastAPI
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

red_potion_price = 50
green_potion_price = 50
blue_potion_price = 50

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)


class NewCart(BaseModel):
    customer: str

@router.post("/")
def create_cart(new_cart: NewCart):
   #new cart = new customer
    with db.engine.begin() as connection:
        sql_to_execute = """INSERT INTO customer (customer_name) VALUES (:customer_name) RETURNING user_id """
        result = connection.execute(sqlalchemy.text(sql_to_execute), [{"customer_name": new_cart.customer}])
        first_row = result.first()

    return {"cart_id": first_row.user_id}


@router.get("/{cart_id}")
def get_cart(cart_id: int):
    #identify a customer by their id
    with db.engine.begin() as connection:
        sql_to_execute = """SELECT customer_name FROM customer WHERE user_id = :cart_id"""
        result = connection.execute(sqlalchemy.text(sql_to_execute), [{"cart_id": cart_id}])
        first_row = result.first()

    return {first_row.customer_name}


class CartItem(BaseModel):
    #a potion
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    with db.engine.begin() as connection:
        sql_to_execute = """SELECT inventory FROM potions WHERE potion_type = :item_sku"""
        result = connection.execute(sqlalchemy.text(sql_to_execute), [{"item_sku": item_sku}])
        first_row = result.first()
    
    if first_row.inventory < cart_item.quantity:
        raise HTTPException(status_code=404, detail = "Not enough potions in inventory")

    with db.engine.begin() as connection:
        sql_to_execute = """INSERT INTO orders (user_id, potion_type, quantity) 
                            VALUES (:cart_id, :potion_type, :quantity)"""
        connection.execute(sqlalchemy.text(sql_to_execute), [{"cart_id": cart_id, 
                            "potion_type": item_sku, "quantity": cart_item.quantity}])
       
    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    with db.engine.begin() as connection:
        sql_to_execute = """SELECT new_table.quantity, new_table.price, new_table.inventory
                            FROM (
                                SELECT orders.*, potions.price, potions.inventory
                                FROM orders JOIN potions ON orders.potion_type = potions.potion_type
                            ) AS new_table
                            WHERE new_table.user_id = :cart_id"""
        result = connection.execute(sqlalchemy.text(sql_to_execute), [{"cart_id": cart_id}])
    
        total_price = 0
        total_quantity = 0
        for row in result:
            print(row)
            if row.quantity > row.inventory:
                raise HTTPException(status_code=404, detail = "Not enough potions in inventory")
            total_price += (row.quantity * row.price)
            total_quantity += row.quantity


    with db.engine.begin() as connection:
        sql_to_execute = """UPDATE potions
                        SET inventory = potions.inventory - orders.quantity
                        FROM orders
                        WHERE potions.potion_type = orders.potion_type and 
                        orders.user_id = :cart_id """
        other_executable = """UPDATE global_inventory
                            SET gold = gold + :total_price"""
        connection.execute(sqlalchemy.text(sql_to_execute), [{"cart_id": cart_id}])
        connection.execute(sqlalchemy.text(other_executable), [{"total_price": total_price}])



    return {"total_potions_bought": total_quantity, "total_gold_paid": total_price}
    
