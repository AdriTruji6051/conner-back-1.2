from app.models.tickets import Tickets
from app.extensions import db
from flask import Flask
from config.config import Config

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    result = Tickets.list_created_at('2026-06-13', page=1, per_page=10)
    print(f'Total tickets: {result["total"]}')
    print(f'Page: {result["page"]} of {result["total_pages"]}')
    print(f'Showing {len(result["tickets"])} tickets')
    print('\nFirst 3 tickets:')
    for t in result['tickets'][:3]:
        print(f'  ID: {t.id}, Date: {t.created_at}, Total: ${t.total}')
