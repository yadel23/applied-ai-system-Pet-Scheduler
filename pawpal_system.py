from datetime import date, time
from typing import List, Optional
from models import (
    Owner as OwnerModel, Pet as PetModel, PetTask, TaskType, TimeWindow,
    OwnerPreferences, SchedulingRules, DailySchedule
)
from taskScheduler import TaskScheduler


PRIORITY_MAP = {"low": 1, "medium": 3, "high": 5}


class Task:
    """Represents a single pet care activity."""

    def __init__(self, title: str, duration_minutes: int, priority: str,
                 frequency: str = "daily", completed: bool = False):
        self.title = title
        self.duration_minutes = duration_minutes
        self.priority = priority          # "low", "medium", "high"
        self.frequency = frequency
        self.completed = completed

    def mark_complete(self):
        self.completed = True

    def _resolve_task_type(self) -> TaskType:
        title_lower = self.title.lower()
        if "feed" in title_lower:
            return TaskType.FEED
        if "med" in title_lower:
            return TaskType.MEDS
        return TaskType.WALK

    def to_pet_task(self, task_id: str) -> PetTask:
        return PetTask(
            task_id=task_id,
            title=self.title,
            task_type=self._resolve_task_type(),
            duration_min=self.duration_minutes,
            priority=PRIORITY_MAP[self.priority],
            mandatory=self.priority == "high",
            frequency=self.frequency,
            completed_today=self.completed
        )


class Pet:
    """Stores pet details and a list of tasks."""

    def __init__(self, name: str, species: str, age: int = 2):
        self.name = name
        self.species = species
        self.age = age
        self.tasks: List[Task] = []

    def add_task(self, task: Task):
        self.tasks.append(task)

    def get_pending_tasks(self) -> List[Task]:
        return [t for t in self.tasks if not t.completed]

    def to_pet_model(self) -> PetModel:
        return PetModel(name=self.name, species=self.species, age=self.age)


class Owner:
    """Manages multiple pets and provides access to all their tasks."""

    def __init__(self, name: str, availability_windows: List[dict],
                 max_activity_minutes: int = 180):
        self.name = name
        self.availability_windows = availability_windows
        self.max_activity_minutes = max_activity_minutes
        self.pets: List[Pet] = []

    def add_pet(self, pet: Pet):
        self.pets.append(pet)

    def get_all_tasks(self) -> List[Task]:
        return [task for pet in self.pets for task in pet.tasks]

    def _build_availability(self) -> List[TimeWindow]:
        return [
            TimeWindow(
                time.fromisoformat(w["start"]),
                time.fromisoformat(w["end"])
            )
            for w in self.availability_windows
        ]

    def to_owner_model(self) -> OwnerModel:
        availability = self._build_availability()
        preferences = OwnerPreferences(
            preferred_times=availability,
            quiet_hrs=[TimeWindow(time(23, 0), time(7, 0))],
            max_activity_minutes=self.max_activity_minutes
        )
        return OwnerModel(name=self.name, availability=availability,
                          preferences=preferences)


class Scheduler:
    """The brain that retrieves, organizes, and manages tasks across pets."""

    def __init__(self, owner: Owner):
        self.owner = owner

    def run(self) -> DailySchedule:
        owner_model = self.owner.to_owner_model()
        # Collect all pets and their tasks; use the first pet for the schedule
        # (single-pet scheduling — consistent with existing app behaviour)
        pet = self.owner.pets[0] if self.owner.pets else Pet("", "")
        pet_model = pet.to_pet_model()
        pet_tasks = [
            task.to_pet_task(f"task_{i}")
            for i, task in enumerate(pet.tasks)
        ]
        scheduler = TaskScheduler(SchedulingRules())
        return scheduler.generate(owner_model, pet_model, pet_tasks, date.today())


# ---------------------------------------------------------------------------
# Public entry point called by app.py (interface unchanged)
# ---------------------------------------------------------------------------

def generate_schedule(
    owner_name: str,
    pet_name: str,
    species: str,
    availability_windows: List[dict],
    max_activity_minutes: int,
    task_dicts: List[dict]
) -> DailySchedule:
    pet = Pet(name=pet_name, species=species)
    for task_dict in task_dicts:
        pet.add_task(Task(
            title=task_dict["title"],
            duration_minutes=task_dict["duration_minutes"],
            priority=task_dict["priority"]
        ))

    owner = Owner(
        name=owner_name,
        availability_windows=availability_windows,
        max_activity_minutes=max_activity_minutes
    )
    owner.add_pet(pet)

    return Scheduler(owner).run()
