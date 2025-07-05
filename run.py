from app import create_app, db
from flask_migrate import Migrate

app = create_app()
migrate = Migrate(app, db)

if __name__ == "__main__":
    app.run(debug=True, port=5000)  # Change port if needed
    # Note: In production, you would typically not run the app with debug=True
