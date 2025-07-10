import os
import logging
import smtplib
from datetime import datetime, timezone
from email.message import EmailMessage

import psycopg2
import psycopg2.extras
from prometheus_client import start_http_server, Counter

logging.basicConfig(level=logging.INFO, format='{"ts":"%(asctime)s","level":"%(levelname)s","msg":"%(message)s"}')

EMAILS_SENT = Counter("notifier_emails_total", "Emails sent")
EMAILS_FAILED = Counter("notifier_failures_total", "Send failures")

PG_HOST = os.getenv("PGHOST", "postgres")
PG_PORT = int(os.getenv("PGPORT", "5432"))
PG_PASS = os.environ["PGPASS"]

SMTP_HOST = os.environ["SMTP_HOST"]
SMTP_PORT = int(os.environ["SMTP_PORT"])
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")

conn = psycopg2.connect(
    host=PG_HOST,
    port=PG_PORT,
    user="postgres",
    password=PG_PASS,
    dbname="events",
)
cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
cur.execute(
    """
CREATE TABLE IF NOT EXISTS events (
    id serial PRIMARY KEY,
    title text NOT NULL,
    date_at timestamptz NOT NULL,
    email text DEFAULT '',
    notified boolean DEFAULT false
);
"""
)
conn.commit()

def send_mail(receiver, subject, body):
    msg = EmailMessage()
    msg["From"] = "countdown@example.com"
    msg["To"] = receiver or "noreply@example.com"
    msg["Subject"] = subject
    msg.set_content(body)
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as smtp:
        if SMTP_USER:
            smtp.login(SMTP_USER, SMTP_PASS)
        smtp.send_message(msg)

def run_job():
    now = datetime.now(timezone.utc)
    cur.execute(
        """
        SELECT id, title, date_at, email
        FROM events
        WHERE date_at - interval '1 day' < %s
          AND date_at > %s
          AND notified = false
        """,
        (now, now),
    )
    rows = cur.fetchall()
    for row in rows:
        try:
            send_mail(
                row["email"],
                f"Reminder: {row['title']}",
                f"Noch weniger als 24 h bis: {row['title']} ({row['date_at']})",
            )
            cur.execute("UPDATE events SET notified = true WHERE id = %s", (row["id"],))
            conn.commit()
            EMAILS_SENT.inc()
            logging.info(f"sent mail for event {row['id']}")
        except Exception as exc:
            EMAILS_FAILED.inc()
            logging.error(f"mail failed for event {row['id']}: {exc}")

if __name__ == "__main__":
    start_http_server(8000)
    run_job()
