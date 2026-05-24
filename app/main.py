"""Thin application entry point."""

from app.bootstrap.factory import create_app

app = create_app()
