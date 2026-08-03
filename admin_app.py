from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from database import async_session
from models import User, Test, TestSession, Payment
from sqlalchemy import select, func
import uvicorn

app = FastAPI(title="Test Bot Admin")
templates = Jinja2Templates(directory="templates")

@app.get("/admin/dashboard")
async def dashboard():
    async with async_session() as session:
        users_count = await session.scalar(select(func.count(User.id)))
        tests_count = await session.scalar(select(func.count(Test.id)))
        sessions_count = await session.scalar(select(func.count(TestSession.id)))
        return {
            "users": users_count,
            "tests": tests_count,
            "sessions": sessions_count
        }

@app.get("/admin/tests")
async def list_tests():
    async with async_session() as session:
        result = await session.execute(select(Test))
        tests = result.scalars().all()
        return [{"id": t.id, "title": t.title, "questions": t.question_count, "status": t.status} for t in tests]

@app.get("/admin/users")
async def list_users():
    async with async_session() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()
        return [{"id": u.id, "name": u.full_name, "faculty": u.faculty, "group": u.group_name, "role": u.role} for u in users]

@app.get("/admin/rating")
async def rating():
    async with async_session() as session:
        subq = select(TestSession.user_id, func.sum(TestSession.score).label("total")).where(
            TestSession.status == "completed"
        ).group_by(TestSession.user_id).subquery()
        q = select(User, subq.c.total).join(subq, User.id == subq.c.user_id).order_by(subq.c.total.desc()).limit(50)
        result = await session.execute(q)
        rows = result.all()
        return [{"name": u.full_name, "faculty": u.faculty, "group": u.group_name, "score": score} for u, score in rows]

if __name__ == "__main__":
    uvicorn.run("admin_app:app", host="0.0.0.0", port=8000, reload=True)
