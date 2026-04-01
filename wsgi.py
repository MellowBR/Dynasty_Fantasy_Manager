"""WSGI entry point for PythonAnywhere."""
from app import create_app

application = create_app()
