"""
Academic Scheduling System (CSP revision)
Produces schedules.csv as output.

Dependencies:
    pip install python-constraint
"""

from constraint import Problem, FunctionConstraint
import itertools
import csv
import random
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import math

# ---------------------------
# Utility: time slot generation
# ---------------------------
def generate_time_slots(start="07:30", end="21:00", slot_minutes=90):
    fmt = "%H:%M"
    start_dt = datetime.strptime(start, fmt)
    end_dt = datetime.strptime(end, fmt)
    slots = []
    cur = start_dt
    while cur + timedelta(minutes=slot_minutes) <= end_dt:
        s = cur.strftime(fmt)
        e = (cur + timedelta(minutes=slot_minutes)).strftime(fmt)
        slots.append((s, e))
        cur += timedelta(minutes=slot_minutes)
    return slots

# ---------------------------
# Default / Procedural Inputs
# ---------------------------
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
SLOT_MINUTES = 90  # 1.5 hours per slot
SLOTS = generate_time_slots("07:30", "21:00", SLOT_MINUTES)  # 9 slots per day

# Rooms generation helper
def generate_rooms(floors=3, rooms_per_floor=6, labs=2):
    rooms = {}
    # Regular and Science Lab: letters A..Z per floor
    letters = [chr(ord("A") + i) for i in range(min(rooms_per_floor, 26))]
    for f in range(1, floors + 1):
        for i, letter in enumerate(letters, start=1):
            room_id = f"{f}{letter}"
            # alternate categories for variety
            category = "Regular" if i % 3 != 0 else "Science Lab"
            rooms[room_id] = {"category": category, "capacity": random.randint(15, 30)}
    # Computer labs
    for i in range(1, labs + 1):
        lab_id = f"Lab {i}"
        rooms[lab_id] = {"category": "Computer Lab", "capacity": random.randint(15, 30)}
    return rooms

# Sample teachers
def generate_teachers():
    # Each teacher: id, expertise list, availability (list of (day, slot_index))
    teachers = {
        "T_Ana": {
            "expertise": ["WebSys", "DBMS", "SysArc"],
            "availability": [(d, s) for d in DAYS for s in range(len(SLOTS)) if d != "Sunday"]
        },
        "T_Ben": {
            "expertise": ["Rizal", "ArcOrg", "QMethods"],
            "availability": [(d, s) for d in DAYS for s in range(len(SLOTS)) if s not in (0, 1)]
        },
        "T_Carol": {
            "expertise": ["QMethods", "WebSys"],
            "availability": [(d, s) for d in DAYS for s in range(len(SLOTS))]
        },
        "T_Dan": {
            "expertise": ["Capstone", "SysArc"],
            "availability": [(d, s) for d in DAYS for s in range(len(SLOTS)) if d not in ("Saturday", "Sunday")]
        },
    }
    return teachers

# Sample courses, sections, and subjects
def generate_sections_and_subjects():
    # Courses and sections
    courses = ["BSIT", "BSBA"]
    # sections per course
    sections = []
    for c in courses:
        for year in [1, 2]:
            for secnum in range(1, 3):  # small sample
                section_id = f"{c}-{year}0{secnum}"
                sections.append({"id": section_id, "course": c, "year": year})
    # Subjects per section (simplified)
    # Each subject: name, structure, units, modality, roomRequirement (or list)
    subject_catalog = {
        "WebSys": {"structure": "Single", "units": 3, "modality": "F2F", "roomRequirement": ["Computer Lab"]},
        "ArcOrg": {"structure": "Single", "units": 3, "modality": "F2F", "roomRequirement": ["Regular"]},
        "QMethods": {"structure": "Single", "units": 3, "modality": "F2F", "roomRequirement": ["Computer Lab", "Regular"]},
        "Rizal": {"structure": "Single", "units": 1.5, "modality": "Online", "roomRequirement": ["Regular"]},
        "Capstone": {"structure": "Split", "units": 3, "modality": "F2F", "roomRequirement": ["Computer Lab"]},
        "DBMS": {"structure": "Single", "units": 3, "modality": "F2F", "roomRequirement": ["Computer Lab"]},
    }
    # Assign subjects to each section (simple sample mapping)
    section_subjects = {}
    for sec in sections:
        if sec["course"] == "BSIT":
            subs = ["WebSys", "ArcOrg", "QMethods", "Rizal"]
        else:
            subs = ["ArcOrg", "QMethods", "Rizal"]
        section_subjects[sec["id"]] = [ (name, subject_catalog[name]) for name in subs ]
    return sections, section_subjects

