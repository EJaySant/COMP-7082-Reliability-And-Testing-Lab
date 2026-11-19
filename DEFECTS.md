| # | Where the defect occurred | What can go wrong | How it was corrected |
|---|---|---|---|
| 1 | repository.py > get_product & get_saved_cart | The function places input directly into the database string query rather than in a prepared statement, which may cause a security risk from a possible injection attack. | Converted the f strings into prepared statements and passed the input as a tuple. |
| 2 | repository.py > list_orders | The parameter user_id goes unused and the function effectively returns all of the orders, which exposes unintended orders from other users. | Added a where clause to the prepared statement that would ensure that only orders from the given user is returned and not all of the orders. |
| 3 | repository.py > update_stock | The current prepared statement will update product stock even if there isn't enough stock available causing stock to become negative. | Updated the query statement to ensure that only products with enough stock are updated, updated the parameter variable name in the function to be more clear and added a return of true or false to indicate if the product was updated. |
| 4 | repository.py > save_cart | The current function separately executes 2 prepared statements, which means that the function is no longer atomic and may cause an unintended state in the user cart if the 2nd statements fails. | Added with resources condition statement to ensure that the function does not create an unintended state . |
| 5 | | | |
| 6 | | | |
| 7 | | | |
| 8 | | | |
| 9 | | | |
| 10 | | | |