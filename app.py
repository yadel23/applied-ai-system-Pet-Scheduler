import streamlit as st
from datetime import time
from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
#### Welcome to the PawPal+ app.
"""
)
# This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
# but **it does not implement the project logic**. Your job is to design the system and build it.
# Use this app as your interactive demo once your backend classes/functions exist.

# with st.expander("Scenario", expanded=True):
#     st.markdown(
#         """
# **PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
# for their pet(s) based on constraints like time, priority, and preferences.
# """
#     )
# # You will design and implement the scheduling logic and connect it to this Streamlit UI.


# with st.expander("What you need to build", expanded=True):
#     st.markdown(
#         """
# At minimum, your system should:
# - Represent pet care tasks (what needs to happen, how long it takes, priority)
# - Represent the pet and the owner (basic info and preferences)
# - Build a plan/schedule for a day that chooses and orders tasks based on constraints
# - Explain the plan (why each task was chosen and when it happens)
# """
#     )

st.divider()

st.subheader("Pet Owner Input")
owner_name = st.text_input("Owner name", value="Jordan")
pet_name = st.text_input("Pet name", value="Mochi")
col_species, col_age = st.columns(2)
with col_species:
    species = st.selectbox("Species", ["dog", "cat", "rabbit", "bird", "reptile", "other"])
with col_age:
    pet_age = st.number_input("Pet age (years)", min_value=0, max_value=30, value=2)

st.markdown("### Availability Windows")
st.caption("Add the time windows when you are available to complete tasks. (must have at least one time window)")

if "availability_windows" not in st.session_state:
    st.session_state.availability_windows = []
if "owner" not in st.session_state:
    st.session_state.owner = None
if "pet" not in st.session_state:
    st.session_state.pet = None
if "schedule" not in st.session_state:
    st.session_state.schedule = None

col_s, col_e = st.columns(2)
with col_s:
    window_start = st.time_input("Start time", value=time(8, 0), key="window_start")
with col_e:
    window_end = st.time_input("End time", value=time(12, 0), key="window_end")

if st.button("Add window"):
    if window_start >= window_end:
        st.error("Start time must be before end time.")
    else:
        st.session_state.availability_windows.append(
            {"start": window_start.strftime("%H:%M"), "end": window_end.strftime("%H:%M")}
        )

if st.session_state.availability_windows:
    st.write("Your availability:")
    for i, w in enumerate(st.session_state.availability_windows):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"{w['start']} – {w['end']}")
        with col2:
            if st.button("Remove", key=f"remove_window_{i}"):
                st.session_state.availability_windows.pop(i)
                st.rerun()
else:
    st.info("No availability windows added yet.")

max_activity_minutes = st.number_input("Max activity (minutes)", min_value=30, max_value=480, value=180, step=10)

st.markdown("### Tasks")
st.caption("Add a few tasks. In your final version, these should feed into your scheduler.")

if "tasks" not in st.session_state:
    st.session_state.tasks = []

col1, col2, col3 = st.columns(3)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
with col3:
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

if st.button("Add task"):
    st.session_state.tasks.append(
        {"title": task_title, "duration_minutes": int(duration), "priority": priority}
    )

if st.session_state.tasks:
    st.write("Current tasks:")
    st.table(st.session_state.tasks)
else:
    st.info("No tasks yet. Add one above.")

st.divider()

st.subheader("Build Schedule")
st.caption("Use 'Generate schedule' button should to build your schedule.")