# ---------------------------
# CSP Model Construction
# ---------------------------
def build_domains(sections, section_subjects, rooms, teachers, days=DAYS, slots=SLOTS):
    """
    For each (section, subject) create a variable name and domain of feasible assignments.
    Domain element: (day, slot_index, room_id, teacher_id)
    """
    domains = {}
    for sec in sections:
        sec_id = sec["id"]
        for subj_name, subj_info in section_subjects[sec_id]:
            var = f"{sec_id}__{subj_name}"
            domain = []
            # For split subjects: treat as single slot for lab component (2 units -> 1 slot) and lecture online (skip room)
            # For simplicity, schedule only the F2F component in room when structure is Split and roomRequirement exists.
            room_reqs = subj_info["roomRequirement"]
            modality = subj_info["modality"]
            for day in days:
                for s_idx in range(len(slots)):
                    # For online-only subjects, room can be "Online" and teacher must be available at that slot
                    for room_id, rinfo in rooms.items():
                        if modality == "Online":
                            # allow "Online" pseudo-room
                            room_choice = "Online"
                            # teacher must be able to teach subject and be available at (day, s_idx)
                            for t_id, tinfo in teachers.items():
                                if subj_name in tinfo["expertise"] and (day, s_idx) in tinfo["availability"]:
                                    domain.append((day, s_idx, room_choice, t_id))
                            # only once per slot-room-teacher combination
                            continue
                        # For F2F or Split lab component: room category must match one of room_reqs
                        if rinfo["category"] in room_reqs:
                            for t_id, tinfo in teachers.items():
                                if subj_name in tinfo["expertise"] and (day, s_idx) in tinfo["availability"]:
                                    domain.append((day, s_idx, room_id, t_id))
            # Remove duplicates
            domain = list(set(domain))
            if not domain:
                raise ValueError(f"No feasible domain for variable {var}. Check inputs (rooms/teachers/availability).")
            domains[var] = domain
    return domains

# ---------------------------
# Hard constraints and solver
# ---------------------------
def add_hard_constraints(problem, variables):
    """
    Add pairwise constraints:
      - Section continuity: same section variables must not share same (day, slot)
      - Teacher cannot be in two places at same (day, slot)
      - Room cannot host two classes at same (day, slot) (except 'Online')
    """
    var_list = list(variables.keys())
    # helper to extract day-slot-room-teacher
    def dsrt(val):
        return (val[0], val[1], val[2], val[3])

    # For every pair of variables, add constraints
    for a, b in itertools.combinations(var_list, 2):
        def pairwise_constraint(val_a, val_b, a=a, b=b):
            day_a, slot_a, room_a, teacher_a = val_a
            day_b, slot_b, room_b, teacher_b = val_b
            # If same section (variable name prefix before '__'), they must not overlap same day+slot
            sec_a = a.split("__")[0]
            sec_b = b.split("__")[0]
            if sec_a == sec_b and (day_a == day_b and slot_a == slot_b):
                return False
            # Teacher conflict
            if teacher_a == teacher_b and (day_a == day_b and slot_a == slot_b):
                return False
            # Room conflict (ignore Online pseudo-room)
            if room_a != "Online" and room_b != "Online" and room_a == room_b and (day_a == day_b and slot_a == slot_b):
                return False
            return True
        problem.addConstraint(FunctionConstraint(pairwise_constraint), (a, b))

