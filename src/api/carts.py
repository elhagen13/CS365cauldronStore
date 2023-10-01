from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db


cur_id = 1

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
   print(new_cart.customer)
   with db.engine.begin() as connection:
       customer_string = new_cart.customer
       sql_to_execute = f"""INSERT INTO customer (customer_name) VALUES ({customer_string})
         RETURNING id """
       id = connection.execute(sqlalchemy.text(sql_to_execute))
       print(id)


   return {"cart_id": id}



@router.get("/{cart_id}")
def get_cart(cart_id: int):
    #identify a customer by their id
    """ """

    return {}


class CartItem(BaseModel):
    #a potion
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
   #customer, what they're buying and the quantity
   with db.engine.begin() as connection:
       sql_to_execute = f"""UPDATE customer SET {item_sku} = {cart_item.quantity} WHERE id = {cart_id}"""
       connection.execute(sqlalchemy.text(sql_to_execute))
       print(cart_item.quantity)
   return "OK"



class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """

    return {"total_potions_bought": 1, "total_gold_paid": 50}
