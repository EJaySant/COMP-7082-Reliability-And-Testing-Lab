| # | Where the defect occurred | What can go wrong | How it was corrected |
|---|---|---|---|
| 1 | repository.py > get_product & get_saved_cart | The function places input directly into the database string query rather than in a prepared statement, which may cause a security risk from a possible injection attack. | Converted the f strings into prepared statements and passed the input as a tuple |
| 2 | repository > list_orders | The parameter user_id goes unused and the function effectively returns all of the orders, which exposes unintended orders from other users. | Added a where clause to the prepared statement that would ensure that only orders from the given user is returned and not all of the orders. |
| 3 | | | |
| 4 | | | |
| 5 | | | |
| 6 | | | |
| 7 | | | |
| 8 | | | |
| 9 | | | |
| 10 | | | |