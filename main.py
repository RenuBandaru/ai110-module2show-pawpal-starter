from datetime import datetime, timedelta
from pawpal_system import Owner, Pet, Task, Scheduler

# --- Setup ---
scheduler = Scheduler()
owner = Owner("o1", "Alex Johnson", "alex@pawpal.com", "555-0101", scheduler)

# --- Pets ---
buddy = Pet("Buddy", "dog", "Labrador", 3, 28.5, "o1")
luna  = Pet("Luna",  "cat", "Siamese",  5, 4.2,  "o1")

owner.add_pet(buddy)
owner.add_pet(luna)

# --- Tasks (now with specific times of day) ---
now       = datetime.now()
yesterday = now - timedelta(days=1)
tomorrow  = now + timedelta(days=1)

task1 = Task("t1", "feeding",    "Feed Buddy his morning kibble",  "Buddy", "o1", now.replace(hour=8,  minute=0,  second=0, microsecond=0), recurrence="daily")
task2 = Task("t2", "medication", "Give Luna her allergy tablet",   "Luna",  "o1", now.replace(hour=9,  minute=30, second=0, microsecond=0), recurrence="daily")
task3 = Task("t3", "grooming",   "Brush Buddy's coat",             "Buddy", "o1", tomorrow.replace(hour=14, minute=0, second=0, microsecond=0))
task4 = Task("t4", "vet",        "Luna's annual checkup",          "Luna",  "o1", yesterday.replace(hour=10, minute=0, second=0, microsecond=0))  # overdue

for task in [task1, task2, task3, task4]:
    owner.schedule_task(task, scheduler)

# --- Today's Schedule ---
print("=" * 45)
print("        PAWPAL+ — TODAY'S SCHEDULE")
print("=" * 45)
print(f"Owner : {owner.name}")
print(f"Pets  : {', '.join(p.name for p in owner.get_pets())}")
print("-" * 45)

upcoming = scheduler.get_upcoming_tasks(days=1)
if upcoming:
    for task in upcoming:
        recur = f"  [{task.recurrence}]" if task.recurrence else ""
        print(f"  [{task.type.upper()}] {task.description} — due {task.due_date.strftime('%Y-%m-%d %I:%M %p')}{recur}")
else:
    print("  No tasks due today or tomorrow.")

print("-" * 45)

overdue = scheduler.check_overdue_tasks()
if overdue:
    print(f"  ⚠  {len(overdue)} overdue task(s):")
    for task in overdue:
        print(f"     - {task.description} (was due {task.due_date.strftime('%Y-%m-%d %I:%M %p')})")
        scheduler.send_reminder(task, owner)
else:
    print("  No overdue tasks.")

print("=" * 45)

if scheduler.notifications:
    print("\nNOTIFICATIONS:")
    for note in scheduler.notifications:
        print(f"  • {note}")
