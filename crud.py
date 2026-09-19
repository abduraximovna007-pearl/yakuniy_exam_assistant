from sqlalchemy import select, func
from database import async_session
from models import User, Test, Question, TestSession, Payment
import random
from datetime import datetime, timezone

async def get_user(telegram_id: int) -> User | None:
    async with async_session() as session:
        return await session.scalar(select(User).where(User.telegram_id == telegram_id))

async def create_user(telegram_id: int, full_name: str, faculty: str, group_name: str) -> User:
    async with async_session() as session:
        user = User(telegram_id=telegram_id, full_name=full_name, faculty=faculty, group_name=group_name)
        session.add(user)
        await session.commit()
        return user

async def check_test_exists(title: str) -> Test | None:
    # Kengaytmani olib tashlash (Dinshunoslik.docx -> Dinshunoslik)
    clean_title = title.replace('.docx', '').replace('.txt', '').strip()
    async with async_session() as session:
        # Kengaytmasiz va kengaytmali ikkalasini ham tekshirish
        result = await session.scalar(
            select(Test).where(
                Test.status == 'approved',
                Test.title.in_([clean_title, clean_title + '.docx', clean_title + '.txt'])
            )
        )
        return result

async def create_test(title: str, price: int, uploaded_by: int, file_path: str = "") -> Test:
    async with async_session() as session:
        test = Test(title=title, price=price, uploaded_by=uploaded_by, file_path=file_path)
        session.add(test)
        await session.commit()
        await session.refresh(test)
        return test

async def save_questions(test_id: int, questions_data: list[dict]) -> int:
    async with async_session() as session:
        for q in questions_data:
            question = Question(test_id=test_id, **q)
            session.add(question)
        await session.commit()
        return len(questions_data)

async def approve_test(test_id: int, question_count: int = 0):
    async with async_session() as session:
        test = await session.get(Test, test_id)
        if test:
            test.status = 'approved'
            test.question_count = question_count
            await session.commit()

async def reject_test(test_id: int):
    async with async_session() as session:
        test = await session.get(Test, test_id)
        if test:
            test.status = 'rejected'
            await session.commit()

async def get_approved_tests() -> list[Test]:
    async with async_session() as session:
        result = await session.execute(
            select(Test).where(Test.status == 'approved', Test.question_count > 0)
        )
        return list(result.scalars().all())

async def get_test_questions(test_id: int, count: int = 25) -> list[Question]:
    async with async_session() as session:
        result = await session.execute(select(Question).where(Question.test_id == test_id))
        questions = list(result.scalars().all())
        return random.sample(questions, min(count, len(questions)))

async def create_session(user_id: int, test_id: int, questions_order: list) -> TestSession:
    async with async_session() as session:
        ts = TestSession(user_id=user_id, test_id=test_id, questions_order=questions_order, total=len(questions_order))
        session.add(ts)
        await session.commit()
        await session.refresh(ts)
        return ts

async def update_session_answer(session_id: int, q_index: int, answer: str):
    async with async_session() as session:
        ts = await session.get(TestSession, session_id)
        if ts:
            answers = dict(ts.answers) if ts.answers else {}
            answers[str(q_index)] = answer
            ts.answers = answers
            await session.commit()

async def complete_session(session_id: int) -> tuple[int, int, int]:
    async with async_session() as session:
        ts = await session.get(TestSession, session_id)
        if not ts:
            return 0, 0, 0
        score = 0
        questions = ts.questions_order
        answers = ts.answers or {}
        for q_id, ans in answers.items():
            idx = int(q_id)
            if 0 <= idx < len(questions):
                q = await session.get(Question, questions[idx])
                if q and ans == q.correct_answer:
                    score += 1
        ts.score = score
        ts.status = 'completed'
        ts.completed_at = datetime.now(timezone.utc)
        await session.commit()
        return score, len(answers), ts.total

