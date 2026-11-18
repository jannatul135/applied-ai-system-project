# Model Card: PawPal+ Care Advisor

## System Overview
A pet-care scheduler (my Module 2 PawPal+ project) extended with a retrieval-based advisor. There is no trained model: it uses keyword retrieval over three small text files in `knowledge/`, rule-based guardrails, and human approval of the final plan.

## Limitations and Biases
- **Tiny, unreviewed knowledge base.** About a dozen general tips that I wrote myself. A veterinarian has not checked them, and they are not medical advice.
- **Uneven species coverage.** Guidance exists mainly for dogs and cats. Birds and "other" pets usually get "ask your vet," so owners of less common pets get less help.
- **Keyword matching only.** A differently worded task ("stroll" instead of "walk") may find nothing, and a generic word can match an unrelated tip. I saw this in testing with the bird task "Play time," which matched a medication tip about "the same time each day" until I added a confidence cutoff.
- **Coarse confidence scores.** Confidence is matched words divided by query words, so short queries give nearly identical numbers (0.67 in every harness run).
- **Only one plan-level safety rule.** The meal-then-walk check is the only one. Heat, medication timing, and other risks are not checked.
- **Typical-pet bias.** The tips assume a healthy adult pet of average size. Puppies, seniors, and sick animals need different care.
- **Scheduler limits (from the original project).** Conflict detection only catches exact matching start times, not overlapping durations.

## Misuse and Prevention
Someone could treat the tips as veterinary advice and skip a real vet visit. Prevention in the current system: it says "ask your vet" when it has no reliable match, discards weak matches, shows a confidence value, requires the owner to approve or reject the plan, and logs decisions to `pawpal.log`. A future version should show a permanent disclaimer and use vet-reviewed sources.

## What Surprised Me in Testing
- The bird task "Play time" received an unrelated medication tip, because both contain the word "time." Matching on shared words alone is easy to fool, which is why I added a minimum confidence cutoff.
- Every confidence score came out as 0.67. The score works as a pass/fail cutoff but is not a precise measure of how good a match is.

## Collaboration with AI
I used Claude to plan the extension, write the retriever, advisor, and test harness, and debug setup problems (for example, a file saved in the wrong folder).
- **Suggestion I accepted:** keeping the new AI feature in separate `retriever.py` and `advisor.py` modules instead of editing my scheduler. My Module 2 code and its 14 pytest tests stayed unchanged, and I could test the new feature on its own.
- **Suggestion I scoped down:** the assignment and the AI offered four optional stretch features (RAG enhancement, agentic workflow, fine-tuning, test harness). I built only two, the RAG enhancement and the test harness, because they fit my system and I wanted to finish a smaller project that I understand fully.

## Evaluation Results

| Test Input | Evaluation Criteria | Result |
|---|---|---|
| Dog "Morning walk" | Retrieves an exercise tip | Pass (confidence 0.67) |
| Cat "Feed breakfast" | Retrieves a feeding tip | Pass (confidence 0.67) |
| Bird "Play time" | No irrelevant tip shown | Pass |
| Empty task title | Handled without crashing | Pass |
| Empty retrieval query | Returns no results | Pass |
| Two tasks at 09:00 | Conflict flagged | Pass |
| Dinner at 08:00, walks at 08:20 and 10:00 | Warning for the 08:20 walk only | Pass |
| 30-minute budget, two 20-minute tasks | High-priority task kept, low dropped | Pass |

Summary: 8/8 harness tests passed, average retrieval confidence 0.67. Full log: `assets/harness_output.txt`. The original 14 pytest tests also cover the scheduler.