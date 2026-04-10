from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.auth.middleware import get_current_user, MultiTenantContext, security
from app.models import Task
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse
from typing import Optional

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskResponse])
async def list_tasks(
    status: Optional[str] = Query(None),
    client_id: Optional[int] = Query(None),
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """List tasks with optional filters."""
    ctx = await get_current_user(credentials)
    query = db.query(Task).filter(Task.agency_id == ctx.agency_id)

    if status:
        query = query.filter(Task.status == status)
    if client_id:
        query = query.filter(Task.client_id == client_id)

    return query.order_by(Task.created_at.desc()).all()


@router.post("", response_model=TaskResponse, status_code=201)
async def create_task(
    task_data: TaskCreate,
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Create new task."""
    ctx = await get_current_user(credentials)
    task = Task(
        agency_id=ctx.agency_id,
        title=task_data.title,
        description=task_data.description,
        client_id=task_data.client_id,
        priority=task_data.priority,
        due_date=task_data.due_date,
        status="pending",
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_data: TaskUpdate,
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Update a task."""
    ctx = await get_current_user(credentials)
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.agency_id == ctx.agency_id,
    ).first()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    for field, value in task_data.model_dump(exclude_unset=True).items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)
    return task
