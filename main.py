from datetime import datetime, timedelta
from pawpal_system import Owner, Pet, Task, Scheduler

# --- Setup ---
scheduler = Scheduler()
owner = Owner("o1", "Alex Johnson", "alex@pawpal.com", "555-0101", scheduler)

buddy = Pet("Buddy", "dog", "Labrador", 3, 28.5, "o1")
luna  = Pet("Luna",  "cat", "Siamese",  5, 4.2,  "o1")
owner.add_pet(buddy)
owner.add_pet(luna)

# --- Tasks added OUT OF ORDER (far future → overdue → today) ---
# This lets us verify that sorting puts them back in the right order.
now       = datetime.now()
yesterday = now - timedelta(days=1)
tomorrow  = now + timedelta(days=1)
next_week = now + timedelta(days=7)

# Added last but due soonest — sorting should surface these first
task_grooming  = Task("t5", "grooming",   "Brush Buddy's coat",            "Buddy", "o1", next_week.replace(hour=14, minute=0,  second=0, microsecond=0))
task_vet       = Task("t4", "vet",        "Luna's annual checkup",          "Luna",  "o1", yesterday.replace(hour=10, minute=0,  second=0, microsecond=0))  # overdue
task_feeding   = Task("t1", "feeding",    "Feed Buddy his morning kibble",  "Buddy", "o1", now.replace(hour=8,  minute=0,  second=0, microsecond=0), recurrence="daily")
task_exercise  = Task("t3", "exercise",   "Walk Buddy in the park",         "Buddy", "o1", now.replace(hour=8,  minute=0,  second=0, microsecond=0), recurrence="daily")   # same time as feeding — priority tiebreaker
task_medication= Task("t2", "medication", "Give Luna her allergy tablet",   "Luna",  "o1", now.replace(hour=9,  minute=30, second=0, microsecond=0), recurrence="daily")

for task in [task_grooming, task_vet, task_feeding, task_exercise, task_medication]:
    warning = scheduler.add_task(task)
    if warning:
        print(f"  ⚠  {warning}")

# ── 1. SORTED UPCOMING TASKS ─────────────────────────────────────────────────
print("=" * 55)
print("  1. UPCOMING TASKS — sorted by time + priority")
print("     (added out of order; medication beats exercise at 8am)")
print("=" * 55)
upcoming = scheduler.get_upcoming_tasks(days=7)
if upcoming:
    for t in upcoming:
        recur = f"  [{t.recurrence}]" if t.recurrence else ""
        print(f"  [{t.type.upper():10}] {t.description:<35} due {t.due_date.strftime('%a %I:%M %p')}{recur}")
else:
    print("  No upcoming tasks.")

# ── 2. OVERDUE TASKS — sorted oldest first ───────────────────────────────────
print()
print("=" * 55)
print("  2. OVERDUE TASKS — sorted oldest-first")
print("=" * 55)
overdue = scheduler.check_overdue_tasks()
if overdue:
    for t in overdue:
        print(f"  [OVERDUE] {t.description} — was due {t.due_date.strftime('%Y-%m-%d %I:%M %p')}")
        scheduler.send_reminder(t, owner)
else:
    print("  No overdue tasks.")

# ── 3. FILTER BY PET ─────────────────────────────────────────────────────────
print()
print("=" * 55)
print("  3. FILTER BY PET")
print("=" * 55)
for pet in [buddy, luna]:
    pet_tasks = scheduler.get_tasks_for_pet(pet.name)
    print(f"  {pet.name} ({len(pet_tasks)} task(s)):")
    for t in pet_tasks:
        print(f"    • [{t.type}] {t.description}")

# ── 4. FILTER BY STATUS ──────────────────────────────────────────────────────
print()
print("=" * 55)
print("  4. FILTER BY STATUS — before completing a task")
print("=" * 55)
pending   = scheduler.get_tasks_by_status("pending")
completed = scheduler.get_tasks_by_status("completed")
print(f"  Pending   : {len(pending)}")
print(f"  Completed : {len(completed)}")

# ── 5. COMPLETE A RECURRING TASK — new instance spawned ──────────────────────
print()
print("=" * 55)
print("  5. COMPLETE RECURRING TASK — new instance auto-spawned")
print("=" * 55)
print(f"  Completing '{task_feeding.description}' (daily) ...")
task_feeding.complete()
print(f"  Status after complete() : {task_feeding.status}")

# Manually spawn next occurrence to show the timedelta calculation
next_occurrence = task_feeding.get_next_occurrence()
print(f"  Next occurrence (today + 1 day via timedelta) : {next_occurrence.strftime('%Y-%m-%d %I:%M %p') if next_occurrence else 'None'}")

# ── 6. FILTER BY STATUS — after completing ───────────────────────────────────
print()
print("=" * 55)
print("  6. FILTER BY STATUS — after completing one task")
print("=" * 55)
pending   = scheduler.get_tasks_by_status("pending")
completed = scheduler.get_tasks_by_status("completed")
print(f"  Pending   : {len(pending)}")
print(f"  Completed : {len(completed)}")
for t in completed:
    print(f"    ✓ [{t.type}] {t.description}")

# ── 7. CONFLICT DETECTION ────────────────────────────────────────────────────
print()
print("=" * 55)
print("  7. CONFLICT DETECTION — duplicate slot blocked")
print("=" * 55)
# Same-pet conflict: Buddy already has a task at 8am
same_pet_clash = Task("t98", "grooming", "Bath Buddy (same-pet clash at 8am)", "Buddy", "o1",
                      now.replace(hour=8, minute=0, second=0, microsecond=0))
warning = scheduler.add_task(same_pet_clash, buddy)
print(f"  Same-pet → {warning if warning else 'No conflict.'}")

# Cross-pet conflict: Luna task at 8am while owner is already doing Buddy's feeding
cross_pet_clash = Task("t99", "feeding", "Feed Luna (owner busy with Buddy at 8am)", "Luna", "o1",
                       now.replace(hour=8, minute=0, second=0, microsecond=0))
warning = scheduler.add_task(cross_pet_clash, luna)
print(f"  Cross-pet → {warning if warning else 'No conflict.'}")

# ── Notifications ─────────────────────────────────────────────────────────────
if scheduler.notifications:
    print()
    print("=" * 55)
    print("  NOTIFICATIONS")
    print("=" * 55)
    for note in scheduler.notifications:
        print(f"  • {note}")
