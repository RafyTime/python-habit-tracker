"""Database seeding service for test data."""

from collections.abc import Callable
from datetime import datetime, timedelta

from sqlmodel import Session

from src.core.db import engine
from src.core.habit.service import HabitService
from src.core.habit.errors import HabitAlreadyExists, HabitAlreadyCompletedForPeriod
from src.core.models import Periodicity
from src.core.profile.service import ProfileService
from src.core.profile.errors import ProfileAlreadyExists
from src.core.xp.service import XPService


def seed_db(progress_callback: Callable[[str], None] | None = None) -> None:
    """
    Seed the database with test data for evaluation purposes.
    
    Creates two profiles (Primary and Test) with habits and completion records
    that demonstrate various edge cases including streaks, broken streaks, and milestones.
    """
    def _emit(message: str) -> None:
        if progress_callback:
            progress_callback(message)

    with Session(engine) as session:
        session_factory = lambda: iter([session])

        # Initialize services
        profile_service = ProfileService(session_factory)
        xp_service = XPService(session_factory)
        habit_service = HabitService(session_factory, xp_service=xp_service)
    
        # Get or create Primary profile
        _emit('Ensuring profiles exist...')
        try:
            primary_profile = profile_service.create_profile('Primary')
        except ProfileAlreadyExists:
            profiles = profile_service.list_profiles()
            primary_profile = next((p for p in profiles if p.username == 'primary'), None)
            if not primary_profile:
                raise RuntimeError('Primary profile should exist but was not found')

        # Get or create Test profile
        try:
            _ = profile_service.create_profile('Test')
        except ProfileAlreadyExists:
            profiles = profile_service.list_profiles()
            if not next((p for p in profiles if p.username == 'test'), None):
                raise RuntimeError('Test profile should exist but was not found')

        # Set Primary as active profile for seeding
        profile_service.switch_active_profile('Primary')
        now = datetime.now()

        # ===== PRIMARY PROFILE HABITS =====
        _emit('Seeding Primary: Morning Hydration (28-day streak)...')
        try:
            hydration_habit = habit_service.create_habit(
                'Morning Hydration', Periodicity.DAILY
            )
        except HabitAlreadyExists:
            habits = habit_service.list_habits(active_only=False)
            hydration_habit = next((h for h in habits if h.name == 'Morning Hydration'), None)
            if not hydration_habit:
                raise RuntimeError('Could not find existing Morning Hydration habit')

        for day_offset in range(27, -1, -1):
            completion_date = now - timedelta(days=day_offset)
            try:
                habit_service.complete_habit(hydration_habit.id, when=completion_date)
            except HabitAlreadyCompletedForPeriod:
                pass

        _emit('Seeding Primary: Gym Session (weekly consistency)...')
        try:
            gym_habit = habit_service.create_habit('Gym Session', Periodicity.WEEKLY)
        except HabitAlreadyExists:
            habits = habit_service.list_habits(active_only=False)
            gym_habit = next((h for h in habits if h.name == 'Gym Session'), None)
            if not gym_habit:
                raise RuntimeError('Could not find existing Gym Session habit')

        for week_offset in range(3, -1, -1):
            target_date = now - timedelta(weeks=week_offset)
            monday_date = target_date - timedelta(days=target_date.weekday())
            try:
                habit_service.complete_habit(gym_habit.id, when=monday_date)
            except HabitAlreadyCompletedForPeriod:
                pass

        _emit('Seeding Primary: Read 10 Pages (broken streak)...')
        try:
            read_habit = habit_service.create_habit('Read 10 Pages', Periodicity.DAILY)
        except HabitAlreadyExists:
            habits = habit_service.list_habits(active_only=False)
            read_habit = next((h for h in habits if h.name == 'Read 10 Pages'), None)
            if not read_habit:
                raise RuntimeError('Could not find existing Read 10 Pages habit')

        for day_offset in range(17, 7, -1):
            completion_date = now - timedelta(days=day_offset)
            try:
                habit_service.complete_habit(read_habit.id, when=completion_date)
            except HabitAlreadyCompletedForPeriod:
                pass

        # Restart segment after two-day gap.
        for day_offset in range(4, -1, -1):
            completion_date = now - timedelta(days=day_offset)
            try:
                habit_service.complete_habit(read_habit.id, when=completion_date)
            except HabitAlreadyCompletedForPeriod:
                pass

        _emit('Seeding Primary: Code Practice (milestones 7/14)...')
        try:
            code_habit = habit_service.create_habit('Code Practice', Periodicity.DAILY)
        except HabitAlreadyExists:
            habits = habit_service.list_habits(active_only=False)
            code_habit = next((h for h in habits if h.name == 'Code Practice'), None)
            if not code_habit:
                raise RuntimeError('Could not find existing Code Practice habit')

        for day_offset in range(13, -1, -1):
            completion_date = now - timedelta(days=day_offset)
            try:
                habit_service.complete_habit(code_habit.id, when=completion_date)
            except HabitAlreadyCompletedForPeriod:
                pass

        _emit('Seeding Primary: Clean Apartment (weekly edge case)...')
        try:
            clean_habit = habit_service.create_habit('Clean Apartment', Periodicity.WEEKLY)
        except HabitAlreadyExists:
            habits = habit_service.list_habits(active_only=False)
            clean_habit = next((h for h in habits if h.name == 'Clean Apartment'), None)
            if not clean_habit:
                raise RuntimeError('Could not find existing Clean Apartment habit')

        week2_monday = now - timedelta(days=now.weekday())
        week1_sunday = week2_monday - timedelta(days=1)
        try:
            habit_service.complete_habit(clean_habit.id, when=week1_sunday)
        except HabitAlreadyCompletedForPeriod:
            pass
        try:
            habit_service.complete_habit(clean_habit.id, when=week2_monday)
        except HabitAlreadyCompletedForPeriod:
            pass

        # ===== TEST PROFILE HABITS =====
        _emit('Seeding Test profile habits...')
        profile_service.switch_active_profile('Test')

        try:
            test_habit_1 = habit_service.create_habit('Test Habit Daily', Periodicity.DAILY)
            for day_offset in range(2, -1, -1):
                completion_date = now - timedelta(days=day_offset)
                try:
                    habit_service.complete_habit(test_habit_1.id, when=completion_date)
                except HabitAlreadyCompletedForPeriod:
                    pass
        except HabitAlreadyExists:
            pass

        try:
            test_habit_2 = habit_service.create_habit('Test Habit Weekly', Periodicity.WEEKLY)
            this_monday = now - timedelta(days=now.weekday())
            try:
                habit_service.complete_habit(test_habit_2.id, when=this_monday)
            except HabitAlreadyCompletedForPeriod:
                pass
        except HabitAlreadyExists:
            pass

        profile_service.switch_active_profile('Primary')
        _emit('Finalizing seed...')
