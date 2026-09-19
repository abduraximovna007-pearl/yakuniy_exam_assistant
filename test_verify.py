import asyncio
from crud import get_tests_with_stats, get_recent_completed_sessions, get_global_rating, get_system_stats, get_test_participants

async def main():
    stats = await get_system_stats()
    print("SYSTEM STATS:", stats)

    tests_stats = await get_tests_with_stats()
    print(f"OPEN TESTS ({len(tests_stats)}):")
    for item in tests_stats:
        t = item["test"]
        count = item["participants_count"]
        print(f" - Test #{t.id} '{t.title}': {count} participants")
        participants = await get_test_participants(t.id)
        for ts, u in participants[:3]:
            print(f"    * Student: {u.full_name} ({u.faculty}, {u.group_name}) -> Score: {ts.score}/{ts.total}")

    recent = await get_recent_completed_sessions(5)
    print(f"RECENT COMPLETED SESSIONS ({len(recent)}):")
    for ts, u, t in recent:
        print(f" - {u.full_name} completed '{t.title}' -> {ts.score}/{ts.total}")

    ratings = await get_global_rating(5)
    print(f"GLOBAL RATINGS ({len(ratings)}):")
    for u, score in ratings:
        print(f" - {u.full_name} ({u.faculty}, {u.group_name}): {score} points")

if __name__ == "__main__":
    asyncio.run(main())