# ---------------------------
# Soft constraints scoring
# ---------------------------
def score_solution(solution, slots=SLOTS, days=DAYS, e_emptyDays=1):
    """
    Lower score is better.
    Soft preferences:
      - Teacher lunch break: prefer at least one break after 3 consecutive classes (penalize long consecutive runs)
      - Balanced distribution: minimize variance of classes per day per section
      - Empty days: ensure each section has at least e_emptyDays days with zero classes (penalize otherwise)
    """
    # Build schedules
    teacher_schedule = defaultdict(list)  # teacher -> list of (day, slot)
    section_schedule = defaultdict(list)  # section -> list of (day, slot)
    for var, val in solution.items():
        sec = var.split("__")[0]
        day, slot_idx, room, teacher = val
        teacher_schedule[teacher].append((day, slot_idx))
        section_schedule[sec].append((day, slot_idx))

    score = 0.0

    # Teacher lunch break penalty: for each teacher, find longest consecutive run in a day; penalize runs >3
    for t, entries in teacher_schedule.items():
        by_day = defaultdict(list)
        for d, s in entries:
            by_day[d].append(s)
        for d, s_list in by_day.items():
            s_list_sorted = sorted(set(s_list))
            # compute consecutive runs
            run = 1
            max_run = 1
            for i in range(1, len(s_list_sorted)):
                if s_list_sorted[i] == s_list_sorted[i-1] + 1:
                    run += 1
                else:
                    max_run = max(max_run, run)
                    run = 1
            max_run = max(max_run, run)
            if max_run > 3:
                score += (max_run - 3) * 2.0  # penalty per extra consecutive slot

    # Balanced distribution and empty days per section
    for sec, entries in section_schedule.items():
        counts = Counter([d for d, s in entries])
        counts_list = [counts.get(d, 0) for d in days]
        mean = sum(counts_list) / len(days)
        variance = sum((x - mean) ** 2 for x in counts_list) / len(days)
        score += variance  # penalize variance
        # empty days
        empty_days = sum(1 for x in counts_list if x == 0)
        if empty_days < e_emptyDays:
            score += (e_emptyDays - empty_days) * 3.0

    # small random tie-breaker
    score += random.random() * 0.001
    return score

# ---------------------------
# Solve function
# ---------------------------
import time

def solve_schedule(sections, section_subjects, rooms, teachers, days=DAYS, slots=SLOTS, e_emptyDays=1, max_solutions=500, time_limit_seconds=20):
    domains = build_domains(sections, section_subjects, rooms, teachers, days, slots)
    problem = Problem()
    for var, domain in domains.items():
        problem.addVariable(var, domain)
    add_hard_constraints(problem, domains)

    # Use solution iterator instead of getSolutions()
    sol_iter = problem.getSolutionIter()
    best = None
    best_score = float("inf")
    count = 0
    start_time = time.time()

    try:
        for sol in sol_iter:
            count += 1
            sc = score_solution(sol, slots, days, e_emptyDays)
            if sc < best_score:
                best_score = sc
                best = sol
            # stop conditions
            if count >= max_solutions:
                break
            if time.time() - start_time > time_limit_seconds:
                break
    except Exception as e:
        # iterator may raise if search is interrupted; handle gracefully
        pass

    if best is None:
        raise RuntimeError("No feasible schedule found within search budget. Try relaxing inputs or increasing time_limit_seconds.")
    return best

# ---------------------------
# CSV Output
# ---------------------------
def write_csv(solution, filename="schedules.csv", slots=SLOTS):
    fieldnames = ["Section", "Subject", "Day", "StartTime", "EndTime", "Room", "Teacher", "Modality"]
    rows = []
    for var, val in solution.items():
        sec, subj = var.split("__")
        day, slot_idx, room, teacher = val
        start, end = slots[slot_idx]
        rows.append({
            "Section": sec,
            "Subject": subj,
            "Day": day,
            "StartTime": start,
            "EndTime": end,
            "Room": room,
            "Teacher": teacher,
            "Modality": "Online" if room == "Online" else "F2F"
        })
    # sort rows for readability
    rows.sort(key=lambda r: (r["Section"], DAYS.index(r["Day"]), r["StartTime"]))
    with open(filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
    return filename

# ---------------------------
# Main: Input -> Process -> Output
# ---------------------------
if __name__ == "__main__":
    # -----------------------
    # INPUT (procedural or manual)
    # -----------------------
    # Procedural defaults (you may edit these variables manually)
    f_floors = 3
    r_roomsPerFloor = 6
    m_modalityRatio = (30, 70)  # not used in this small sample but available
    s_sections = 4  # not directly used; sections generated procedurally
    e_emptyDays = 1  # prefer 1 empty day per section

    # Generate rooms, teachers, sections, subjects
    rooms = generate_rooms(floors=f_floors, rooms_per_floor=r_roomsPerFloor, labs=2)
    teachers = generate_teachers()
    sections, section_subjects = generate_sections_and_subjects()

    # -----------------------
    # PROCESS (CSP solve)
    # -----------------------
    print("Building CSP and searching for feasible schedules...")
    try:
        best_solution = solve_schedule(sections, section_subjects, rooms, teachers, DAYS, SLOTS, e_emptyDays, max_solutions=800)
    except Exception as e:
        print("Error during solving:", e)
        raise

    # -----------------------
    # OUTPUT (CSV)
    # -----------------------
    out_file = write_csv(best_solution, filename="schedules.csv", slots=SLOTS)
    print(f"Schedule written to {out_file}")
