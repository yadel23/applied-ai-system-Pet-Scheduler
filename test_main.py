from pawpal_system import Owner, Pet, Task, Scheduler


# ===========================================================================
# Task.mark_complete()
# ===========================================================================

class TestMarkComplete:
    def test_task_starts_incomplete(self):
        task = Task(title="Morning walk", duration_minutes=30, priority="high")
        assert task.completed is False

    def test_mark_complete_sets_flag(self):
        task = Task(title="Morning walk", duration_minutes=30, priority="high")
        task.mark_complete()
        assert task.completed is True

    def test_mark_complete_is_idempotent(self):
        task = Task(title="Morning walk", duration_minutes=30, priority="high")
        task.mark_complete()
        task.mark_complete()
        assert task.completed is True

    def test_completing_one_task_does_not_affect_another(self):
        task_a = Task(title="Walk", duration_minutes=20, priority="high")
        task_b = Task(title="Feed", duration_minutes=10, priority="medium")
        task_a.mark_complete()
        assert task_b.completed is False


# ===========================================================================
# Pet.add_task() — task count
# ===========================================================================

class TestPetAddTask:
    def test_new_pet_has_no_tasks(self):
        pet = Pet(name="Mochi", species="dog")
        assert len(pet.tasks) == 0

    def test_add_single_task_increases_count(self):
        pet = Pet(name="Mochi", species="dog")
        pet.add_task(Task(title="Walk", duration_minutes=20, priority="high"))
        assert len(pet.tasks) == 1

    def test_add_multiple_tasks_increases_count(self):
        pet = Pet(name="Mochi", species="dog")
        pet.add_task(Task(title="Walk",  duration_minutes=20, priority="high"))
        pet.add_task(Task(title="Feed",  duration_minutes=10, priority="high"))
        pet.add_task(Task(title="Groom", duration_minutes=15, priority="medium"))
        assert len(pet.tasks) == 3

    def test_completed_task_still_counted_in_tasks(self):
        pet = Pet(name="Mochi", species="dog")
        task = Task(title="Walk", duration_minutes=20, priority="high")
        task.mark_complete()
        pet.add_task(task)
        assert len(pet.tasks) == 1

    def test_completed_task_excluded_from_pending(self):
        pet = Pet(name="Mochi", species="dog")
        task = Task(title="Walk", duration_minutes=20, priority="high")
        task.mark_complete()
        pet.add_task(task)
        assert len(pet.get_pending_tasks()) == 0


# ===========================================================================
# Integration — mark_complete() removes task from schedule
# ===========================================================================

class TestMarkCompleteUpdatesSchedule:
    def _make_owner_with_pet(self, pet):
        owner = Owner(
            name="Jordan",
            availability_windows=[{"start": "08:00", "end": "12:00"}]
        )
        owner.add_pet(pet)
        return owner

    def test_completed_task_not_in_schedule(self):
        pet = Pet(name="Mochi", species="dog")
        walk = Task(title="Morning walk", duration_minutes=30, priority="high")
        feed = Task(title="Feed breakfast", duration_minutes=10, priority="high")
        pet.add_task(walk)
        pet.add_task(feed)

        walk.mark_complete()
        owner = self._make_owner_with_pet(pet)
        schedule = Scheduler(owner).run()

        titles = [item.task.title for item in schedule.items]
        assert "Morning walk" not in titles
        assert "Feed breakfast" in titles

    def test_all_completed_produces_empty_schedule(self):
        pet = Pet(name="Mochi", species="dog")
        tasks = [
            Task(title="Walk",  duration_minutes=20, priority="high"),
            Task(title="Feed",  duration_minutes=10, priority="medium"),
            Task(title="Groom", duration_minutes=15, priority="low"),
        ]
        for t in tasks:
            pet.add_task(t)
            t.mark_complete()

        owner = self._make_owner_with_pet(pet)
        schedule = Scheduler(owner).run()
        assert len(schedule.items) == 0

    def test_completing_task_via_pet_complete_task(self):
        pet = Pet(name="Mochi", species="dog")
        pet.add_task(Task(title="Walk", duration_minutes=20, priority="high"))
        pet.add_task(Task(title="Feed", duration_minutes=10, priority="medium"))

        pet.complete_task("Walk")
        owner = self._make_owner_with_pet(pet)
        schedule = Scheduler(owner).run()

        titles = [item.task.title for item in schedule.items]
        assert "Walk" not in titles
        assert "Feed" in titles
