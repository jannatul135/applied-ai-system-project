"""Test harness: runs PawPal+ on predefined inputs and prints a pass/fail summary."""
import logging

from advisor import advise_task, find_plan_warnings
from pawpal_system import Owner, Pet, Scheduler, Task
from retriever import retrieve

logging.basicConfig(
    filename="pawpal.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

confidences = []

def case_species_mismatch():
    advice = advise_task(Task("play", 20, pet_name="Kiwi"), "bird")
    return not advice["tips"], "bird does not get a cat tip"

def case_dog_walk():
    advice = advise_task(Task("Morning walk", 20, pet_name="Rex"), "dog")
    confidences.append(advice["confidence"])
    ok = bool(advice["tips"]) and advice["tips"][0]["source"] == "exercise.txt"
    return ok, f"confidence {advice['confidence']}"


def case_cat_feeding():
    advice = advise_task(Task("Feed breakfast", 10, pet_name="Mia"), "cat")
    confidences.append(advice["confidence"])
    ok = bool(advice["tips"]) and advice["tips"][0]["source"] == "feeding.txt"
    return ok, f"confidence {advice['confidence']}"


def case_bird_no_guidance():
    advice = advise_task(Task("Play time", 15, pet_name="Kiwi"), "bird")
    return not advice["tips"], "irrelevant matches discarded"


def case_empty_title():
    advice = advise_task(Task("", 10, pet_name="Rex"), "dog")
    return not advice["tips"], "no crash on empty title"


def case_empty_query():
    return retrieve("") == [], "empty query returns nothing"


def case_conflict_detection():
    owner = Owner("Test", 120)
    a, b = Pet("Rex", "dog"), Pet("Mia", "cat")
    owner.add_pet(a)
    owner.add_pet(b)
    a.add_task(Task("Walk", 20, time="09:00"))
    b.add_task(Task("Feed", 10, time="09:00"))
    found = Scheduler(owner).detect_conflicts()
    return len(found) == 1, f"{len(found)} conflict found"


def case_walk_after_meal_warning():
    owner = Owner("Test", 120)
    rex = Pet("Rex", "dog")
    owner.add_pet(rex)
    rex.add_task(Task("Feed dinner", 20, time="08:00"))
    rex.add_task(Task("Evening walk", 20, time="08:20"))
    rex.add_task(Task("Late walk", 20, time="10:00"))
    warnings = find_plan_warnings(owner, rex.get_tasks())
    return len(warnings) == 1, f"{len(warnings)} warning (only the 08:20 walk)"


def case_time_budget():
    owner = Owner("Test", 30)
    rex = Pet("Rex", "dog")
    owner.add_pet(rex)
    rex.add_task(Task("Walk", 20, priority="high", time="09:00"))
    rex.add_task(Task("Brush", 20, priority="low", time="10:00"))
    plan = Scheduler(owner).generate_schedule()
    return len(plan) == 1 and plan[0].title == "Walk", "high priority kept, low dropped"


CASES = [
    ("Dog walk retrieves an exercise tip", case_dog_walk),
    ("Cat feeding retrieves a feeding tip", case_cat_feeding),
    ("Bird 'play time' gets no irrelevant tip", case_bird_no_guidance),
    ("Empty task title handled safely", case_empty_title),
    ("Empty retrieval query handled safely", case_empty_query),
    ("Same-time tasks flagged as conflict", case_conflict_detection),
    ("Walk right after a meal triggers warning", case_walk_after_meal_warning),
    ("Schedule respects owner's time budget", case_time_budget),
    ("Bird 'play' does not get a cat-only tip", case_species_mismatch),
]


def run():
    print("PawPal+ reliability harness")
    print("=" * 60)
    passed = 0
    for name, fn in CASES:
        try:
            ok, detail = fn()
        except Exception as exc:  # a crash counts as a failure
            ok, detail = False, f"crashed: {exc}"
        passed += ok
        print(f"{'PASS' if ok else 'FAIL'}  {name}  ({detail})")
    print("=" * 60)
    avg = sum(confidences) / len(confidences) if confidences else 0
    print(f"Result: {passed}/{len(CASES)} passed | avg retrieval confidence: {avg:.2f}")


if __name__ == "__main__":
    run()