import pytest
from datetime import datetime, timedelta
from pawpal_system import Pet, Task, Scheduler


# Creates a fresh Scheduler instance for each test that requests it
@pytest.fixture
def scheduler():
    return Scheduler()


# Creates a sample Pet named "Buddy" for use in tests
@pytest.fixture
def pet():
    return Pet(name="Buddy", species="Dog", breed="Labrador", age=3, weight=30.0, owner_id="o1")


# Creates a second pet owned by the same owner (used for cross-pet conflict tests)
@pytest.fixture
def pet2():
    return Pet(name="Luna", species="Cat", breed="Siamese", age=2, weight=4.0, owner_id="o1")


# Creates a sample feeding Task linked to Buddy, due tomorrow
@pytest.fixture
def task(pet):
    return Task(
        task_id="t1",
        type="feeding",
        description="Feed Buddy",
        pet_id=pet.name,   # links the task to Buddy by name
        owner_id="o1",
        due_date=datetime.now() + timedelta(days=1),  # due tomorrow so it's not overdue
    )


# Task Completion: Verify that calling complete() changes the task's status to "completed"
def test_mark_complete_changes_status(task):
    # A new task should always start in the "pending" state
    assert task.status == "pending"

    # Marking the task complete should update its status
    task.complete()

    # Status must now reflect "completed", not "pending"
    assert task.status == "completed"


# Task Addition: Verify that adding a task to a Pet increases that pet's task count
def test_add_task_increases_pet_task_count(scheduler, pet, task):
    # Record how many tasks Buddy has before adding anything (should be 0)
    initial_count = len(pet.get_tasks())

    # Add the task through the Scheduler, passing the pet so both lists stay in sync
    scheduler.add_task(task, pet)

    # Buddy's task list should now have exactly one more task than before
    assert len(pet.get_tasks()) == initial_count + 1


# ─── SORTING CORRECTNESS ─────────────────────────────────────────────────────

# Happy path: three tasks added out of order — get_upcoming_tasks() must return them
# sorted chronologically (earliest due_date first).
def test_upcoming_tasks_sorted_chronologically(scheduler, pet):
    now = datetime.now()
    t_day3 = Task("s1", "feeding",   "Feed Buddy day 3", pet.name, "o1", now + timedelta(days=3))
    t_day1 = Task("s2", "grooming",  "Groom Buddy day 1", pet.name, "o1", now + timedelta(days=1))
    t_day2 = Task("s3", "vet",       "Vet visit day 2",   pet.name, "o1", now + timedelta(days=2))

    # Add tasks in the wrong order to confirm sorting is not insertion-order dependent
    for t in [t_day3, t_day1, t_day2]:
        scheduler.add_task(t, pet)

    result = scheduler.get_upcoming_tasks(days=7)
    due_dates = [t.due_date for t in result]

    # Each date must be <= the next — strictly ascending (or equal) chronological order
    assert due_dates == sorted(due_dates), "Tasks must be returned in chronological order"


# Edge case: two tasks scheduled at the exact same time for the same pet.
# The more medically urgent type (medication, priority 0) must appear before
# grooming (priority 4) because the secondary sort key is the PRIORITY rank.
def test_same_time_tasks_sorted_by_medical_priority(scheduler, pet):
    now = datetime.now()
    same_time = now + timedelta(hours=2)

    t_grooming   = Task("p1", "grooming",   "Groom Buddy",     pet.name, "o1", same_time)
    t_medication = Task("p2", "medication", "Give medication",  pet.name, "o1", same_time)
    t_feeding    = Task("p3", "feeding",    "Feed Buddy",       pet.name, "o1", same_time)

    for t in [t_grooming, t_medication, t_feeding]:
        scheduler.add_task(t, pet)

    result = scheduler.get_upcoming_tasks(days=1)

    # Filter to only the same-time tasks we added (scheduler may have other tasks)
    same_time_tasks = [t for t in result if t.due_date == same_time]
    task_types = [t.type for t in same_time_tasks]

    # medication(0) → feeding(2) → grooming(4)
    assert task_types == ["medication", "feeding", "grooming"], (
        f"Expected priority order [medication, feeding, grooming], got {task_types}"
    )


# Edge case: a task with an unknown type should sort after all known types
# (falls back to priority rank 99) without raising an exception.
def test_unknown_task_type_sorts_last(scheduler, pet):
    now = datetime.now()
    same_time = now + timedelta(hours=1)

    t_known   = Task("u1", "medication", "Give meds",   pet.name, "o1", same_time)
    t_unknown = Task("u2", "bath",       "Give a bath",  pet.name, "o1", same_time)

    scheduler.add_task(t_known, pet)
    scheduler.add_task(t_unknown, pet)

    result = scheduler.get_upcoming_tasks(days=1)
    same_time_tasks = [t for t in result if t.due_date == same_time]

    # The unknown type must appear last — known medical types surface first
    assert same_time_tasks[-1].type == "bath", "Unknown task type should sort after all known types"


# ─── RECURRENCE LOGIC ────────────────────────────────────────────────────────

