import pytest
from datetime import date, time, timedelta
from models import (
    TimeWindow, OwnerPreferences, Owner, Pet, PetTask,
    TaskType, ScheduledItem, DailySchedule, SchedulingRules, ScheduleStatus
)
from taskScheduler import TaskScheduler


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_owner(availability=None, quiet_hrs=None, max_activity=180):
    if availability is None:
        availability = [TimeWindow(time(8, 0), time(12, 0))]
    if quiet_hrs is None:
        quiet_hrs = []
    prefs = OwnerPreferences(
        preferred_times=availability,
        quiet_hrs=quiet_hrs,
        max_activity_minutes=max_activity
    )
    return Owner(name="Jordan", availability=availability, preferences=prefs)


def make_pet(rest_blocks=None):
    return Pet(name="Mochi", species="dog", age=2,
               rest_blocks=rest_blocks or [])


def make_task(task_id="t1", title="Walk", duration=20, priority=3,
              mandatory=False, preferred_window=None):
    return PetTask(
        task_id=task_id,
        title=title,
        task_type=TaskType.WALK,
        duration_min=duration,
        priority=priority,
        mandatory=mandatory,
        preferred_window=preferred_window
    )


def make_scheduler():
    return TaskScheduler(SchedulingRules())


# ===========================================================================
# TimeWindow
# ===========================================================================

class TestTimeWindow:
    def test_duration_minutes(self):
        w = TimeWindow(time(8, 0), time(9, 30))
        assert w.duration_minutes() == 90

    def test_contains_true(self):
        outer = TimeWindow(time(8, 0), time(12, 0))
        inner = TimeWindow(time(9, 0), time(10, 0))
        assert outer.contains(inner)

    def test_contains_false(self):
        w1 = TimeWindow(time(8, 0), time(10, 0))
        w2 = TimeWindow(time(9, 0), time(11, 0))
        assert not w1.contains(w2)

    def test_overlaps_true(self):
        w1 = TimeWindow(time(8, 0), time(10, 0))
        w2 = TimeWindow(time(9, 0), time(11, 0))
        assert w1.overlaps(w2)

    def test_overlaps_false_adjacent(self):
        w1 = TimeWindow(time(8, 0), time(9, 0))
        w2 = TimeWindow(time(9, 0), time(10, 0))
        assert not w1.overlaps(w2)

    def test_overlaps_false_disjoint(self):
        w1 = TimeWindow(time(8, 0), time(9, 0))
        w2 = TimeWindow(time(10, 0), time(11, 0))
        assert not w1.overlaps(w2)

    def test_is_working_inside(self):
        w = TimeWindow(time(8, 0), time(12, 0))
        assert w.is_working(time(10, 0))

    def test_is_working_outside(self):
        w = TimeWindow(time(8, 0), time(12, 0))
        assert not w.is_working(time(13, 0))

    def test_is_working_at_start_boundary(self):
        w = TimeWindow(time(8, 0), time(12, 0))
        assert w.is_working(time(8, 0))

    def test_is_working_at_end_boundary(self):
        w = TimeWindow(time(8, 0), time(12, 0))
        assert w.is_working(time(12, 0))

    def test_zero_duration_window(self):
        w = TimeWindow(time(9, 0), time(9, 0))
        assert w.duration_minutes() == 0

    def test_contains_exact_match(self):
        w = TimeWindow(time(8, 0), time(12, 0))
        assert w.contains(TimeWindow(time(8, 0), time(12, 0)))

    def test_contains_sharing_start(self):
        outer = TimeWindow(time(8, 0), time(12, 0))
        inner = TimeWindow(time(8, 0), time(10, 0))
        assert outer.contains(inner)

    def test_contains_sharing_end(self):
        outer = TimeWindow(time(8, 0), time(12, 0))
        inner = TimeWindow(time(10, 0), time(12, 0))
        assert outer.contains(inner)


# ===========================================================================
# OwnerPreferences
# ===========================================================================

