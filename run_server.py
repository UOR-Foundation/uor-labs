#!/usr/bin/env python3
"""Convenience script to start the HTTP API server."""
from uor.api_server import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
