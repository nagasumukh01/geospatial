from app.db.database import get_db

# Re-export get_db dependency for clean imports in routes
__all__ = ["get_db"]
