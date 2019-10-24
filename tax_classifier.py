from app import app, db, cli
from app.models import User, Searches


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Search': Searches}