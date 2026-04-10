from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from app.models import Client, Transaction, Document, Task


def calculate_health_score(client_id: int, db: Session) -> str:
    """
    Calculate client health score based on:
    - Document pipeline timeliness
    - Financial data recency
    - Task completion rate
    """
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        return "unknown"

    score = 100
    now = datetime.now(timezone.utc)

    # Recent documents (last 30 days)
    recent_docs = db.query(Document).filter(
        Document.client_id == client_id,
        Document.created_at > now - timedelta(days=30),
    ).count()
    if recent_docs == 0:
        score -= 30

    # Recent transactions (last 60 days)
    recent_txns = db.query(Transaction).filter(
        Transaction.client_id == client_id,
        Transaction.created_at > now - timedelta(days=60),
    ).count()
    if recent_txns == 0:
        score -= 25

    # Overdue tasks
    overdue_tasks = db.query(Task).filter(
        Task.client_id == client_id,
        Task.status.in_(["pending", "in_progress"]),
        Task.due_date < now,
    ).count()
    if overdue_tasks > 0:
        score -= min(20, overdue_tasks * 5)

    if score >= 80:
        return "excellent"
    elif score >= 60:
        return "good"
    elif score >= 40:
        return "fair"
    else:
        return "poor"
