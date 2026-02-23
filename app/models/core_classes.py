from app.extensions import db
from datetime import datetime

SET_NULL = 'SET NULL'
CASCADE = 'CASCADE'
CASCADE_ALL_ORPHANS = 'all, delete-orphan'
PRODUCTS_CODE = 'products.code'
# ===================== MAIN DB MODELS =====================

class Department(db.Model):
    __tablename__ = 'departments'

    code = db.Column(db.Integer, primary_key=True, autoincrement=True)
    description = db.Column(db.Text, nullable=False)

    products = db.relationship('Product', backref='department_ref', lazy='dynamic', foreign_keys='Product.department')

    def to_dict(self) -> dict:
        return {
            'code': self.code,
            'description': self.description,
        }


class Product(db.Model):
    __tablename__ = 'products'

    code = db.Column(db.Text, primary_key=True, nullable=False, unique=True)
    description = db.Column(db.Text, nullable=False)
    sale_type = db.Column(db.Text, nullable=False)
    cost = db.Column(db.Float, nullable=True)
    sale_price = db.Column(db.Float, nullable=False)
    department = db.Column(db.Integer, db.ForeignKey('departments.code', onupdate=CASCADE, ondelete=SET_NULL), nullable=True)
    wholesale_price = db.Column(db.Float, nullable=True)
    priority = db.Column(db.Integer, nullable=True)
    inventory = db.Column(db.Float, nullable=True)
    modified_at = db.Column(db.Text, nullable=True)
    profit_margin = db.Column(db.Integer, nullable=True)
    parent_code = db.Column(db.Text, db.ForeignKey(PRODUCTS_CODE, onupdate=CASCADE, ondelete=SET_NULL), nullable=True)

    # Relationships
    children = db.relationship('Product', backref=db.backref('parent', remote_side=[code]), lazy='dynamic')
    associates = db.relationship('AssociateCode', backref='parent_product', lazy='dynamic', cascade=CASCADE_ALL_ORPHANS)
    inventory_logs = db.relationship('InventoryLog', backref='product', lazy='dynamic', cascade=CASCADE_ALL_ORPHANS)

    def to_dict(self, is_associate: bool = False) -> dict:
        return {
            'code': self.code,
            'description': self.description,
            'sale_type': self.sale_type,
            'cost': self.cost,
            'sale_price': self.sale_price,
            'department': self.department,
            'wholesale_price': self.wholesale_price,
            'priority': self.priority,
            'inventory': self.inventory,
            'modified_at': self.modified_at,
            'profit_margin': self.profit_margin,
            'parent_code': self.parent_code,
            'is_associate': is_associate,
        }


class InventoryLog(db.Model):
    __tablename__ = 'inventory_log'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_code = db.Column(db.Text, db.ForeignKey(PRODUCTS_CODE, onupdate=CASCADE, ondelete=CASCADE), nullable=False)
    old_inventory = db.Column(db.Float, nullable=True)
    new_inventory = db.Column(db.Float, nullable=True)
    change = db.Column(db.Float, nullable=True)
    change_type = db.Column(db.Text, nullable=True)  # 'INCREASE' or 'DECREASE'
    modified_at = db.Column(db.Text, default=lambda: datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'product_code': self.product_code,
            'old_inventory': self.old_inventory,
            'new_inventory': self.new_inventory,
            'change': self.change,
            'change_type': self.change_type,
            'modified_at': self.modified_at,
        }


class AssociateCode(db.Model):
    __tablename__ = 'associates_codes'

    code = db.Column(db.Text, primary_key=True, nullable=False)
    parent_code = db.Column(db.Text, db.ForeignKey(PRODUCTS_CODE, onupdate=CASCADE, ondelete=CASCADE), nullable=False)
    tag = db.Column(db.Text, nullable=True)

    def to_dict(self) -> dict:
        return {
            'code': self.code,
            'parent_code': self.parent_code,
            'tag': self.tag,
        }


# ===================== TICKETS MODELS =====================

class TicketModel(db.Model):
    __tablename__ = 'tickets'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created_at = db.Column(db.Text, nullable=False)
    modified_at = db.Column(db.Text, nullable=True)
    sub_total = db.Column(db.Float, nullable=False)
    total = db.Column(db.Float, nullable=False)
    profit = db.Column(db.Float, nullable=False)
    products_count = db.Column(db.Integer, nullable=False)
    notes = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, nullable=False)
    ipv4_sender = db.Column(db.Text, nullable=False)
    discount = db.Column(db.Float, nullable=True)

    products_in_ticket = db.relationship('ProductInTicket', backref='ticket', lazy='dynamic', cascade=CASCADE_ALL_ORPHANS)

    def to_dict(self, include_products: bool = False) -> dict:
        d = {
            'id': self.id,
            'created_at': self.created_at,
            'modified_at': self.modified_at,
            'sub_total': self.sub_total,
            'total': self.total,
            'profit': self.profit,
            'products_count': self.products_count,
            'notes': self.notes,
            'user_id': self.user_id,
            'ipv4_sender': self.ipv4_sender,
            'discount': self.discount,
        }
        if include_products:
            d['products'] = [p.to_dict() for p in self.products_in_ticket.all()]
        return d


