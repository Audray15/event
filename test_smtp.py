import smtplib
from os import environ

def test_gmail():
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(environ.get('MAIL_USERNAME'), 
                   environ.get('MAIL_PASSWORD'))
        server.sendmail(
            environ.get('MAIL_DEFAULT_SENDER'),
            ["votre@email.com"],
            "Subject: Test SMTP\n\nCeci est un test"
        )
    print("Email envoyé avec succès!")

test_gmail()