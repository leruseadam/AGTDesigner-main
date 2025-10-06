#!/usr/bin/env python3

# Test Flask import and app creation
print("Testing Flask import...")

from flask import Flask

print("✅ Flask imported successfully")

def create_app():
    app = Flask(__name__)
    return app

print("Testing app creation...")
app = create_app()
print("✅ App created successfully")

if __name__ == "__main__":
    print("✅ All tests passed")