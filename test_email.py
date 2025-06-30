import os
from flask import Flask
from flask_mail import Mail, Message
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Configuration email (chargée depuis .env)
app.config['MAIL_SERVER'] = os.getenv("MAIL_SERVER")
app.config['MAIL_PORT'] = int(os.getenv("MAIL_PORT", 587))
app.config['MAIL_USE_TLS'] = os.getenv("MAIL_USE_TLS", "True").lower() in ['true', '1']
app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")
app.config['MAIL_DEFAULT_SENDER'] = os.getenv("MAIL_DEFAULT_SENDER")

mail = Mail(app)

@app.route('/')
def send_test_email():
    try:
        msg = Message("✅ Test Email depuis Flask",
                      recipients=[os.getenv("MAIL_USERNAME")])
        msg.body = "Ce message est un test simple d’envoi d’email via Flask-Mail et Gmail."
        mail.send(msg)
        return "📧 Email envoyé avec succès !"
    except Exception as e:
        return f"❌ Erreur lors de l'envoi de l'email : {e}"

if __name__ == '__main__':
    app.run(debug=True)
