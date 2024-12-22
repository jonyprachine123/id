from app import app, db

def update_database():
    with app.app_context():
        db.create_all()
        print("Database updated successfully!")

if __name__ == "__main__":
    update_database()
