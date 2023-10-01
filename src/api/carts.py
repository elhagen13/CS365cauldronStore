from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

red_potion_price = 50

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
        sql_to_execute = f"""INSERT INTO customer (customer_name) VALUES ('{new_cart.customer}') RETURNING id """
        result = connection.execute(sqlalchemy.text(sql_to_execute))
        first_row = result.first()

    return {"cart_id": first_row.id}



@router.get("/{cart_id}")
def get_cart(cart_id: int):
    #identify a customer by their id
    with db.engine.begin() as connection:
        sql_to_execute = f"""SELECT customer_name FROM customer WHERE id = {cart_id}"""
        result = connection.execute(sqlalchemy.text(sql_to_execute))
        first_row = result.first()

    return {first_row.customer_name}


class CartItem(BaseModel):
    #a potion
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
   #customer, what they're buying and the quantity
   with db.engine.begin() as connection:
       sql_to_execute = f"""UPDATE customer SET {item_sku} = {cart_item.quantity},
       total = total + ({red_potion_price} * {cart_item.quantity}) WHERE id = {cart_id}"""
       connection.execute(sqlalchemy.text(sql_to_execute))

   return "OK"

class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):

    with db.engine.begin() as connection:
       sql_inventory = """SELECT num_red_potions FROM global_inventory"""
       sql_customer = f"""SELECT red_potion, total FROM customer WHERE id = {cart_id}"""
       result_requested = connection.execute(sqlalchemy.text(sql_customer))
       result_in_inventory = connection.execute(sqlalchemy.text(sql_inventory))
       
       customer_requested =  result_requested.first()
       potions_in_inventory = result_in_inventory.first()

       if customer_requested.red_potion > potions_in_inventory.num_red_potions:
           return "Not enough potions in inventory"
       
       total_gold = customer_requested.red_potion * red_potion_price

       connection.execute(sqlalchemy.text(f"""UPDATE global_inventory
                                           SET gold = gold +  {total_gold}, 
                                           num_red_potions = num_red_potions - {customer_requested.red_potion}"""))
       connection.execute(sqlalchemy.text(f"""UPDATE customer
                                            SET payment = "{cart_checkout.payment}" WHERE id = {cart_id}"""))
       


    return {"total_potions_bought": customer_requested.red_potion, "total_gold_paid": total_gold}
