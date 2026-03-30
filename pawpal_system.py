from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass
class Pet:
    name: str
    species: str
    breed: str
    age: int
    weight: float
    owner_id: str
    medical_history: list[str] = field(default_factory=list)

    def get_profile(self) -> str: ...

    def add_medical_note(self, note: str) -> None: ...

    def get_age(self) -> int: ...


@dataclass
class Task:
    task_id: str
    type: str
    description: str
    pet_id: str
    due_date: date
    status: str = "pending"
    recurrence: Optional[str] = None

    def complete(self) -> None: ...

    def is_overdue(self) -> bool: ...

    def reschedule(self, new_date: date) -> None: ...

    def get_next_occurrence(self) -> Optional[date]: ...


class Owner:
    def __init__(self, name: str, email: str, phone: str):
        self.name = name
        self.email = email
        self.phone = phone
        self.pets: list[Pet] = []

    def add_pet(self, pet: Pet) -> None: ...

    def remove_pet(self, pet_id: str) -> None: ...

    def get_pets(self) -> list[Pet]: ...

    def schedule_task(self, task: Task, scheduler: "Scheduler") -> None: ...


class Scheduler:
    def __init__(self):
        self.tasks: list[Task] = []
        self.notifications: list[str] = []

    def add_task(self, task: Task) -> None: ...

    def remove_task(self, task_id: str) -> None: ...

    def get_tasks_for_pet(self, pet_id: str) -> list[Task]: ...

    def get_upcoming_tasks(self, days: int) -> list[Task]: ...

    def check_overdue_tasks(self) -> list[Task]: ...

    def send_reminder(self, task: Task, owner: Owner) -> None: ...
