import smtplib
from email.message import EmailMessage

def test_smtp():
    msg = EmailMessage()
    msg['From'] = "audraykouya@gmail.com"
    msg['To'] = "audraykouya@gmail.com"
    msg['Subject'] = "Test SMTP Urgent"
    msg.set_content("Ceci est un test critique")

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login("audraykouya@gmail.com", "rfhvgvzlukhbqtxe")
        server.send_message(msg)
    print("SUCCÈS SMTP!")

test_smtp()