async def create_payment(user_id: int, test_id: int, screenshot: str, amount: int) -> Payment:
    async with async_session() as session:
        p = Payment(user_id=user_id, test_id=test_id, screenshot_file_id=screenshot, amount=amount)
        session.add(p)
        await session.commit()
        await session.refresh(p)
        return p

async def get_rating(faculty: str, group_name: str) -> list[tuple]:
    async with async_session() as session:
        subq = select(TestSession.user_id, func.sum(TestSession.score).label('total_score')).where(
            TestSession.status == 'completed'
        ).group_by(TestSession.user_id).subquery()
        q = select(User, subq.c.total_score).join(subq, User.id == subq.c.user_id).where(
            User.faculty == faculty, User.group_name == group_name
        ).order_by(subq.c.total_score.desc()).limit(20)
        result = await session.execute(q)
        return list(result.all())

async def get_global_rating(limit: int = 50) -> list[tuple]:
    async with async_session() as session:
        subq = select(TestSession.user_id, func.sum(TestSession.score).label('total_score')).where(
            TestSession.status == 'completed'
        ).group_by(TestSession.user_id).subquery()
        q = select(User, subq.c.total_score).join(
            subq, User.id == subq.c.user_id
        ).order_by(subq.c.total_score.desc()).limit(limit)
        result = await session.execute(q)
        return list(result.all())

async def get_user_scores(user_id: int) -> int:
    async with async_session() as session:
        result = await session.execute(
            select(func.coalesce(func.sum(TestSession.score), 0)).where(
                TestSession.user_id == user_id, TestSession.status == 'completed'
            )
        )
        return result.scalar()

async def get_pending_test(test_id: int) -> Test | None:
    async with async_session() as session:
        return await session.get(Test, test_id)

async def get_test_participants(test_id: int) -> list[tuple[TestSession, User]]:
    async with async_session() as session:
        q = select(TestSession, User).join(
            User, TestSession.user_id == User.id
        ).where(
            TestSession.test_id == test_id,
            TestSession.status == 'completed'
        ).order_by(TestSession.completed_at.desc())
        result = await session.execute(q)
        return list(result.all())

async def get_recent_completed_sessions(limit: int = 30) -> list[tuple[TestSession, User, Test]]:
    async with async_session() as session:
        q = select(TestSession, User, Test).join(
            User, TestSession.user_id == User.id
        ).join(
            Test, TestSession.test_id == Test.id
        ).where(
            TestSession.status == 'completed'
        ).order_by(TestSession.completed_at.desc()).limit(limit)
        result = await session.execute(q)
        return list(result.all())

async def get_tests_with_stats() -> list[dict]:
    async with async_session() as session:
        result = await session.execute(
            select(Test).where(Test.status == 'approved')
        )
        tests = list(result.scalars().all())
        data = []
        for t in tests:
            count = await session.scalar(
                select(func.count(TestSession.id)).where(
                    TestSession.test_id == t.id,
                    TestSession.status == 'completed'
                )
            )
            data.append({
                "test": t,
                "participants_count": count or 0
            })
        return data

async def get_system_stats() -> dict:
    async with async_session() as session:
        users_count = await session.scalar(select(func.count(User.id)))
        tests_count = await session.scalar(select(func.count(Test.id)).where(Test.status == 'approved'))
        sessions_count = await session.scalar(select(func.count(TestSession.id)).where(TestSession.status == 'completed'))
        questions_count = await session.scalar(select(func.count(Question.id)))
        return {
            "users": users_count or 0,
            "tests": tests_count or 0,
            "sessions": sessions_count or 0,
            "questions": questions_count or 0,
        }

async def get_user_completed_sessions(user_id: int, limit: int = 20) -> list[tuple[TestSession, Test]]:
    async with async_session() as session:
        q = select(TestSession, Test).join(
            Test, TestSession.test_id == Test.id
        ).where(
            TestSession.user_id == user_id,
            TestSession.status == 'completed'
        ).order_by(TestSession.completed_at.desc()).limit(limit)
        result = await session.execute(q)
        return list(result.all())


