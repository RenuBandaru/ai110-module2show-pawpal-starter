# PawPal+ Project Reflection

## 1. System Design

The Application needs to be able to do the following : 
1. Add a user profile
2. Add a pet
3. Schedule a walk for the pet
4. Show today's tasks
5. Make a meal plan 
6. Scheule med times with the meal plans
7. Schedule doctor appointments or grooming appointments

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

The main components/classes are Owner, Pet, Task, Scheduler.

The application needs ot know the profile details for both the owner and the pet. This includes name, contact like an email, username and password and maybe allergies for the owner and the pet's name, kind, age, diseases, allergies or pre-conditions that the pet might have. If there are multiple pets then that needs to be saved too. 

The application needs to be able to create a task based on the owner's inputs for the pet and schedule it accordingly into their calendar to accomadate for themselves and their pet.

These are the components and their corresponding attributes and methods

**Owner**

_Attributes:_
* name — owner's full name
* email — contact/login identifier
* phone — contact number
* pets — list of Pet objects they own

_Methods:_
* addPet(pet) — registers a pet to this owner
* removePet(petId) — removes a pet from their list
* getPets() — returns all pets for this owner
* scheduleTask(task, scheduler) — submits a task to the scheduler

**Pet**

_Attributes:_

name — pet's name
species — e.g. dog, cat, bird
breed — specific breed
age — age in years
weight — for medication/feeding calculations
medicalHistory — list of notes/conditions
ownerId — reference back to Owner
Methods:

getProfile() — returns pet summary info
addMedicalNote(note) — appends to medical history
getAge() — calculates/returns current age

**Task**

_Attributes:_

taskId — unique identifier
type — e.g. "feeding", "grooming", "vet", "medication"
description — details about the task
petId — which pet this task is for
dueDate — when it needs to happen
status — "pending", "completed", "overdue"
recurrence — e.g. "daily", "weekly", null

Methods:

complete() — marks task as completed
isOverdue() — checks if dueDate has passed
reschedule(newDate) — updates the due date
getNextOccurrence() — calculates next date if recurring

**Scheduler**

_Attributes:_

tasks — list of all Task objects
notifications — pending alerts to send

_Methods:_

addTask(task) — registers a new task
removeTask(taskId) — deletes a task
getTasksForPet(petId) — filters tasks by pet
getUpcomingTasks(days) — returns tasks due within N days
checkOverdueTasks() — scans and flags overdue tasks
sendReminder(task, owner) — triggers a notification


**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
