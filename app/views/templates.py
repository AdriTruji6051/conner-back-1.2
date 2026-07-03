from flask import Blueprint, render_template, redirect, url_for
from app.routes_constants import (
    ROUTE_INDEX, ROUTE_PAGE_INDEX, ROUTE_PAGE_DYNAMIC
)

routesTemplates = Blueprint('routes-templates', __name__)

@routesTemplates.route(ROUTE_INDEX)
def redirect_to_page():
    """Redirect root to /page/ for Angular app"""
    return redirect('/page/', code=302)

@routesTemplates.route(ROUTE_PAGE_INDEX)
@routesTemplates.route(ROUTE_PAGE_INDEX + '/')
@routesTemplates.route(ROUTE_PAGE_DYNAMIC)
def serve_index(path=None):
    """Serve Angular app for all /page/* routes"""
    return render_template('index.html')