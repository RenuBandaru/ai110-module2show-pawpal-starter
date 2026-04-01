from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional


# ─── PET ────────────────────────────────────────────────────────────────────
# Represents a single pet owned by an Owner.
# Stores all personal details and maintains its own list of Tasks.
# "Task" is quoted because Task is defined after Pet in this file —
# Python resolves forward references like this at runtime.
@dataclass
class Pet:
    name: str
    species: str
    breed: str
    age: int
    weight: float
    owner_id: str                                          # links back to the Owner who owns this pet
    medical_history: list[str] = field(default_factory=list)  # grows over time via add_medical_note()
    tasks: list["Task"] = field(default_factory=list)         # direct task list; also stored in Scheduler

    def get_profile(self) -> str:
        """Return a readable summary string of the pet's name, species, breed, age, and weight."""
        return f"{self.name} ({self.species}, {self.breed}) - Age: {self.age}, Weight: {self.weight}kg"

    def add_medical_note(self, note: str) -> None:
        """Append a new note to the pet's medical history."""
        # (e.g. "Vaccinated 2026-03")
        self.medical_history.append(note)

    def get_age(self) -> int:
        """Return the pet's current age in years."""
        return self.age

    def get_tasks(self) -> list["Task"]:
        """Return all tasks directly attached to this pet."""
        # Tasks are added here when Scheduler.add_task() is called with this pet as an argument
        return self.tasks


# ─── TASK ────────────────────────────────────────────────────────────────────
# Represents a single care activity for a pet (feeding, medication, vet visit, etc.).
# Tracks what needs to be done, when, how often, and whether it's been completed.
@dataclass
class Task:
    task_id: str                       # unique identifier (e.g. "t1") used to find/remove tasks
    type: str                          # category label: "feeding", "grooming", "medication", "vet"
    description: str                   # human-readable detail of what needs to be done
    pet_id: str                        # which pet this task belongs to (matches Pet.name for now)
    owner_id: str                      # which owner is responsible (matches Owner.owner_id)
    due_date: datetime                 # the date and time this task is due
    status: str = "pending"            # lifecycle state: "pending" → "completed"
    recurrence: Optional[str] = None   # how often to repeat: "daily", "weekly", "monthly", or None

    def complete(self) -> None:
        """Mark this task as completed so it no longer appears as overdue."""
        # Marks this task as done — prevents it from appearing as overdue
        self.status = "completed"

    def is_overdue(self) -> bool:
        """Return True if the task is still pending and its due date has passed."""
        # A task is overdue only if it hasn't been completed AND its due datetime has passed.
        # Checking status first ensures completed tasks are never flagged as overdue.
        return self.status != "completed" and self.due_date < datetime.now()

    def reschedule(self, new_date: datetime) -> None:
        """Move the task to a new due date and reset its status to pending."""
        # Moves the task to a new datetime and resets status to "pending"
        # so the task becomes active again (handles missed or rescheduled tasks)
        self.due_date = new_date
        self.status = "pending"

    def get_next_occurrence(self) -> Optional[datetime]:
        """Return the next due date for a recurring task, or None if the task does not recur."""
        # Calculates the next due date for a recurring task by adding the
        # recurrence interval (in days) to the current due_date.
        # Returns None for one-off (non-recurring) tasks.
        intervals: dict[str, int] = {"daily": 1, "weekly": 7, "monthly": 30}
        if self.recurrence in intervals:
            return self.due_date + timedelta(days=intervals[self.recurrence])
        return None


