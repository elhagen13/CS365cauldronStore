from fastapi import APIRouter, Depends, Request
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
       potions = """SELECT num_red_potions, num_green_potions, num_blue_potions FROM global_inventory"""
       result = connection.execute(sqlalchemy.text(potions))
    num_potions = result.first()
    if item_sku == "red_potion":
       if num_potions.num_red_potions < cart_item.quantity:
           return "Not enough potions in inventory"
       else:
           sql_to_execute = f"""UPDATE customer SET {item_sku} = {cart_item.quantity},
           total = total + ({red_potion_price} * {cart_item.quantity}) WHERE id = {cart_id}"""
    
    elif item_sku == "green_potion":
        if num_potions.num_green_potions < cart_item.quantity:
           return "Not enough potions in inventory"
        else:
           sql_to_execute = f"""UPDATE customer SET {item_sku} = {cart_item.quantity},
           total = total + ({green_potion_price} * {cart_item.quantity}) WHERE id = {cart_id}"""
    
    elif item_sku == "blue_potion":
        if num_potions.num_blue_potions < cart_item.quantity:
            return "Not enough potions in inventory"
        else:
            sql_to_execute = f"""UPDATE customer SET {item_sku} = {cart_item.quantity},
            total = total + ({blue_potion_price} * {cart_item.quantity}) WHERE id = {cart_id}"""
    
       
    with db.engine.begin() as connection:
       connection.execute(sqlalchemy.text(sql_to_execute))
       
    return "OK"

class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    sql_customer = f"""SELECT red_potion, green_potion, blue_potion, total FROM customer WHERE id = {cart_id}"""
    with db.engine.begin() as connection:
       result_requested = connection.execute(sqlalchemy.text(sql_customer))
       
    customer_requested =  result_requested.first()

    total_gold = (customer_requested.red_potion * red_potion_price) + \
        (customer_requested.green_potion * green_potion_price) + \
        (customer_requested.blue_potion * blue_potion_price)

    total_potions = customer_requested.red_potion + customer_requested.green_potion \
        + customer_requested.blue_potion

    with db.engine.begin() as connection:   
       connection.execute(sqlalchemy.text(f"""UPDATE global_inventory
                                           SET gold = gold +  {total_gold}, 
                                           num_red_potions = num_red_potions - {customer_requested.red_potion},
                                           num_green_potions = num_green_potions - {customer_requested.green_potion},
                                           num_blue_potions = num_blue_potions - {customer_requested.blue_potion}"""))
       connection.execute(sqlalchemy.text(f"""UPDATE customer
                                           SET payment = '{cart_checkout.payment}' WHERE id = {cart_id}"""))

    return {"total_potions_bought": total_potions, "total_gold_paid": total_gold}
