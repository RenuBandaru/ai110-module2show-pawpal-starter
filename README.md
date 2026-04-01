# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Smarter Scheduling

The scheduler goes beyond a simple task list with four algorithmic improvements:

**Priority-aware sorting** — `get_upcoming_tasks(days)` sorts first by due time, then by task type when two tasks share the same slot. Medication and vet visits always surface above grooming or exercise, so a pet owner sees the most critical care first.

**Status filtering** — `get_tasks_by_status(status)` lets callers query `"pending"` or `"completed"` tasks independently. Completed tasks are preserved as a history record rather than deleted, and `check_overdue_tasks()` returns the oldest overdue item first so nothing critical gets buried.

**Recurring task auto-advance** — `Task.complete()` marks a task done permanently. For recurring tasks (`"daily"`, `"weekly"`, `"monthly"`), `get_next_occurrence()` calculates the next due date anchored to today using `timedelta`, not the original (potentially stale) due date. This means completing an overdue daily feeding always schedules the next one for tomorrow at the same time — never in the past.

**Conflict detection** — `has_conflict(task)` checks every new task against all pending tasks for the same owner, covering two cases: a same-pet overlap (the pet already has something in that window) and a cross-pet owner conflict (the owner is already occupied with another pet at that time). Rather than blocking the add, a descriptive warning string is returned so the owner stays informed but in control.

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.
