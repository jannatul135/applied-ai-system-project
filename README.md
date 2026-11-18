# PawPal+ Care Advisor 🐾

## Original Project

This project extends **PawPal+ (Module 2)**, a Streamlit pet-care planner built with Python OOP. The original app let a busy pet owner register several pets, add timed care tasks (walks, feeding, medicine), and build a daily plan that fits their available time. It also sorted and filtered tasks, warned about same-time conflicts, and automatically repeated daily and weekly tasks.

## Summary

PawPal+ Care Advisor adds a **retrieval-augmented advisor** on top of that scheduler. After the plan is built, the advisor looks up pet-care guidance from a small knowledge base and uses it to (1) explain each task with relevant tips, (2) **act on the plan itself** by warning when a dog's walk is scheduled right after its meal, and (3) say "ask your vet" instead of guessing when nothing relevant is found. The owner must approve or reject the plan before it is accepted. It matters because a tool that gives advice should be honest about what it does not know.

## Features

**Original scheduler (Module 2)**
- **Multiple pets, one owner:** an `Owner` manages several `Pet`s, each with its own tasks.
- **Sorting by time** (`Scheduler.sort_by_time()`) and **filtering** by pet or status (`filter_by_pet()`, `filter_by_status()`).
- **Priority-based daily plan** that fits the owner's available minutes (`generate_schedule()`), with a plain-language explanation (`explain_plan()`).
- **Conflict warnings** for tasks at the same date and time (`detect_conflicts()`).
- **Recurring tasks:** completing a daily or weekly task creates the next occurrence (`mark_task_complete()`).

**New AI features (final project)**
- **RAG:** `retriever.py` searches `knowledge/*.txt` and `advisor.py` uses the results to explain tasks and check the plan.
- **Guardrails:** a minimum confidence cutoff, a meal-then-walk safety check, empty-input handling, and try/except around the advisor.
- **Human-in-the-loop:** the owner approves or rejects the generated plan.
- **Logging:** retrievals, warnings, and approvals are written to `pawpal.log`.
- **Reliability harness:** `test_harness.py` runs 8 predefined cases and prints a pass/fail summary.

## Architecture Overview

The source diagram is in [`diagrams/architecture.mmd`](diagrams/architecture.mmd).

1. The owner enters pets and tasks in the Streamlit UI (`app.py`), and input is validated.
2. The **Scheduler** (`pawpal_system.py`) builds a plan by priority and time budget and detects conflicts.
3. The **Advisor** (`advisor.py`) asks the **Retriever** (`retriever.py`) for matching tips from the text files in `knowledge/`.
4. **Guardrails** discard low-confidence matches and run the meal-then-walk check, using a retrieved tip as the explanation.
5. A **human-in-the-loop** step lets the owner approve or reject the plan, and the decision is logged.
6. `test_harness.py` exercises the scheduler, retriever, and advisor on fixed inputs.

## Setup Instructions

```bash
git clone https://github.com/jannatul135/applied-ai-system-project.git
cd applied-ai-system-project
python3 -m venv .venv
source .venv/bin/activate        # Windows PowerShell: .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

```bash
streamlit run app.py             # launch the web app
python demo.py                   # end-to-end demo of the AI features
python test_harness.py           # reliability harness (8 cases)
python -m pytest                 # original scheduler tests (14 tests)
python main.py                   # original command-line demo
```

## Demo Walkthrough (web app)

1. **Set up the owner.** Enter your name and how many minutes you have today.
2. **Add pets.** Enter a name and species (dog, cat, bird, other).
3. **Add tasks.** Choose a pet, then enter a title, duration, priority, time, and repeat setting.
4. **Watch for conflicts.** Two pending tasks at the same time produce a yellow warning.
5. **Complete a task.** If it repeats, the app shows the next due date.
6. **Generate the schedule.** You get today's plan, the meal-then-walk warnings, and care tips with confidence values.
7. **Approve or reject.** Your decision is logged to `pawpal.log`.

## Sample Interactions

Full output is saved in [`assets/demo_output.txt`](assets/demo_output.txt). Command: `python demo.py`

**Case 1: normal day.** Input: Mia (cat) "Feed breakfast" 08:00, 10 min, medium; Rex (dog) "Morning walk" 09:00, 30 min, high.

```
Plan:
  08:00  Mia: Feed breakfast (10 min, medium)
  09:00  Rex: Morning walk (30 min, high)
TIPS for Mia: Feed breakfast (confidence 67%)
   - Adult cats are usually fed two or more small meals a day; always keep fresh water available.
TIPS for Rex: Morning walk (confidence 67%)
   - Most adult dogs need about 30 to 60 minutes of exercise or walking each day; puppies and high-energy breeds often need more, small or senior dogs often need less.
   - Walk a dog at least once or twice a day, and avoid long walks in the hottest part of the day.
```

**Case 2: guardrail acts on the plan.** Input: Rex (dog) "Feed dinner" 18:00, 20 min; "Evening walk" 18:20, 30 min.

```
Plan:
  18:00  Rex: Feed dinner (20 min, high)
  18:20  Rex: Evening walk (30 min, high)
