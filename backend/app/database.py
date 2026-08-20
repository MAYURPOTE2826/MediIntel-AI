import time
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.engine import Engine

db = SQLAlchemy()

# Note: We must import the metric inside the event listener to avoid circular imports if needed, 
# but it's safe here since we'll import it directly.
from app.monitoring import db_query_latency_histogram

@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    conn.info.setdefault('query_start_time', []).append(time.time())

@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    query_type = statement.split()[0].upper() if statement else "UNKNOWN"
    start_time = conn.info['query_start_time'].pop(-1)
    latency = time.time() - start_time
    db_query_latency_histogram.labels(query_type=query_type).observe(latency)
