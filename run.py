#!/usr/bin/env python

from app import app

# Run the web app
if __name__ == "__main__":
    app.run(
            debug=True,
            host = "0.0.0.0",
            port = 80,
            )
