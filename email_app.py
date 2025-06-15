import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_mail import Mail, Message
from dotenv import load_dotenv
from datetime import datetime
import csv
import pandas as pd

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

# 🔧 Explicitly set the templates folder
app = Flask(__name__, template_folder='templates')
app.secret_key = os.getenv("SECRET_KEY", "default_key")

# Load email accounts from .env
email_accounts = [
    {
        "MAIL_USERNAME": os.getenv("MAIL_USERNAME_1"),
        "MAIL_PASSWORD": os.getenv("MAIL_PASSWORD_1"),
    },
    {
        "MAIL_USERNAME": os.getenv("MAIL_USERNAME_2"),
        "MAIL_PASSWORD": os.getenv("MAIL_PASSWORD_2"),
    }
]

# Mail server configuration from .env
app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER")
app.config["MAIL_PORT"] = int(os.getenv("MAIL_PORT"))
app.config["MAIL_USE_TLS"] = os.getenv("MAIL_USE_TLS") == "True"
app.config["MAIL_USE_SSL"] = os.getenv("MAIL_USE_SSL") == "True"

mail = Mail(app)

@app.route('/')
def index():
    search_query = request.args.get('search', '')

    try:
        df = pd.read_csv("emails.csv", names=["Sender Email", "Recipient", "Subject", "Message", "Timestamp"], encoding="ISO-8859-1")
        emails = df.to_dict(orient="records")

        if search_query:
            emails = [
                email for email in emails
                if search_query.lower() in email["Recipient"].lower() or
                   search_query.lower() in email["Subject"].lower()
            ]
    except FileNotFoundError:
        emails = []

    return render_template("index.html", emails=emails, search_query=search_query)

@app.route('/send-email', methods=['POST'])
def send_email():
    recipient_email = request.form['recipient_email']
    subject = request.form['subject']
    message = request.form['message']

    for account in email_accounts:
        try:
            app.config["MAIL_USERNAME"] = account["MAIL_USERNAME"]
            app.config["MAIL_PASSWORD"] = account["MAIL_PASSWORD"]

            msg = Message(subject, sender=app.config["MAIL_USERNAME"], recipients=[recipient_email])
            msg.body = message
            mail.send(msg)

            with open("emails.csv", mode="a", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow([
                    app.config["MAIL_USERNAME"], recipient_email,
                    subject, message, datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ])

            flash(f"Email sent successfully from {app.config['MAIL_USERNAME']}!", "success")
        except Exception as e:
            flash(f"Error sending email from {app.config['MAIL_USERNAME']}: {str(e)}", "danger")

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