class ProductInTicket(db.Model):
    __tablename__ = 'product_in_ticket'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('tickets.id'), nullable=False)
    code = db.Column(db.Text, db.ForeignKey(PRODUCTS_CODE, onupdate=CASCADE, ondelete=SET_NULL), nullable=True)
    description = db.Column(db.Text, nullable=False)
    cantity = db.Column(db.Float, nullable=False)
    profit = db.Column(db.Float, nullable=True)
    wholesale_price = db.Column(db.Float, nullable=True)
    sale_price = db.Column(db.Float, nullable=False)

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'ticket_id': self.ticket_id,
            'code': self.code,
            'description': self.description,
            'cantity': self.cantity,
            'profit': self.profit,
            'wholesale_price': self.wholesale_price,
            'sale_price': self.sale_price,
        }


# ===================== ANALYTICS MODELS =====================

class DrawerLog(db.Model):
    __tablename__ = 'drawer_logs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    open_at = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    method = db.Column(db.Text, nullable=False)
    transaction_type = db.Column(db.Integer, nullable=False)
    transaction_id = db.Column(db.Integer, nullable=True)

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'open_at': self.open_at,
            'user_id': self.user_id,
            'method': self.method,
            'transaction_type': self.transaction_type,
            'transaction_id': self.transaction_id,
        }


class ProductChange(db.Model):
    __tablename__ = 'products_changes'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code = db.Column(db.Text, nullable=False)
    original_code = db.Column(db.Text, nullable=True)
    cost = db.Column(db.Float, nullable=True)
    sale_price = db.Column(db.Float, nullable=False)
    wholesale_price = db.Column(db.Float, nullable=True)
    modified_at = db.Column(db.Text, nullable=False)
    method = db.Column(db.Text, nullable=True)

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'code': self.code,
            'original_code': self.original_code,
            'cost': self.cost,
            'sale_price': self.sale_price,
            'wholesale_price': self.wholesale_price,
            'modified_at': self.modified_at,
            'method': self.method,
        }


class CashFlow(db.Model):
    __tablename__ = 'cash_flow'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    description = db.Column(db.Text, nullable=True)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.Text, nullable=False)
    in_or_out = db.Column(db.Integer, nullable=False)
    is_payment = db.Column(db.Integer, nullable=False, default=0)

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'description': self.description,
            'amount': self.amount,
            'date': self.date,
            'in_or_out': self.in_or_out,
            'is_payment': self.is_payment,
        }


# ===================== CONFIG MODELS =====================

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user = db.Column(db.Text, nullable=False, unique=True)
    user_name = db.Column(db.Text, nullable=False)
    password = db.Column(db.Text, nullable=False)
    role_type = db.Column(db.Text, nullable=False)

    def to_dict(self, include_password: bool = False) -> dict:
        d = {
            'id': self.id,
            'user': self.user,
            'user_name': self.user_name,
            'role_type': self.role_type,
        }
        if include_password:
            d['password'] = self.password
        return d


class TicketFontConfig(db.Model):
    __tablename__ = 'ticket_font_configs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    font = db.Column(db.Text, nullable=False)
    weigh = db.Column(db.Integer, nullable=False)
    size = db.Column(db.Integer, nullable=False)

    text_entries = db.relationship('TicketText', backref='font_config_ref', lazy='dynamic')

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'font': self.font,
            'weigh': self.weigh,
            'size': self.size,
        }


class TicketText(db.Model):
    __tablename__ = 'ticket_text'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    text = db.Column(db.Text, nullable=False)
    line = db.Column(db.Integer, nullable=False)
    is_header = db.Column(db.Integer, nullable=False)
    font_config = db.Column(db.Integer, db.ForeignKey('ticket_font_configs.id', onupdate=CASCADE, ondelete=SET_NULL), nullable=True)

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'text': self.text,
            'line': self.line,
            'is_header': self.is_header,
            'font_config': self.font_config,
        }

    def to_display_dict(self) -> dict:
        """Returns dict with font info joined, used for header/footer display."""
        fc = self.font_config_ref
        return {
            'text': self.text,
            'line': self.line,
            'font': fc.font if fc else None,
            'size': fc.size if fc else None,
            'weigh': fc.weigh if fc else None,
            'font_config': self.font_config,
        }


# ===================== SQLALCHEMY EVENT: Inventory tracking =====================

from sqlalchemy import event, inspect

@event.listens_for(Product, 'after_insert')
@event.listens_for(Product, 'after_update')
@event.listens_for(Product, 'after_delete')
def track_inventory_changes(mapper, connection, target):
    """Replaces the old SQLite TRIGGER track_inventory_changes."""
    state = inspect(target)
    history = state.attrs.inventory.history

    if not history.has_changes():
        return

    old_val = history.deleted[0] if history.deleted else None
    new_val = history.added[0] if history.added else None

    if old_val is None and new_val is None:
        return

    change = (new_val or 0) - (old_val or 0)
    if change == 0:
        return

    change_type = 'INCREASE' if change > 0 else 'DECREASE'

    connection.execute(
        InventoryLog.__table__.insert().values(
            product_code=target.code,
            old_inventory=old_val,
            new_inventory=new_val,
            change=change,
            change_type=change_type,
            modified_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        )
    )
