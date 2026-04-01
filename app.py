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

        # Scheduler.add_task() returns a conflict warning string, or None if the slot is clear.
        # We always add the task (the owner stays in control) but surface the warning immediately.
        conflict = scheduler.add_task(task, pet)
        if conflict:
            st.warning(f"Task added with a scheduling conflict:\n\n{conflict}")
        else:
            st.success(f"Task added: {task.description}")

# ── Task list: split into Pending / Completed tabs ───────────────────────────
# Uses Scheduler.get_tasks_by_status() so both tabs are sorted by due_date
# rather than raw insertion order. Completed tasks are preserved as history.
scheduler_ref: Scheduler = st.session_state.scheduler
pending_tasks   = scheduler_ref.get_tasks_by_status("pending")
completed_tasks = scheduler_ref.get_tasks_by_status("completed")

# Metrics give a quick at-a-glance count before the table loads
m1, m2, m3 = st.columns(3)
m1.metric("Pending",   len(pending_tasks))
m2.metric("Completed", len(completed_tasks))
m3.metric("Total",     len(scheduler_ref.tasks))

# Priority badge shown next to each task type so urgency is visible at a glance
PRIORITY_LABEL = {
    "medication": "🔴 medication",
    "vet":        "🟠 vet",
    "feeding":    "🟡 feeding",
    "exercise":   "🟢 exercise",
    "grooming":   "🔵 grooming",
}

tab_pending, tab_completed = st.tabs(["Pending", "Completed"])

with tab_pending:
    if pending_tasks:
        st.dataframe(
            [
                {
                    "Priority": PRIORITY_LABEL.get(t.type, f"⚪ {t.type}"),
                    "Description": t.description,
                    "Pet": t.pet_id,
                    "Due": t.due_date.strftime("%b %d  %H:%M"),
                    "Recurrence": t.recurrence or "—",
                    "ID": t.task_id,
                }
                for t in pending_tasks   # already sorted by due_date from get_tasks_by_status()
            ],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No pending tasks yet. Add one above.")

with tab_completed:
    if completed_tasks:
        st.dataframe(
            [
                {
                    "Type": t.type,
                    "Description": t.description,
                    "Pet": t.pet_id,
                    "Was due": t.due_date.strftime("%b %d  %H:%M"),
                    "Recurrence": t.recurrence or "—",
                    "ID": t.task_id,
                }
                for t in completed_tasks
            ],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No completed tasks yet.")

st.divider()

# ── Section 3: Build Schedule ─────────────────────────────────────────────────
# Calls Scheduler methods to surface upcoming and overdue tasks.
# No new data is created here — this is purely a read/query operation.
st.subheader("Build Schedule")

# The slider controls how far ahead to look when calling get_upcoming_tasks()
days_ahead = st.slider("Show tasks due within (days)", min_value=1, max_value=30, value=7)

if st.button("Generate schedule"):
    scheduler: Scheduler = st.session_state.scheduler

    # get_upcoming_tasks() — sorted by (due_date, medical priority) via Scheduler
    upcoming = scheduler.get_upcoming_tasks(days_ahead)
    # check_overdue_tasks() — oldest overdue first, delegates to Task.is_overdue()
    overdue  = scheduler.check_overdue_tasks()

    if not upcoming and not overdue:
        st.info("No upcoming or overdue tasks in the selected window.")
    else:
        # ── Overdue tasks ── shown first so critical items are never buried
        if overdue:
            st.markdown("#### Overdue Tasks")
            for t in overdue:
                st.error(
                    f"**OVERDUE** — {t.description}  |  "
                    f"{PRIORITY_LABEL.get(t.type, t.type)}  |  "
                    f"was due {t.due_date.strftime('%b %d  %H:%M')}"
                )

        # ── Upcoming tasks ── rendered as a styled dataframe so columns are scannable
        if upcoming:
            st.markdown("#### Upcoming Tasks")

            # Rows are already priority-sorted by Scheduler.get_upcoming_tasks()
            rows = []
            for t in upcoming:
                rows.append({
                    "Priority": PRIORITY_LABEL.get(t.type, f"⚪ {t.type}"),
                    "Description": t.description,
                    "Pet": t.pet_id,
                    "Due": t.due_date.strftime("%b %d  %H:%M"),
                    "Recurrence": f"↻ {t.recurrence}" if t.recurrence else "—",
                })

            st.dataframe(rows, use_container_width=True, hide_index=True)
            st.success(
                f"{len(upcoming)} task{'s' if len(upcoming) != 1 else ''} scheduled "
                f"over the next {days_ahead} day{'s' if days_ahead != 1 else ''}."
            )
