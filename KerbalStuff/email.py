import smtplib
import pystache
import os
from email.mime.text import MIMEText

from KerbalStuff.database import db
from KerbalStuff.objects import User
from KerbalStuff.config import _cfg, _cfgi

def send_confirmation(user):
    smtp = smtplib.SMTP(_cfg("smtp-host"), _cfgi("smtp-port"))
    smtp.login(_cfg("smtp-user"), _cfg("smtp-password"))
    with open("emails/confirm-account") as f:
        message = MIMEText(pystache.render(f.read(), user))
    message['Subject'] = "Welcome to Kerbal Stuff!"
    message['From'] = "support@kerbalstuff.com"
    message['To'] = user.email
    smtp.sendmail("support@kerbalstuff.com", [ user.email ], message.as_string())
    smtp.quit()
