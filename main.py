from pawpal_system import Owner, Pet, Task, Scheduler

# --- Tasks for Mochi (dog) ---
mochi = Pet(name="Mochi", species="dog", age=3)
mochi.add_task(Task(title="Morning walk",    duration_minutes=30, priority="high"))
mochi.add_task(Task(title="Feed breakfast",  duration_minutes=10, priority="high"))
mochi.add_task(Task(title="Evening walk",    duration_minutes=20, priority="medium"))

# --- Tasks for Luna (cat) ---
luna = Pet(name="Luna", species="cat", age=2)
luna.add_task(Task(title="Feed lunch",       duration_minutes=10, priority="high"))
luna.add_task(Task(title="Grooming",         duration_minutes=15, priority="medium"))
luna.add_task(Task(title="Enrichment play",  duration_minutes=20, priority="low"))

# --- Tasks for Pip (rabbit) ---
pip = Pet(name="Pip", species="rabbit", age=1)
pip.add_task(Task(title="Feed veggies",      duration_minutes=10, priority="high"))
pip.add_task(Task(title="Cage cleaning",     duration_minutes=25, priority="medium"))
pip.add_task(Task(title="Free roam time",    duration_minutes=30, priority="low"))

# --- Owner with availability 8am–12pm and 2pm–6pm ---
owner = Owner(
    name="Jordan",
    availability_windows=[
        {"start": "08:00", "end": "12:00"},
        {"start": "14:00", "end": "18:00"},
    ],
    max_activity_minutes=240
)
owner.add_pet(mochi)
owner.add_pet(luna)
owner.add_pet(pip)

# --- Print Today's Schedule for each pet ---
print("=" * 50)
print("           Today's Schedule")
print("=" * 50)

for pet in owner.pets:
    single_owner = Owner(
        name=owner.name,
        availability_windows=owner.availability_windows,
        max_activity_minutes=owner.max_activity_minutes
    )
    single_owner.add_pet(pet)
    schedule = Scheduler(single_owner).run()

    print(f"\n--- {pet.name} ({pet.species}, age {pet.age}) ---")

    if schedule.items:
        for item in sorted(schedule.items, key=lambda x: x.start):
            print(f"  {item.start.strftime('%H:%M')} - {item.end.strftime('%H:%M')}  "
                  f"{item.task.title} "
                  f"({'mandatory' if item.task.mandatory else 'optional'})")
    else:
        print("  No tasks could be scheduled.")

    if any("Could not place" in n for n in schedule.notes):
        for note in schedule.notes:
            if "Could not place" in note:
                print(f"  ! {note}")

print("\n" + "=" * 50)
print(f"Owner: {owner.name}  |  Max activity: {owner.max_activity_minutes} min")
print("=" * 50)
