import os
from datetime import datetime, timezone

import psycopg2
import psycopg2.extras
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from prometheus_client import Counter, start_http_server

REQUESTS = Counter("api_requests_total", "API requests")
start_http_server(8001)

app = FastAPI()

conn = psycopg2.connect(
    host=os.environ["DB_HOST"],
    user="postgres",
    password=os.environ["DB_PASS"],
    dbname="events",
)
cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
cur.execute(
    """
CREATE TABLE IF NOT EXISTS events (
    id serial PRIMARY KEY,
    title text NOT NULL,
    date_at timestamptz NOT NULL,
    email text NOT NULL,
    notified boolean DEFAULT false
);
"""
)
conn.commit()


class EventIn(BaseModel):
    title: str
    date: str
    email: str


@app.middleware("http")
async def count_requests(request, call_next):
    REQUESTS.inc()
    return await call_next(request)


@app.get("/events")
def list_events():
    cur.execute(
        "SELECT id, title, date_at AS date, email FROM events ORDER BY date_at;"
    )
    return [dict(r) for r in cur.fetchall()]


@app.post("/events")
def add_event(e: EventIn):
    cur.execute(
        "INSERT INTO events (title, date_at, email) VALUES (%s, %s, %s)",
        (
            e.title,
            datetime.fromisoformat(e.date).astimezone(timezone.utc),
            e.email,
        ),
    )
    conn.commit()
    return {"status": "ok"}


@app.delete("/events/{event_id}")
def delete_event(event_id: int):
    cur.execute("DELETE FROM events WHERE id = %s RETURNING id;", (event_id,))
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Event not found")
    conn.commit()
    return {"status": "deleted"}