class TestOwnerPreferences:
    def test_is_quiet_hour(self):
        prefs = OwnerPreferences(
            preferred_times=[],
            quiet_hrs=[TimeWindow(time(22, 0), time(23, 59))]
        )
        assert prefs.is_quiet_hour(time(23, 0))
        assert not prefs.is_quiet_hour(time(10, 0))

    def test_is_preferred_time(self):
        prefs = OwnerPreferences(
            preferred_times=[TimeWindow(time(9, 0), time(11, 0))],
            quiet_hrs=[]
        )
        assert prefs.is_preferred_time(time(10, 0))
        assert not prefs.is_preferred_time(time(8, 0))

    def test_empty_quiet_hrs(self):
        prefs = OwnerPreferences(preferred_times=[], quiet_hrs=[])
        assert not prefs.is_quiet_hour(time(23, 0))

    def test_empty_preferred_times(self):
        prefs = OwnerPreferences(preferred_times=[], quiet_hrs=[])
        assert not prefs.is_preferred_time(time(10, 0))

    def test_multiple_quiet_hr_ranges(self):
        prefs = OwnerPreferences(
            preferred_times=[],
            quiet_hrs=[
                TimeWindow(time(0, 0), time(7, 0)),
                TimeWindow(time(22, 0), time(23, 59))
            ]
        )
        assert prefs.is_quiet_hour(time(6, 0))
        assert prefs.is_quiet_hour(time(23, 0))
        assert not prefs.is_quiet_hour(time(12, 0))


# ===========================================================================
# Owner
# ===========================================================================

class TestOwner:
    def test_get_available_hours_today(self):
        owner = make_owner(availability=[
            TimeWindow(time(8, 0), time(10, 0)),
            TimeWindow(time(14, 0), time(16, 0))
        ])
        assert owner.get_available_hours_today() == 4

    def test_is_available_at(self):
        owner = make_owner(availability=[TimeWindow(time(8, 0), time(12, 0))])
        assert owner.is_available_at(time(9, 0))
        assert not owner.is_available_at(time(13, 0))

    def test_no_availability_windows(self):
        owner = make_owner(availability=[])
        assert owner.get_available_hours_today() == 0
        assert not owner.is_available_at(time(9, 0))


# ===========================================================================
# Pet
# ===========================================================================

class TestPet:
    def test_is_rest_time(self):
        pet = make_pet(rest_blocks=[TimeWindow(time(13, 0), time(15, 0))])
        assert pet.is_rest_time(time(14, 0))
        assert not pet.is_rest_time(time(10, 0))

    def test_no_rest_blocks(self):
        pet = make_pet(rest_blocks=[])
        assert not pet.is_rest_time(time(14, 0))


# ===========================================================================
# PetTask
# ===========================================================================

class TestPetTask:
    def test_is_overdue_no_last_done(self):
        task = make_task()
        assert task.is_overdue(date.today())

    def test_is_overdue_done_today(self):
        task = make_task()
        task.last_done_date = date.today()
        assert not task.is_overdue(date.today())

    def test_is_overdue_done_yesterday(self):
        task = make_task()
        task.last_done_date = date.today() - timedelta(days=1)
        assert task.is_overdue(date.today())

    def test_fits_in_window_true(self):
        task = make_task(duration=30)
        window = TimeWindow(time(8, 0), time(9, 0))
        assert task.fits_in_window(window)

    def test_fits_in_window_false(self):
        task = make_task(duration=90)
        window = TimeWindow(time(8, 0), time(9, 0))
        assert not task.fits_in_window(window)

    def test_respects_preferred_window_no_preference(self):
        task = make_task()
        assert task.respects_preferred_window(time(8, 0))

    def test_respects_preferred_window_match(self):
        task = make_task(preferred_window=TimeWindow(time(9, 0), time(11, 0)))
        assert task.respects_preferred_window(time(10, 0))
        assert not task.respects_preferred_window(time(8, 0))

    def test_fits_in_window_exact_fit(self):
        task = make_task(duration=60)
        window = TimeWindow(time(8, 0), time(9, 0))
        assert task.fits_in_window(window)

    def test_is_overdue_done_long_ago(self):
        task = make_task()
        task.last_done_date = date.today() - timedelta(days=7)
        assert task.is_overdue(date.today())


