from app import app, db, User

with app.app_context():
    # Create admin user
    admin = User(username='admin', password='admin123')
    db.session.add(admin)
    db.session.commit()
    print("Admin user created successfully!")
    print("Username: admin")
    print("Password: admin123")
