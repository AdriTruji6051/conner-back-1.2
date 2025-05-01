from flask import Blueprint, render_template

routesTemplates = Blueprint('routes-templates', __name__)

@routesTemplates.route('/')
@routesTemplates.route('/dashboard')
@routesTemplates.route('/<path:path>')
@routesTemplates.route('/dashboard/<path:path>')
def serve_index(path=None):
    print(path)
    return render_template('index.html')