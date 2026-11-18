"""Care advisor: uses retrieved tips to explain and check a schedule (RAG + guardrails)."""
import logging

from retriever import retrieve

logger = logging.getLogger(__name__)

MIN_CONFIDENCE = 0.5       # tips below this are discarded as probably irrelevant
HIGH_CONFIDENCE = 0.6      # between MIN and HIGH, tell the user to double-check
SAFETY_GAP_MINUTES = 30    # no exercise this soon after a meal

FEED_WORDS = ("feed", "meal", "breakfast", "dinner", "lunch")
EXERCISE_WORDS = ("walk", "run", "jog", "exercise", "play")

KNOWN_SPECIES = ("dog", "cat", "rabbit", "bird")


def _fits_species(tip_text, species):
    """Reject tips that are about a different species than this pet."""
    text = tip_text.lower()
    return not any(s in text for s in KNOWN_SPECIES if s != species)

def _to_minutes(hhmm):
    hours, minutes = hhmm.split(":")
    return int(hours) * 60 + int(minutes)


def _mentions(title, words):
    return any(w in title.lower() for w in words)


def advise_task(task, species):
    """Look up care tips for one task. Never raises; returns a result dict."""
    result = {
        "pet": task.pet_name,
        "task": task.title,
        "tips": [],
        "confidence": 0.0,
        "low_confidence": True,
    }
    try:
        if not task.title.strip():
            logger.warning("Task with empty title skipped")
            return result
        tips = retrieve(f"{species} {task.title}", k=4)
        tips = [t for t in tips if t["confidence"] >= MIN_CONFIDENCE]
        tips = [t for t in tips if _fits_species(t["text"], species)][:2]
        if not tips:
            logger.info("No reliable guidance for %s / %s", species, task.title)
            return result
        result["tips"] = tips
        result["confidence"] = tips[0]["confidence"]
        result["low_confidence"] = result["confidence"] < HIGH_CONFIDENCE
        logger.info(
            "Advice for %s/%s: confidence %.2f", species, task.title, result["confidence"]
        )
    except Exception:
        logger.exception("Advisor failed for task %r", task.title)
    return result


def advise_schedule(owner, tasks):
    """Return advice for each task in a schedule."""
    species_by_pet = {p.name: p.species for p in owner.pets}
    return [advise_task(t, species_by_pet.get(t.pet_name, "pet")) for t in tasks]


def find_plan_warnings(owner, tasks):
    """Warn when a dog's exercise starts soon after its meal (uses a retrieved tip)."""
    warnings = []
    for pet in owner.pets:
        if pet.species != "dog":
            continue
        pet_tasks = [t for t in tasks if t.pet_name == pet.name and t.time]
        for meal in pet_tasks:
            if not _mentions(meal.title, FEED_WORDS):
                continue
            meal_start = _to_minutes(meal.time)
            meal_end = meal_start + meal.duration_minutes
            for ex in pet_tasks:
                if ex is meal or not _mentions(ex.title, EXERCISE_WORDS):
                    continue
                start = _to_minutes(ex.time)
                if meal_start <= start < meal_end + SAFETY_GAP_MINUTES:
                    found = retrieve("avoid heavy exercise walk after eats big meal", k=1)
                    reason = found[0]["text"] if found else "Wait before exercising after meals."
                    message = (
                        f"{pet.name}: '{ex.title}' at {ex.time} is right after "
                        f"'{meal.title}'. {reason}"
                    )
                    logger.warning("Plan warning: %s", message)
                    warnings.append(message)
    return warnings