# Happy path: completing a daily recurring task returns a next_occurrence that is
# approximately 1 day from now (same time-of-day, ±1 minute tolerance for test speed).
def test_daily_recurrence_next_occurrence_is_tomorrow(pet):
    task = Task(
        task_id="r1",
        type="feeding",
        description="Daily feeding",
        pet_id=pet.name,
        owner_id="o1",
        due_date=datetime.now() - timedelta(days=2),  # overdue — anchoring must still give tomorrow
        recurrence="daily",
    )
    task.complete()

    next_occ = task.get_next_occurrence()

    assert next_occ is not None, "A daily task must produce a next occurrence"
    expected = datetime.now() + timedelta(days=1)
    # Allow a 1-minute window to account for test execution time
    assert abs((next_occ - expected).total_seconds()) < 60, (
        f"Expected ~tomorrow ({expected:%H:%M}), got {next_occ:%H:%M}"
    )


# Happy path: weekly recurrence returns ~7 days from now.
def test_weekly_recurrence_next_occurrence_is_next_week(pet):
    task = Task(
        task_id="r2",
        type="grooming",
        description="Weekly grooming",
        pet_id=pet.name,
        owner_id="o1",
        due_date=datetime.now() + timedelta(days=3),
        recurrence="weekly",
    )

    next_occ = task.get_next_occurrence()

    assert next_occ is not None
    expected = datetime.now() + timedelta(days=7)
    assert abs((next_occ - expected).total_seconds()) < 60


# Edge case: a non-recurring task must return None — no next occurrence exists.
def test_non_recurring_task_returns_none(pet):
    task = Task(
        task_id="r3",
        type="vet",
        description="One-time vet visit",
        pet_id=pet.name,
        owner_id="o1",
        due_date=datetime.now() + timedelta(days=5),
        recurrence=None,  # explicitly no recurrence
    )

    assert task.get_next_occurrence() is None, "Non-recurring task must return None"


# Edge case: an overdue recurring task must schedule its next occurrence in the
# future (not in the past). Without the "anchor to today" fix, completing a task
# that was due last week would produce a next date still in the past.
def test_overdue_recurring_task_next_occurrence_is_in_future(pet):
    task = Task(
        task_id="r4",
        type="medication",
        description="Daily medication",
        pet_id=pet.name,
        owner_id="o1",
        due_date=datetime.now() - timedelta(days=7),  # a week overdue
        recurrence="daily",
    )

    next_occ = task.get_next_occurrence()

    assert next_occ is not None
    assert next_occ > datetime.now(), (
        "Next occurrence for an overdue recurring task must be in the future"
    )


# ─── CONFLICT DETECTION ──────────────────────────────────────────────────────

# Happy path: two tasks for the same pet at the same time triggers a SAME-PET warning.
def test_same_pet_same_time_returns_conflict_warning(scheduler, pet):
    same_time = datetime.now() + timedelta(hours=1)

    t1 = Task("c1", "feeding",  "Feed Buddy",   pet.name, "o1", same_time)
    t2 = Task("c2", "grooming", "Groom Buddy",  pet.name, "o1", same_time)

    scheduler.add_task(t1, pet)
    warning = scheduler.add_task(t2, pet)

    assert warning is not None, "Scheduler must return a warning for a same-pet time conflict"
    assert "SAME-PET" in warning, f"Expected SAME-PET warning, got: {warning}"


# Edge case: same owner, two different pets, same time — owner cannot handle both at once.
def test_same_owner_different_pets_same_time_returns_owner_warning(scheduler, pet, pet2):
    same_time = datetime.now() + timedelta(hours=2)

    t1 = Task("c3", "feeding", "Feed Buddy",  pet.name,  "o1", same_time)
    t2 = Task("c4", "feeding", "Feed Luna",   pet2.name, "o1", same_time)

    scheduler.add_task(t1, pet)
    warning = scheduler.add_task(t2, pet2)

    assert warning is not None, "Scheduler must warn when the same owner has overlapping tasks for different pets"
    assert "OWNER" in warning, f"Expected OWNER warning, got: {warning}"


# Happy path: tasks for two different owners at the same time — no conflict expected.
def test_different_owners_same_time_no_conflict(scheduler, pet):
    same_time = datetime.now() + timedelta(hours=3)

    t1 = Task("c5", "feeding", "Feed Buddy",  pet.name, "o1", same_time)
    t2 = Task("c6", "feeding", "Feed Rex",    "Rex",    "o2", same_time)  # different owner

    scheduler.add_task(t1, pet)
    warning = scheduler.add_task(t2)  # no pet passed — owner o2 not registered here

    assert warning is None, "Tasks for different owners at the same time must not produce a conflict"


# Edge case: completed tasks must be ignored by conflict detection — a completed
# task should not block a new task from being scheduled in the same slot.
def test_completed_task_does_not_block_new_task(scheduler, pet):
    same_time = datetime.now() + timedelta(hours=1)

    t1 = Task("c7", "feeding", "Feed Buddy", pet.name, "o1", same_time)
    scheduler.add_task(t1, pet)
    t1.complete()  # mark it done — slot should now be free

    t2 = Task("c8", "grooming", "Groom Buddy", pet.name, "o1", same_time)
    warning = scheduler.add_task(t2, pet)

    assert warning is None, "A completed task must not trigger a conflict for a new task in the same slot"
