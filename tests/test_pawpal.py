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
