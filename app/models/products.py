from app.connections.connections import DB_manager

class Products:
    @staticmethod
    def get_by_id(id: str) -> dict:
        sql = 'SELECT * FROM products WHERE code = ?;'
        db = DB_manager.get_products_db()
        ans = dict(db.execute(sql, [id]).fetchone())
        DB_manager.close_products_db()

        return ans