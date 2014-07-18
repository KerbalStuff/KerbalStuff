import smtplib
import pystache
import os
from email.mime.text import MIMEText
from werkzeug.utils import secure_filename

from KerbalStuff.database import db
from KerbalStuff.objects import User
from KerbalStuff.config import _cfg, _cfgi

def send_confirmation(user):
    if _cfg("smtp-host") == "":
        return
    smtp = smtplib.SMTP(_cfg("smtp-host"), _cfgi("smtp-port"))
    smtp.login(_cfg("smtp-user"), _cfg("smtp-password"))
    with open("emails/confirm-account") as f:
        message = MIMEText(pystache.render(f.read(), { 'user': user, "domain": _cfg("domain"), 'confirmation': user.confirmation }))
    message['X-MC-Important'] = "true"
    message['Subject'] = "Welcome to Kerbal Stuff!"
    message['From'] = "support@kerbalstuff.com"
    message['To'] = user.email
    smtp.sendmail("support@kerbalstuff.com", [ user.email ], message.as_string())
    smtp.quit()

def send_reset(user):
    if _cfg("smtp-host") == "":
        return
    smtp = smtplib.SMTP(_cfg("smtp-host"), _cfgi("smtp-port"))
    smtp.login(_cfg("smtp-user"), _cfg("smtp-password"))
    with open("emails/password-reset") as f:
        message = MIMEText(pystache.render(f.read(), { 'user': user, "domain": _cfg("domain"), 'confirmation': user.passwordReset }))
    message['X-MC-Important'] = "true"
    message['Subject'] = "Reset your password on Kerbal Stuff"
    message['From'] = "support@kerbalstuff.com"
    message['To'] = user.email
    smtp.sendmail("support@kerbalstuff.com", [ user.email ], message.as_string())
    smtp.quit()

def send_update_notification(mod):
    if _cfg("smtp-host") == "":
        return
    followers = [u.email for u in mod.followers]
    changelog = mod.versions[-1].changelog
    if changelog:
        changelog = '\n'.join(['    ' + l for l in changelog.split('\n')])

    for follower in followers:
        smtp = smtplib.SMTP(_cfg("smtp-host"), _cfgi("smtp-port"))
        smtp.login(_cfg("smtp-user"), _cfg("smtp-password"))
        with open("emails/mod-updated") as f:
            message = MIMEText(pystache.render(f.read(),
                {
                    'mod': mod,
                    'domain': _cfg("domain"),
                    'latest': mod.versions[-1],
                    'url': '/mod/' + str(mod.id) + '/' + secure_filename(mod.name)[:64],
                    'changelog': changelog
                }))
        message['Subject'] = mod.user.username + " has just updated " + mod.name + "!"
        message['From'] = "support@kerbalstuff.com"
        message['To'] = follower
        smtp.sendmail("support@kerbalstuff.com", [ follower ], message.as_string())
        smtp.quit()

def send_autoupdate_notification(mod):
    if _cfg("smtp-host") == "":
        return
    followers = [u.email for u in mod.followers]
    changelog = mod.versions[-1].changelog
    if changelog:
        changelog = '\n'.join(['    ' + l for l in changelog.split('\n')])

    for follower in followers:
        smtp = smtplib.SMTP(_cfg("smtp-host"), _cfgi("smtp-port"))
        smtp.login(_cfg("smtp-user"), _cfg("smtp-password"))
        with open("emails/mod-autoupdated") as f:
            message = MIMEText(pystache.render(f.read(),
                {
                    'mod': mod,
                    'domain': _cfg("domain"),
                    'latest': mod.versions[-1],
                    'url': '/mod/' + str(mod.id) + '/' + secure_filename(mod.name)[:64],
                    'changelog': changelog
                }))
        message['Subject'] = mod.name + " is compatible with KSP " + mod.versions[0].ksp_version + "!"
        message['From'] = "support@kerbalstuff.com"
        message['To'] = follower
        smtp.sendmail("support@kerbalstuff.com", [ follower ], message.as_string())
        smtp.quit()

def send_bulk_email(users, subject, body):
    if _cfg("smtp-host") == "":
        return
    for u in users:
        smtp = smtplib.SMTP(_cfg("smtp-host"), _cfgi("smtp-port"))
        smtp.login(_cfg("smtp-user"), _cfg("smtp-password"))
        message = MIMEText(body)
        message['Subject'] = subject
        message['From'] = "support@kerbalstuff.com"
        message['To'] = u
        smtp.sendmail("support@kerbalstuff.com", [ u ], message.as_string())
        smtp.quit()