if st.button("Generate schedule"):
    if not st.session_state.tasks:
        st.error("Please add at least one task.")
    elif not st.session_state.availability_windows:
        st.error("Please add at least one availability window.")
    else:
        # Reuse existing pet if name and species haven't changed, otherwise create a new one
        existing_pet = st.session_state.pet
        if (existing_pet is None
                or existing_pet.name != pet_name
                or existing_pet.species != species
                or existing_pet.age != pet_age):
            st.session_state.pet = Pet(name=pet_name, species=species, age=pet_age)
        pet = st.session_state.pet

        # Reuse existing owner if name, windows, and max activity haven't changed
        existing_owner = st.session_state.owner
        if (existing_owner is None
                or existing_owner.name != owner_name
                or existing_owner.availability_windows != st.session_state.availability_windows
                or existing_owner.max_activity_minutes != max_activity_minutes):
            st.session_state.owner = Owner(
                name=owner_name,
                availability_windows=st.session_state.availability_windows,
                max_activity_minutes=max_activity_minutes
            )
        owner = st.session_state.owner

        # Always rebuild tasks from current session state and attach to pet
        pet.tasks = [
            Task(
                title=t["title"],
                duration_minutes=t["duration_minutes"],
                priority=t["priority"]
            )
            for t in st.session_state.tasks
        ]
        owner.pets = [pet]

        st.session_state.schedule = Scheduler(owner).run()

# Display schedule from session state so it persists across reruns
schedule = st.session_state.schedule
if schedule:
        st.success(f"Schedule generated for {schedule.date.strftime('%Y-%m-%d')}")

        if schedule.items:
            st.subheader("Scheduled Tasks")
            sorted_items = sorted(schedule.items, key=lambda x: x.start)
            schedule_data = []
            for item in sorted_items:
                schedule_data.append({
                    "Time": f"{item.start.strftime('%H:%M')} - {item.end.strftime('%H:%M')}",
                    "Task": item.task.title,
                    "Duration": f"{item.duration_minutes()} min",
                    "Priority": item.task.priority,
                    "Reason": item.reason
                })
            st.table(schedule_data)

            st.subheader("Todo Task(s) List")
            for i, item in enumerate(sorted_items):
                done = st.checkbox(
                    item.task.title,
                    key=f"done_{i}_{item.task.title}",
                    value=item.task.completed_today
                )
                if done and not item.task.completed_today:
                    st.session_state.pet.complete_task(item.task.title)
                    st.session_state.schedule = Scheduler(st.session_state.owner).run()
                    st.rerun()
        elif st.session_state.pet and all(t.completed for t in st.session_state.pet.tasks):
            st.success("All scheduled tasks have been completed!")
        else:
            st.warning("No tasks could be scheduled.")

        if schedule.notes:
            st.subheader("Notes")
            for note in schedule.notes:
                st.write(f"- {note}")

        st.subheader("Summary")
        st.write(f"Total scheduled time: {schedule.total_minutes_scheduled()} minutes")

        mandatory = schedule.get_mandatory_tasks()
        optional = schedule.get_optional_tasks()

        st.write(f"**Mandatory tasks ({len(mandatory)}):**")
        if mandatory:
            for item in mandatory:
                st.write(f"  - {item.task.title}")
        else:
            st.write("  None")

        st.write(f"**Optional tasks ({len(optional)}):**")
        if optional:
            for item in optional:
                st.write(f"  - {item.task.title}")
        else:
            st.write("  None")

        st.write(f"**Optional tasks ({len(optional)}):**")
        if optional:
            for item in optional:
                st.write(f"  - {item.task.title}")
        else:
            st.write("  None")

# Chatbot in sidebar as toast-like chat
with st.sidebar:
    st.header("💬 PawPal+ Chat")
    
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    # Chat input at the top
    if prompt := st.chat_input("Ask simple pet questions..."):
        if not prompt.strip():
            st.toast("Please enter a question.", icon="❓")
        else:
            from pawpal_system import answer_schedule_question
            response = answer_schedule_question(
                st.session_state.owner,
                st.session_state.pet,
                st.session_state.schedule,
                prompt
            )
            st.session_state.chat_history.append({"question": prompt, "response": response})
            st.rerun()
    
    # Display chat messages (most recent at top)
    for chat in reversed(st.session_state.chat_history):
        with st.chat_message("user"):
            st.write(chat["question"])
        with st.chat_message("assistant"):
            st.write(chat["response"])
