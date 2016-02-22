import smtplib
from celery import Celery
from email.mime.text import MIMEText
from KerbalStuff.config import _cfg, _cfgi

app = Celery("tasks", broker="redis://localhost:6379/0")

def chunks(l, n):
    """ Yield successive n-sized chunks from l.
    """
    for i in range(0, len(l), n):
        yield l[i:i+n]

@app.task
def send_mail(sender, recipients, subject, message, important=False):
    if _cfg("smtp-host") == "":
        return
    smtp = smtplib.SMTP(_cfg("smtp-host"), _cfgi("smtp-port"))
    smtp.login(_cfg("smtp-user"), _cfg("smtp-password"))
    message = MIMEText(message)
    if important:
        message['X-MC-Important'] = "true"
    message['X-MC-PreserveRecipients'] = "false"
    message['Subject'] = subject
    message['From'] = sender
    for group in chunks(recipients, 100):
        message['To'] = sender
        print("Sending email from {} to {} recipients".format(sender, len(group)))
        smtp.sendmail(sender, group, message.as_string())
    smtp.quit()
