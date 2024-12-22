import os
import sys
from app import app, db, User

def reset_database():
    # Define the database path
    db_path = os.path.join(app.instance_path, 'prachin_bangla.db')
    
    # Remove the existing database if it exists
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Removed existing database at {db_path}")
    
    # Create the instance folder if it doesn't exist
    if not os.path.exists(app.instance_path):
        os.makedirs(app.instance_path)
    
    # Create all tables
    with app.app_context():
        db.create_all()
        
        # Create admin user
        admin = User(username='admin', password='admin123')
        db.session.add(admin)
        db.session.commit()
        
        print("Database reset complete! Created new database with admin user.")

if __name__ == "__main__":
    reset_database()
