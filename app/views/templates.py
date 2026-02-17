from flask import Blueprint, render_template
from app.routes_constants import (
    ROUTE_INDEX, ROUTE_DASHBOARD, ROUTE_DYNAMIC_PATH, ROUTE_DASHBOARD_DYNAMIC_PATH
)

routesTemplates = Blueprint('routes-templates', __name__)

@routesTemplates.route(ROUTE_INDEX)
@routesTemplates.route(ROUTE_DASHBOARD)
@routesTemplates.route(ROUTE_DYNAMIC_PATH)
@routesTemplates.route(ROUTE_DASHBOARD_DYNAMIC_PATH)
def serve_index(path=None):
    print(path)
    return render_template('index.html')