# ===========================================================================
# ScheduledItem
# ===========================================================================

class TestScheduledItem:
    def test_duration_minutes(self):
        item = ScheduledItem(task=make_task(), start=time(8, 0), end=time(8, 30))
        assert item.duration_minutes() == 30

    def test_overlaps_with_true(self):
        item1 = ScheduledItem(task=make_task(), start=time(8, 0), end=time(9, 0))
        item2 = ScheduledItem(task=make_task(), start=time(8, 30), end=time(9, 30))
        assert item1.overlaps_with(item2)

    def test_overlaps_with_false(self):
        item1 = ScheduledItem(task=make_task(), start=time(8, 0), end=time(9, 0))
        item2 = ScheduledItem(task=make_task(), start=time(9, 0), end=time(10, 0))
        assert not item1.overlaps_with(item2)

    def test_overlaps_with_self(self):
        item = ScheduledItem(task=make_task(), start=time(8, 0), end=time(9, 0))
        assert item.overlaps_with(item)

    def test_zero_duration_item(self):
        item = ScheduledItem(task=make_task(), start=time(8, 0), end=time(8, 0))
        assert item.duration_minutes() == 0


# ===========================================================================
# DailySchedule
# ===========================================================================

class TestDailySchedule:
    def _make_schedule(self):
        owner = make_owner()
        pet = make_pet()
        schedule = DailySchedule(date=date.today(), owner=owner, pet=pet)
        mandatory_task = make_task(task_id="m1", title="Meds", mandatory=True)
        optional_task = make_task(task_id="o1", title="Walk", mandatory=False)
        schedule.items = [
            ScheduledItem(task=mandatory_task, start=time(8, 0), end=time(8, 20)),
            ScheduledItem(task=optional_task, start=time(9, 0), end=time(9, 20)),
        ]
        return schedule

    def test_total_minutes_scheduled(self):
        schedule = self._make_schedule()
        assert schedule.total_minutes_scheduled() == 40

    def test_get_mandatory_tasks(self):
        schedule = self._make_schedule()
        mandatory = schedule.get_mandatory_tasks()
        assert len(mandatory) == 1
        assert mandatory[0].task.title == "Meds"

    def test_get_optional_tasks(self):
        schedule = self._make_schedule()
        optional = schedule.get_optional_tasks()
        assert len(optional) == 1
        assert optional[0].task.title == "Walk"

    def test_get_unscheduled_tasks(self):
        schedule = self._make_schedule()
        all_tasks = [
            make_task(task_id="m1"),
            make_task(task_id="o1"),
            make_task(task_id="x1", title="Unscheduled"),
        ]
        unscheduled = schedule.get_unscheduled_tasks(all_tasks)
        assert len(unscheduled) == 1
        assert unscheduled[0].task_id == "x1"

    def test_empty_schedule_totals_zero(self):
        schedule = DailySchedule(date=date.today(), owner=make_owner(), pet=make_pet())
        assert schedule.total_minutes_scheduled() == 0
        assert schedule.get_mandatory_tasks() == []
        assert schedule.get_optional_tasks() == []

    def test_all_tasks_scheduled_returns_empty_unscheduled(self):
        schedule = self._make_schedule()
        all_tasks = [make_task(task_id="m1"), make_task(task_id="o1")]
        assert schedule.get_unscheduled_tasks(all_tasks) == []


# ===========================================================================
# SchedulingRules
# ===========================================================================

class TestSchedulingRules:
    def test_calculate_score_mandatory_higher(self):
        rules = SchedulingRules()
        owner = make_owner()
        pet = make_pet()
        high = make_task(priority=5)
        low = make_task(priority=1)
        score_high = rules.calculate_score(high, owner, pet, days_overdue=0)
        score_low = rules.calculate_score(low, owner, pet, days_overdue=0)
        assert score_high > score_low

    def test_calculate_score_overdue_increases_score(self):
        rules = SchedulingRules()
        owner = make_owner()
        pet = make_pet()
        task = make_task(priority=3)
        score_fresh = rules.calculate_score(task, owner, pet, days_overdue=0)
        score_overdue = rules.calculate_score(task, owner, pet, days_overdue=5)
        assert score_overdue > score_fresh