WARNING: Rex: 'Evening walk' at 18:20 is right after 'Feed dinner'. Avoid heavy exercise or a long walk right after a dog eats a big meal.
```

**Case 3: no relevant knowledge, so the system admits it.** Input: Kiwi (bird) "Play time" 10:00, 15 min.

```
Plan:
  10:00  Kiwi: Play time (15 min, medium)
NO RELIABLE GUIDANCE for Kiwi: Play time -> ask your vet
```

## Reliability and Guardrail Results

Command: `python test_harness.py` (saved in [`assets/harness_output.txt`](assets/harness_output.txt))

```
PawPal+ reliability harness
============================================================
PASS  Dog walk retrieves an exercise tip  (confidence 0.67)
PASS  Cat feeding retrieves a feeding tip  (confidence 0.67)
PASS  Bird 'play time' gets no irrelevant tip  (irrelevant matches discarded)
PASS  Empty task title handled safely  (no crash on empty title)
PASS  Empty retrieval query handled safely  (empty query returns nothing)
PASS  Same-time tasks flagged as conflict  (1 conflict found)
PASS  Walk right after a meal triggers warning  (1 warning (only the 08:20 walk))
PASS  Schedule respects owner's time budget  (high priority kept, low dropped)
============================================================
Result: 8/8 passed | avg retrieval confidence: 0.67
```

**RAG enhancement (before/after).** Before: the plan explanation said only that higher-priority tasks go first. After: each task shows tips pulled from three knowledge files (`exercise.txt`, `feeding.txt`, `care.txt`), and a retrieved tip is the stated reason for the meal-then-walk warning in Case 2.

## Original Scheduler Output

Output from the original `python main.py` demo:

```
Conflict check:
  WARNING: Conflict at 08:00 on 2026-10-18: Rex: Give medicine, Luna: Feed breakfast

Completing 'Morning walk' (repeats daily)...
  New task created for 2026-10-19: Morning walk
```

## Implementation Summary

`pawpal_system.py` holds four classes. A `Task` is one care activity (title, duration, priority, time, frequency, completion status, due date, and its pet's name). A `Pet` holds its tasks, an `Owner` holds several pets and returns every task through `get_all_tasks()`, and the `Scheduler` reads tasks through that method so it works across all pets. The Owner is stored in `st.session_state` so data persists between clicks. The final project adds `retriever.py` (loads the knowledge files and scores matches), `advisor.py` (applies the retrieved tips and guardrails), `test_harness.py`, and `demo.py`, without changing the scheduler classes.

## Smarter Scheduling

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_by_time()` | Sorts by zero-padded "HH:MM" time; untimed tasks go last |
| Filtering | `filter_by_status()`, `filter_by_pet()` | By completed/pending, or by pet name |
| Conflict handling | `detect_conflicts()` | Warns when pending tasks share a date and time; never crashes |
| Recurring tasks | `mark_task_complete()` | Creates the next daily or weekly task using `timedelta` |
| Schedule building | `generate_schedule()` | Priority first, then shortest, until time runs out |
| Care tips (new) | `advisor.advise_task()` | Retrieves tips and drops matches below 0.5 confidence |
| Meal-then-walk check (new) | `advisor.find_plan_warnings()` | Warns when a dog's exercise starts within 30 minutes after a meal |

## Design Decisions

- **Keyword retrieval instead of embeddings.** It needs no API keys or extra installs, runs offline, and every match can be explained. Trade-off: it only matches shared words, so it misses synonyms.
- **Advisor as a separate module.** The scheduler is unchanged, so the original 14 tests still apply.
- **Discard weak matches instead of only labeling them.** An unrelated tip with a warning label still misleads, so the advisor drops it and says "ask your vet."
- **Human approval.** Pet-care advice has real consequences, so the owner makes the final call.
- **Kept the original trade-off:** conflict detection checks exact start times only, not overlapping durations.

## Testing Summary

- `python test_harness.py`: **8 of 8 passed**, average retrieval confidence 0.67.
- `python -m pytest`: the original **14 scheduler tests** (sorting, recurrence, conflicts, filtering, edge cases).
- What worked: the guardrails, empty-input handling, and the plan-level warning.
- What I learned: the bird task "Play time" first matched an unrelated medication tip, so a confidence cutoff was needed. Every confidence score is 0.67 because queries are short, so the score is only useful as a cutoff, not as a precise measure.

## Project Structure

```
pawpal_system.py      # Task, Pet, Owner, Scheduler (logic layer)
retriever.py          # keyword retriever over knowledge/*.txt
advisor.py            # RAG advisor, confidence cutoff, meal-then-walk check
app.py                # Streamlit UI with approve/reject step
main.py               # original CLI demo
demo.py               # end-to-end demo of the AI features
test_harness.py       # reliability harness (8 cases)
tests/test_pawpal.py  # original pytest suite (14 tests)
knowledge/            # exercise.txt, feeding.txt, care.txt
diagrams/             # architecture.mmd, uml_draft.mmd, uml_final.mmd
assets/               # harness_output.txt, demo_output.txt
model_card.md         # limitations, misuse, testing surprises, AI collaboration
reflection.md         # design and AI collaboration reflection
```

## Reflection

This project taught me that the hard part of an AI feature is deciding when it should *not* answer. Retrieval was quick to build, but the guardrails and tests took the real thought. See `model_card.md` for limitations, misuse, and how I worked with AI.

Loom walkthrough (optional): _add link here_