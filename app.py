import streamlit as st
from datetime import datetime
from pawpal_system import Owner, Pet, Task, Scheduler  # Phase 2 classes

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

# ── Session-state bootstrap ──────────────────────────────────────────────────
# Streamlit reruns the entire script on every interaction.
# st.session_state persists objects across reruns so we don't lose data.
# We initialize each key only once (on the very first load).
if "scheduler" not in st.session_state:
    st.session_state.scheduler = Scheduler()  # central coordinator — holds all tasks and owners
if "owner" not in st.session_state:
    st.session_state.owner = None             # set when "Register owner & pet" is clicked
if "pet" not in st.session_state:
    st.session_state.pet = None               # set alongside the owner above

# ── Section 1: Owner & Pet registration ─────────────────────────────────────
# The user provides a name, pet name, and species.
# Clicking "Register" creates real Owner and Pet objects from pawpal_system.py.
st.subheader("Owner & Pet")
owner_name = st.text_input("Owner name", value="Jordan")
pet_name = st.text_input("Pet name", value="Mochi")
species = st.selectbox("Species", ["dog", "cat", "other"])

if st.button("Register owner & pet"):
    # Pull the shared Scheduler out of session state so Owner can reference it.
    # Owner stores a reference to Scheduler so it can query tasks without owning them directly.
    scheduler = st.session_state.scheduler

    # Create the Owner — owner_id is a slug (e.g. "jordan") used as a dict key in Scheduler.owners
    owner = Owner(
        owner_id=owner_name.lower().replace(" ", "_"),
        name=owner_name,
        email="",   # not collected in the UI; defaults to empty
        phone="",   # not collected in the UI; defaults to empty
        scheduler=scheduler,
    )

    # Create the Pet — breed/age/weight aren't collected in the UI so we use safe defaults
    pet = Pet(
        name=pet_name,
        species=species,
        breed="unknown",  # placeholder; could be added to the UI later
        age=1,            # placeholder default age in years
        weight=0.0,       # placeholder default weight in kg
        owner_id=owner.owner_id,  # links Pet back to its Owner
    )

    owner.add_pet(pet)                    # Owner.add_pet() — appends pet to owner.pets list
    scheduler.owners[owner.owner_id] = owner  # register owner in Scheduler for O(1) lookup later

    # Save both to session state so other buttons can access them
    st.session_state.owner = owner
    st.session_state.pet = pet

    # Pet.get_profile() returns a formatted summary string, e.g. "Mochi (dog, unknown) - Age: 1, Weight: 0.0kg"
    st.success(f"Registered {owner.name} with pet: {pet.get_profile()}")

st.divider()

# ── Section 2: Add a Task ─────────────────────────────────────────────────────
# The user describes a care task. Clicking "Add task" creates a Task object
# and hands it to the Scheduler (which is the single source of truth for all tasks).
st.subheader("Tasks")
st.caption("Add tasks for your pet. Each task is passed to the Scheduler.")

# Row 1: what the task is
col1, col2, col3 = st.columns(3)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
with col3:
    # task_type maps to Task.type — the category labels defined in the Task dataclass
    task_type = st.selectbox("Type", ["feeding", "grooming", "medication", "vet", "exercise"])

# Row 2: when the task is due (Task.due_date requires a full datetime)
col4, col5 = st.columns(2)
with col4:
    due_date = st.date_input("Due date", value=datetime.today())
with col5:
    due_time = st.time_input("Due time", value=datetime.now().replace(second=0, microsecond=0).time())

# Optional recurrence — maps to Task.recurrence ("daily", "weekly", "monthly", or None)
recurrence = st.selectbox("Recurrence", ["none", "daily", "weekly", "monthly"])

if st.button("Add task"):
    # Guard: owner and pet must be registered before a task can be created,
    # because Task needs owner_id and pet_id to link back to them.
    if st.session_state.owner is None or st.session_state.pet is None:
        st.warning("Please register an owner and pet first.")
    else:
        owner: Owner = st.session_state.owner
        pet: Pet = st.session_state.pet
        scheduler: Scheduler = st.session_state.scheduler

        task = Task(
            task_id=f"t{len(scheduler.tasks) + 1}",  # simple auto-increment ID (e.g. "t1", "t2")
            type=task_type,                            # category label from the selectbox
            description=f"{task_title} ({duration} min)",  # combines title + duration into one string
            pet_id=pet.name,                           # links task to the pet
            owner_id=owner.owner_id,                   # links task to the owner
            due_date=datetime.combine(due_date, due_time),  # merge date + time into one datetime
            recurrence=recurrence if recurrence != "none" else None,  # None means one-off task
        )

        # Scheduler.add_task(task, pet) does two things:
        #   1. Appends task to scheduler.tasks (the master list)
        #   2. Appends task to pet.tasks (so pet.get_tasks() stays in sync)
        scheduler.add_task(task, pet)
        st.success(f"Task added: {task.description}")

# Read tasks directly from the Scheduler's master list (not a separate session_state list)
current_tasks = st.session_state.scheduler.tasks
if current_tasks:
    st.write("Current tasks:")
    # Build a list of plain dicts so st.table can render them as a readable table
    st.table([
        {
            "ID": t.task_id,
            "Type": t.type,
            "Description": t.description,
            "Pet": t.pet_id,
            "Due": t.due_date.strftime("%Y-%m-%d %H:%M"),
            "Status": t.status,                  # "pending" or "completed"
            "Recurrence": t.recurrence or "—",   # show a dash if the task doesn't repeat
        }
        for t in current_tasks
    ])
else:
    st.info("No tasks yet. Add one above.")

st.divider()

# ── Section 3: Build Schedule ─────────────────────────────────────────────────
# Calls Scheduler methods to surface upcoming and overdue tasks.
# No new data is created here — this is purely a read/query operation.
st.subheader("Build Schedule")

# The slider controls how far ahead to look when calling get_upcoming_tasks()
days_ahead = st.slider("Show tasks due within (days)", min_value=1, max_value=30, value=7)

if st.button("Generate schedule"):
    scheduler: Scheduler = st.session_state.scheduler

    # Scheduler.get_upcoming_tasks(days) — returns tasks due between now and now+days,
    # sorted chronologically by due_date
    upcoming = scheduler.get_upcoming_tasks(days_ahead)

    # Scheduler.check_overdue_tasks() — returns tasks whose due_date has passed
    # and whose status is still "pending" (delegates to Task.is_overdue() internally)
    overdue = scheduler.check_overdue_tasks()

    if not upcoming and not overdue:
        st.info("No upcoming or overdue tasks in the selected window.")
    else:
        if upcoming:
            st.markdown("#### Upcoming Tasks")
            for t in upcoming:
                # Append a recurrence note if the task repeats (e.g. "_(repeats daily)_")
                extra = f" _(repeats {t.recurrence})_" if t.recurrence else ""
                st.markdown(
                    f"- **{t.description}** [{t.type}] — due {t.due_date.strftime('%Y-%m-%d %H:%M')}{extra}"
                )

        if overdue:
            st.markdown("#### Overdue Tasks")
            for t in overdue:
                # st.error renders a red banner — makes overdue tasks visually distinct
                st.error(
                    f"OVERDUE — {t.description} [{t.type}] was due {t.due_date.strftime('%Y-%m-%d %H:%M')}"
                )