# ===========================================================================
# TaskScheduler
# ===========================================================================

class TestTaskScheduler:
    def test_single_task_scheduled(self):
        scheduler = make_scheduler()
        owner = make_owner(availability=[TimeWindow(time(8, 0), time(12, 0))])
        pet = make_pet()
        tasks = [make_task(task_id="t1", duration=30)]
        schedule = scheduler.generate(owner, pet, tasks, date.today())
        assert len(schedule.items) == 1
        assert schedule.items[0].task.task_id == "t1"

    def test_multiple_tasks_all_fit(self):
        scheduler = make_scheduler()
        owner = make_owner(availability=[TimeWindow(time(8, 0), time(12, 0))])
        pet = make_pet()
        tasks = [
            make_task(task_id="t1", duration=30),
            make_task(task_id="t2", duration=30),
            make_task(task_id="t3", duration=30),
        ]
        schedule = scheduler.generate(owner, pet, tasks, date.today())
        assert len(schedule.items) == 3

    def test_task_too_long_not_scheduled(self):
        scheduler = make_scheduler()
        owner = make_owner(availability=[TimeWindow(time(8, 0), time(8, 10))])
        pet = make_pet()
        tasks = [make_task(task_id="t1", duration=60)]
        schedule = scheduler.generate(owner, pet, tasks, date.today())
        assert len(schedule.items) == 0
        assert any("Could not place" in note for note in schedule.notes)

    def test_no_overlap_between_scheduled_items(self):
        scheduler = make_scheduler()
        owner = make_owner(availability=[TimeWindow(time(8, 0), time(12, 0))])
        pet = make_pet()
        tasks = [
            make_task(task_id=f"t{i}", duration=30)
            for i in range(4)
        ]
        schedule = scheduler.generate(owner, pet, tasks, date.today())
        items = schedule.items
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                assert not items[i].overlaps_with(items[j]), \
                    f"{items[i].task.title} overlaps with {items[j].task.title}"

    def test_pet_rest_block_respected(self):
        scheduler = make_scheduler()
        # Only window: 8–10, pet rests 8–9 → only 9–10 left
        owner = make_owner(availability=[TimeWindow(time(8, 0), time(10, 0))])
        pet = make_pet(rest_blocks=[TimeWindow(time(8, 0), time(9, 0))])
        tasks = [make_task(task_id="t1", duration=30)]
        schedule = scheduler.generate(owner, pet, tasks, date.today())
        assert len(schedule.items) == 1
        assert schedule.items[0].start >= time(9, 0)

    def test_quiet_hours_excluded(self):
        scheduler = make_scheduler()
        # Availability 8–10, quiet 8–9 → only 9–10 free
        owner = make_owner(
            availability=[TimeWindow(time(8, 0), time(10, 0))],
            quiet_hrs=[TimeWindow(time(8, 0), time(9, 0))]
        )
        pet = make_pet()
        tasks = [make_task(task_id="t1", duration=30)]
        schedule = scheduler.generate(owner, pet, tasks, date.today())
        assert len(schedule.items) == 1
        assert schedule.items[0].start >= time(9, 0)

    def test_high_priority_scheduled_before_low(self):
        scheduler = make_scheduler()
        owner = make_owner(availability=[TimeWindow(time(8, 0), time(12, 0))])
        pet = make_pet()
        tasks = [
            make_task(task_id="low", title="Low task", priority=1, duration=30),
            make_task(task_id="high", title="High task", priority=5, duration=30),
        ]
        schedule = scheduler.generate(owner, pet, tasks, date.today())
        scheduled_ids = [item.task.task_id for item in schedule.items]
        assert scheduled_ids.index("high") < scheduled_ids.index("low")

    def test_schedule_notes_contain_summary(self):
        scheduler = make_scheduler()
        owner = make_owner(availability=[TimeWindow(time(8, 0), time(12, 0))])
        pet = make_pet()
        tasks = [make_task(task_id="t1", duration=20)]
        schedule = scheduler.generate(owner, pet, tasks, date.today())
        assert any("Successfully scheduled" in note for note in schedule.notes)

    def test_max_activity_warning(self):
        scheduler = make_scheduler()
        owner = make_owner(
            availability=[TimeWindow(time(8, 0), time(12, 0))],
            max_activity=30
        )
        pet = make_pet()
        # Tasks total 60 min, exceeds max_activity of 30
        tasks = [
            make_task(task_id="t1", duration=20),
            make_task(task_id="t2", duration=20),
            make_task(task_id="t3", duration=20),
        ]
        schedule = scheduler.generate(owner, pet, tasks, date.today())
        assert any("exceeds max activity" in note for note in schedule.notes)

    def test_empty_task_list(self):
        scheduler = make_scheduler()
        owner = make_owner(availability=[TimeWindow(time(8, 0), time(12, 0))])
        pet = make_pet()
        schedule = scheduler.generate(owner, pet, [], date.today())
        assert len(schedule.items) == 0

    def test_no_availability_windows_schedules_nothing(self):
        scheduler = make_scheduler()
        owner = make_owner(availability=[])
        pet = make_pet()
        tasks = [make_task(task_id="t1", duration=20)]
        schedule = scheduler.generate(owner, pet, tasks, date.today())
        assert len(schedule.items) == 0
        assert any("Could not place" in note for note in schedule.notes)

    def test_task_exact_fit_in_window(self):
        scheduler = make_scheduler()
        owner = make_owner(availability=[TimeWindow(time(8, 0), time(8, 30))])
        pet = make_pet()
        tasks = [make_task(task_id="t1", duration=30)]
        schedule = scheduler.generate(owner, pet, tasks, date.today())
        assert len(schedule.items) == 1

    def test_task_placed_in_second_window(self):
        scheduler = make_scheduler()
        owner = make_owner(availability=[
            TimeWindow(time(8, 0), time(8, 10)),   # too small for 30-min task
            TimeWindow(time(14, 0), time(16, 0)),  # fits
        ])
        pet = make_pet()
        tasks = [make_task(task_id="t1", duration=30)]
        schedule = scheduler.generate(owner, pet, tasks, date.today())
        assert len(schedule.items) == 1
        assert schedule.items[0].start >= time(14, 0)

    def test_rest_block_covers_full_availability(self):
        scheduler = make_scheduler()
        owner = make_owner(availability=[TimeWindow(time(8, 0), time(10, 0))])
        pet = make_pet(rest_blocks=[TimeWindow(time(8, 0), time(10, 0))])
        tasks = [make_task(task_id="t1", duration=20)]
        schedule = scheduler.generate(owner, pet, tasks, date.today())
        assert len(schedule.items) == 0

    def test_quiet_hours_cover_full_availability(self):
        scheduler = make_scheduler()
        owner = make_owner(
            availability=[TimeWindow(time(8, 0), time(10, 0))],
            quiet_hrs=[TimeWindow(time(8, 0), time(10, 0))]
        )
        pet = make_pet()
        tasks = [make_task(task_id="t1", duration=20)]
        schedule = scheduler.generate(owner, pet, tasks, date.today())
        assert len(schedule.items) == 0

    def test_tasks_within_availability_window(self):
        scheduler = make_scheduler()
        window = TimeWindow(time(14, 0), time(16, 0))
        owner = make_owner(availability=[window])
        pet = make_pet()
        tasks = [make_task(task_id="t1", duration=30)]
        schedule = scheduler.generate(owner, pet, tasks, date.today())
        assert len(schedule.items) == 1
        item = schedule.items[0]
        assert item.start >= time(14, 0)
        assert item.end <= time(16, 0)
