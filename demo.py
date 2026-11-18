"""End-to-end demo: three inputs through scheduler -> advisor -> guardrails."""
from advisor import advise_schedule, find_plan_warnings
from pawpal_system import Owner, Pet, Scheduler, Task
import logging
logging.basicConfig(filename="pawpal.log", level=logging.INFO)


def run_case(label, owner):
    scheduler = Scheduler(owner)
    plan = scheduler.generate_schedule()
    print(f"\n=== {label} ===")
    print("Plan:")
    for t in plan:
        print(f"  {t.time}  {t.pet_name}: {t.title} ({t.duration_minutes} min, {t.priority})")
    print(scheduler.explain_plan())
    for c in scheduler.detect_conflicts():
        print("CONFLICT:", c)
    for w in find_plan_warnings(owner, plan):
        print("WARNING:", w)
    for a in advise_schedule(owner, plan):
        if a["tips"]:
            print(f"TIPS for {a['pet']}: {a['task']} (confidence {a['confidence']:.0%})")
            for tip in a["tips"]:
                print("   -", tip["text"])
        else:
            print(f"NO RELIABLE GUIDANCE for {a['pet']}: {a['task']} -> ask your vet")


# Case 1: normal day, a dog walk and a cat feeding
owner = Owner("Jordan", 120)
rex, mia = Pet("Rex", "dog"), Pet("Mia", "cat")
owner.add_pet(rex)
owner.add_pet(mia)
rex.add_task(Task("Morning walk", 30, "high", "09:00"))
mia.add_task(Task("Feed breakfast", 10, "medium", "08:00"))
run_case("Case 1: normal day", owner)

# Case 2: guardrail, a walk scheduled right after a meal
owner = Owner("Jordan", 120)
rex = Pet("Rex", "dog")
owner.add_pet(rex)
rex.add_task(Task("Feed dinner", 20, "high", "18:00"))
rex.add_task(Task("Evening walk", 30, "high", "18:20"))
run_case("Case 2: walk right after a meal", owner)

# Case 3: no relevant knowledge, the system should admit it
owner = Owner("Jordan", 120)
kiwi = Pet("Kiwi", "bird")
owner.add_pet(kiwi)
kiwi.add_task(Task("Play time", 15, "medium", "10:00"))
run_case("Case 3: topic not in the knowledge base", owner)