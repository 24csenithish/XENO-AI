# scripts/setup.py
import os
from app.database.database import engine, Base
from app.database import models  # import to register models
from app.config import settings

def setup():
    print("✦ XENO AI Setup")
    print(f"Using database: {settings.DATABASE_URL}")
    # Create tables
    Base.metadata.create_all(bind=engine)
    print("Database tables created.")
    # Ensure directories exist
    os.makedirs("data/knowledge", exist_ok=True)
    os.makedirs("data/uploads", exist_ok=True)
    os.makedirs("storage", exist_ok=True)
    os.makedirs("models/adapters", exist_ok=True)
    print("Directory structure verified.")
    print("Setup complete.")

if __name__ == "__main__":
    setup()