# ─── OWNER ───────────────────────────────────────────────────────────────────
# Represents a pet owner who manages one or more pets.
# Owner is NOT a dataclass because it requires a Scheduler reference at creation time
# and manages a mutable pets list through methods.
class Owner:
    def __init__(self, owner_id: str, name: str, email: str, phone: str, scheduler: "Scheduler"):
        self.owner_id = owner_id
        self.name = name
        self.email = email
        self.phone = phone
        self.pets: list[Pet] = []         # all pets registered to this owner
        self.scheduler = scheduler        # injected reference — Owner queries Scheduler for tasks
                                          # rather than storing tasks itself (single source of truth)

    def add_pet(self, pet: Pet) -> None:
        """Register a new pet under this owner."""
        self.pets.append(pet)

    def remove_pet(self, pet_id: str) -> None:
        """Remove the pet matching pet_id from this owner's pet list."""
        # Rebuilds the pets list excluding the pet whose name matches pet_id
        self.pets = [p for p in self.pets if p.name != pet_id]

    def get_pets(self) -> list[Pet]:
        """Return all pets belonging to this owner."""
        return self.pets

    def schedule_task(self, task: Task, scheduler: "Scheduler") -> None:
        """Delegate adding a task to the Scheduler."""
        # Owner is the entry point; Scheduler is the keeper of all tasks.
        scheduler.add_task(task)

    def get_all_tasks(self) -> list[Task]:
        """Return every task across all of this owner's pets."""
        # Returns every task across all of this owner's pets
        # by filtering the Scheduler's master task list by owner_id
        return [t for t in self.scheduler.tasks if t.owner_id == self.owner_id]

    def get_tasks_for_pet(self, pet_id: str) -> list[Task]:
        """Return all tasks assigned to a specific pet owned by this owner."""
        # Filters by both pet_id and owner_id to avoid cross-owner collisions.
        return [t for t in self.scheduler.tasks if t.pet_id == pet_id and t.owner_id == self.owner_id]


# ─── SCHEDULER ───────────────────────────────────────────────────────────────
# The central coordinator for the entire system.
# Stores all tasks and owners, handles queries, and dispatches reminders.
# No task logic lives here — it delegates behavior back to Task methods (e.g. is_overdue()).
class Scheduler:
    def __init__(self):
        self.tasks: list[Task] = []          # master list of every task across all pets and owners
        self.notifications: list[str] = []   # log of reminder messages sent
        self.owners: dict[str, Owner] = {}   # registry of owners keyed by owner_id for O(1) lookup

    def add_task(self, task: Task, pet: Optional[Pet] = None) -> None:
        """Add a task to the master list and, if provided, to the pet's own task list."""
        # If a Pet object is also provided, the task is added to that pet's own task list too,
        # keeping both lists in sync so pet.get_tasks() works correctly.
        self.tasks.append(task)
        if pet is not None:
            pet.tasks.append(task)

    def remove_task(self, task_id: str) -> None:
        """Remove the task matching task_id from the master task list."""
        # Rebuilds the task list excluding the task with the matching task_id
        self.tasks = [t for t in self.tasks if t.task_id != task_id]

    def get_tasks_for_pet(self, pet_id: str) -> list[Task]:
        """Return all tasks assigned to a specific pet across all owners."""
        return [t for t in self.tasks if t.pet_id == pet_id]

    def get_upcoming_tasks(self, days: int) -> list[Task]:
        """Return tasks due within the next given number of days, sorted by due date."""
        # Sorting ensures the output is always in chronological order regardless
        # of the order tasks were added.
        cutoff = datetime.now() + timedelta(days=days)
        upcoming = [t for t in self.tasks if datetime.now() <= t.due_date <= cutoff]
        return sorted(upcoming, key=lambda t: t.due_date)

    def check_overdue_tasks(self) -> list[Task]:
        """Return all tasks that are past their due date and not yet completed."""
        # Scans all tasks and returns those that are overdue.
        # Delegates the overdue check to Task.is_overdue() so the logic stays on the Task class.
        return [t for t in self.tasks if t.is_overdue()]

    def send_reminder(self, task: Task, owner: Owner) -> None:
        """Build a reminder message for the given task and append it to the notifications log."""
        # In a real app this would trigger an email, push notification, or SMS.
        message = f"Reminder for {owner.name}: '{task.description}' is due on {task.due_date}"
        self.notifications.append(message)
