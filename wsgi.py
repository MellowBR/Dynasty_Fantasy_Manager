"""WSGI entry point for Render / PythonAnywhere."""
from init_data import init_data
init_data()

from app import create_app

application = create_app()
