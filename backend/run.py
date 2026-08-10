from app import create_app
from app.database import db
from app.models.user import User

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        # Create tables if they don't exist
        db.create_all()
        
    app.run(debug=True, port=5000)
