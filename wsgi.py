"""Entry point for production servers: gunicorn wsgi:app"""
from neurolens import create_app

app = create_app()
