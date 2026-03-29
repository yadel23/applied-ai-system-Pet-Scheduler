# models.py
from dataclasses import dataclass, field
from datetime import date, time
from enum import Enum
from typing import List, Optional

class TaskType(Enum):
    WALK = "walk"
    FEED = "feed"
    MEDS = "meds"
    ENRICHMENT = "enrichment"
    GROOMING = "grooming"

@dataclass
class TimeWindow:
    start: time
    end: time

    def duration_minutes(self): ...
    def contains(self, candidate: "TimeWindow"): ...
    def overlaps(self, candidate: "TimeWindow"): ...

@dataclass
class OwnerPreferences:
    preferred_times: List[TimeWindow]
    quiet_hrs: List[TimeWindow]
    max_activity_minutes: int = 180

@dataclass
class Owner:
    name: str
    availability: List[TimeWindow]
    preferences: OwnerPreferences

@dataclass
class Pet:
    name: str
    species: str
    age: int
    required_daily_tasks: dict = field(default_factory=dict)

@dataclass
class PetTask:
    title: str
    task_type: TaskType
    duration_min: int
    priority: int
    mandatory: bool = False
    preferred_window: Optional[TimeWindow] = None
    frequency: str = "daily"

@dataclass
class ScheduledItem:
    task: PetTask
    start: time
    end: time
    reason: str
    status: str = "planned"

@dataclass
class DailySchedule:
    date: date
    owner: Owner
    pet: Pet
    items: List[ScheduledItem] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)