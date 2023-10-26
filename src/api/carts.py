from fastapi import APIRouter, Depends, Request, HTTPException, FastAPI
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db
from enum import Enum

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)

class search_sort_options(str, Enum):
    customer_name = "customer_name"
    item_sku = "item_sku"
    line_item_total = "line_item_total"
    timestamp = "timestamp"

class search_sort_order(str, Enum):
    asc = "asc"
    desc = "desc"   

@router.get("/search/", tags=["search"])
def search_orders(
    customer_name: str = "",
    potion_sku: str = "",
    search_page: str = "",
    sort_col: search_sort_options = search_sort_options.timestamp,
    sort_order: search_sort_order = search_sort_order.desc,
):
    
    if sort_order.value == "desc":
        order = "DESC"
    else:
        order = "ASC"

    sql_to_execute = f"""
    SELECT customer.customer_name, orders.order_no, orders.time AS timestamp,
    orders.potion_type AS item_sku, orders.quantity, orders.quantity * potions.price AS line_item_total


    FROM orders
    JOIN customer ON orders.user_id = customer.user_id
    JOIN potions on orders.potion_type = potions.potion_type
    WHERE 
    (:customer_name = '' AND :potion_sku = '') OR
    (:customer_name != '' AND :potion_sku != '' AND
    customer_name ILIKE :customer_name AND orders.potion_type ILIKE :potion_sku) OR
    (:customer_name = '' AND orders.potion_type ILIKE :potion_sku) OR
    (:potion_sku = '' AND customer_name ILIKE :customer_name)
  
    ORDER BY {sort_col.value} {order}, orders.order_no ASC
    LIMIT 6 OFFSET :cur_page
    """

    if search_page == "":
        search_page = "0"

    return_list = []
    next_page = False
    with db.engine.begin() as connection: 
        result = connection.execute(sqlalchemy.text(sql_to_execute), 
                [{"cur_page": search_page, "customer_name": f'%{customer_name}%', "potion_sku": f'%{potion_sku}%'}])
        index = 0
        for row in result:
            plural = ""
            if row.quantity > 1:
                plural = "s"
            return_list.append({
                "line_item_id": int(search_page) + index,
                "item_sku": str(row.quantity) + " " + row.item_sku.replace("_", " ") + plural,
                "customer_name": row.customer_name,
                "line_item_total": row.line_item_total,
                "timestamp": row.timestamp,
            })
            index += 1
            if index >= 5:
                next_page = True
                break
        
    if next_page == True:
        next = str(int(search_page) + index)
    else:
        next = ""

    if search_page != "0":
        previous = str(int(search_page) - 5)
    else:
        previous = ""
    
    return {
        "previous": previous,
        "next": next,
        "results": return_list,
    }


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
        sql_to_execute = """SELECT COALESCE(SUM(change), 0) AS inventory FROM ledger WHERE potion_type = :item_sku"""
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
        sql_to_execute = """SELECT orders.potion_type, orders.quantity, potions.price, ledger.inventory, customer.customer_name
        FROM orders
        JOIN potions ON orders.potion_type = potions.potion_type
        JOIN(
            SELECT potion_type, SUM(change) AS inventory FROM ledger
            WHERE potion_type IS NOT NULL GROUP BY potion_type
        ) AS ledger ON orders.potion_type = ledger.potion_type
        JOIN customer ON orders.user_id = customer.user_id
        WHERE orders.user_id = :cart_id
        """
        result = connection.execute(sqlalchemy.text(sql_to_execute), [{"cart_id": cart_id}])
        total_price = 0
        total_quantity = 0
        dictionary = {}
        for row in result:
            print(row)
            customer_name = row.customer_name
            if row.quantity > row.inventory:
                raise HTTPException(status_code=404, detail = "Not enough potions in inventory")
            
            if row.potion_type in dictionary:
                dictionary[row.potion_type]['quantity'] += row.quantity
            else:
                dictionary[row.potion_type] = {
                    'quantity': row.quantity,
                    'price': row.price,
                    'inventory': row.inventory,
                    'customer': row.customer_name
                }
            total_price += (row.quantity * row.price)
            total_quantity += row.quantity

        sql_to_execute = """INSERT INTO transactions (description) VALUES (:description) RETURNING id"""
        id = connection.execute(sqlalchemy.text(sql_to_execute), [{"description": "Sold " + str(total_quantity) + 
        " potions to " + customer_name}]).first().id
        
        for order in dictionary:
            sql_to_execute = """INSERT INTO ledger (transaction_id, type, potion_type, change)
             VALUES (:id, 'potion', :potion_type, :change) """
            connection.execute(sqlalchemy.text(sql_to_execute),
                               [{"id": id, "potion_type": order,
                                 "change": -1 * dictionary[order]['quantity']}])
            

        sql_to_execute = """INSERT INTO ledger (transaction_id, type, change) 
        VALUES (:id, 'gold', :change )"""
        connection.execute(sqlalchemy.text(sql_to_execute), [{"id": id, "change": total_price}])

    return {"total_potions_bought": total_quantity, "total_gold_paid": total_price}
    
