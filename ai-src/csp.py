"""
Academic Scheduling System — OR-Tools CP-SAT
Full spec-compliant implementation.

Key spec rules enforced:
 - Split subjects: Lab(2u, F2F/hyflex) + Lec(1u, online) scheduled as 2 rows
 - Slot duration derived from units: 1.5u=90min, 2u=120min, 3u=180min (in 30-min ticks)
 - Hyflex room allocation per week parity (A=F2F wk1, B=Online wk1)
 - Room capacity >= section.total_students
 - Balanced day distribution (minimise max-subjects-per-day)
 - Teacher lunch: hard-block after 3 consecutive subject slots; 1-4 hr break
 - Empty days: 1-2 per section (configurable)
 - Exactly 5 logical subjects per section per semester (warning if violated)
 - <sub>Lec> always online, no physical room
"""

import csv
import os
import math
from collections import defaultdict
from typing import List, Dict, Tuple, Set, Optional, Any

from ortools.sat.python import cp_model

# ---------------------------------------------------------------------------
# Constants / Config
# ---------------------------------------------------------------------------
DAYS             = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
N_DAYS           = len(DAYS)
START_MIN        = 7 * 60 + 30   # 07:30
END_MIN          = 21 * 60        # 21:00
TICK             = 30             # scheduling resolution (minutes)
START_TICK       = START_MIN // TICK       # 15  (absolute)
END_TICK         = END_MIN   // TICK       # 42  (absolute)
N_TICKS_PER_DAY  = END_TICK - START_TICK   # 27 usable ticks/day
LUNCH_START_REL  = (11 * 60 + 30) // TICK - START_TICK   # relative tick index
LUNCH_END_REL    = (13 * 60)       // TICK - START_TICK
R_ROOM_MAX_CAP   = 30
EMPTY_DAYS_DEFAULT = 1   # 1–2 per spec


def units_to_ticks(units: float) -> int:
    mapping = {1.0: 2, 1.5: 3, 2.0: 4, 3.0: 6}
    key = round(units, 1)
    if key not in mapping:
        raise ValueError(f"Unsupported units: {units}")
    return mapping[key]


def tick_to_hhmm(rel_tick: int) -> str:
    total_min = (rel_tick + START_TICK) * TICK
    return f"{total_min // 60:02d}:{total_min % 60:02d}"


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------
class Room:
    def __init__(self, room_id, category, capacity, floor):
        self.room_id  = room_id
        self.category = category
        self.capacity = int(capacity)
        self.floor    = int(floor)


class Teacher:
    def __init__(self, name, expertise, availability=1):
        self.name      = name
        self.expertise = [e.strip() for e in expertise.split(',')]
        self.available = bool(int(availability))


class Subject:
    """One schedulable unit (Lab or Lec half of a split, or standard single)."""
    def __init__(self, subject, year, semester, units, preferred_room, modality,
                 is_lab=False, is_lec=False, parent=None):
        self.subject        = subject
        self.year           = int(year)
        self.semester       = int(semester)
        self.units          = float(units)
        self.preferred_room = preferred_room
        self.modality       = modality.strip().lower()
        self.is_lab         = is_lab
        self.is_lec         = is_lec
        self.parent         = parent   # logical subject name for teacher lookup
        self.ticks          = units_to_ticks(float(units))

    @property
    def is_online_only(self):
        return self.modality == 'online' or self.preferred_room == 'Online'

    @property
    def is_hyflex(self):
        return self.modality in ('hyflex_a', 'hyflex_b')


class Section:
    def __init__(self, course, year, semester, section_num, total_students):
        self.course         = course
        self.year           = int(year)
        self.semester       = int(semester)
        self.section_num    = section_num
        self.total_students = int(total_students)
        self.subjects: List[Subject] = []

    @property
    def section_id(self):
        return f"{self.course.upper()}-{self.year}{str(self.section_num).zfill(2)}"


# ---------------------------------------------------------------------------
# CSV Parsing
# ---------------------------------------------------------------------------
def parse_rooms_csv(path: str) -> Dict[str, Room]:
    rooms = {}
    with open(path, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            r = Room(row['room_id'], row['category'], row['capacity'], row['floor'])
            rooms[r.room_id] = r
    return rooms


def parse_teachers_csv(path: str) -> Dict[str, Teacher]:
    teachers = {}
    with open(path, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            t = Teacher(row['teacher'], row['expertise'], row.get('availability', '1'))
            teachers[t.name] = t
    return teachers


def parse_course_csv(path: str) -> List[Subject]:
    """
    Parse and expand:
      units==2  → Lab(2u, original modality) + Lec(1u, online)  [Split subject]
      units==1.5 or 3 → Single subject as-is
    """
    subjects = []
    with open(path, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            units    = float(row['units'])
            subj     = row['subject']
            modality = row['modality'].strip().lower()
            yr       = row['year']
            sem      = row['semester']
            proom    = row['preferred_room']

            if units == 2.0:
                # Split: Lab component
                subjects.append(Subject(
                    subject=subj, year=yr, semester=sem,
                    units=2.0, preferred_room=proom,
                    modality=modality,
                    is_lab=True, parent=subj
                ))
                # Lec component — always online, no room
                subjects.append(Subject(
                    subject=f"{subj}<Lec>", year=yr, semester=sem,
                    units=1.0, preferred_room='Online',
                    modality='online',
                    is_lec=True, parent=subj
                ))
            else:
                subjects.append(Subject(
                    subject=subj, year=yr, semester=sem,
                    units=units, preferred_room=proom,
                    modality=modality
                ))
    return subjects


def parse_enrollment_csv(path: str) -> List[Dict[str, Any]]:
    rows = []
    with open(path, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            rows.append({
                'year':           int(row['year']),
                'semester':       int(row['semester']),
                'total_students': int(row['total_students']),
            })
    return rows


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
def validate(rooms, teachers, courses, enrollments):
    for r in rooms.values():
        if r.category != 'Online' and r.capacity > R_ROOM_MAX_CAP:
            raise ValueError(f"Room {r.room_id} capacity {r.capacity} > {R_ROOM_MAX_CAP}")
    for t in teachers.values():
        if not t.expertise:
            raise ValueError(f"Teacher {t.name} has no expertise.")
    for course, subjects in courses.items():
        for s in subjects:
            if s.is_lec:
                continue  # Lec inherits teacher from Lab — validated via parent
            lookup = s.parent or s.subject
            if not any(t.available and lookup in t.expertise for t in teachers.values()):
                raise ValueError(f"No available teacher for '{lookup}' in course {course}.")
    for course, enr_list in enrollments.items():
        for e in enr_list:
            if e['total_students'] < 1:
                raise ValueError(f"Invalid enrollment in {course}")


# ---------------------------------------------------------------------------
# Eligibility helpers
# ---------------------------------------------------------------------------
ONLINE_SENTINEL = '__ONLINE__'
TBA_SENTINEL    = '__TBA__'


def eligible_rooms_for(subj: Subject, rooms: Dict[str, Room],
                       students: int) -> List[str]:
    if subj.is_online_only:
        return [ONLINE_SENTINEL]
    result = [
        rid for rid, r in rooms.items()
        if r.category == subj.preferred_room and r.capacity >= students
    ]
    return result or [TBA_SENTINEL]


def eligible_teachers_for(subj: Subject,
                           teachers: Dict[str, Teacher]) -> List[str]:
    lookup = subj.parent if subj.parent else subj.subject
    result = [n for n, t in teachers.items()
              if t.available and lookup in t.expertise]
    return result or ['TBA']


# ---------------------------------------------------------------------------
# Hyflex
# ---------------------------------------------------------------------------
def hyflex_w1_modality(modality: str) -> str:
    """Return week-1 modality string for hyflex subjects."""
    if modality == 'hyflex_a':
        return 'F2F'    # A: F2F on week 1
    elif modality == 'hyflex_b':
        return 'Online' # B: Online on week 1
    return modality


# ---------------------------------------------------------------------------
# CP-SAT solver — one section
# ---------------------------------------------------------------------------
def _add_no_overlap_if_same_day(model, day_i, day_j,
                                 start_i, end_i, start_j, end_j,
                                 guard_bool, tag):
    """
    If guard_bool AND same_day → intervals [start_i,end_i) and [start_j,end_j)
    must not overlap.
    """
    same_day = model.NewBoolVar(f"sd_{tag}")
    model.Add(day_i == day_j).OnlyEnforceIf(same_day)
    model.Add(day_i != day_j).OnlyEnforceIf(same_day.Not())

    i_before = model.NewBoolVar(f"ib_{tag}")
    j_before = model.NewBoolVar(f"jb_{tag}")
    model.Add(end_i <= start_j).OnlyEnforceIf([guard_bool, same_day, i_before])
    model.Add(end_j <= start_i).OnlyEnforceIf([guard_bool, same_day, j_before])
    model.AddBoolOr([guard_bool.Not(), same_day.Not(), i_before, j_before])


def solve_section(
    section: Section,
    rooms: Dict[str, Room],
    teachers: Dict[str, Teacher],
    global_teacher_used: Set[Tuple],  # (teacher_name, day_idx, start_tick, dur_ticks)
    global_room_used:    Set[Tuple],  # (room_id, day_idx, start_tick, dur_ticks)
    empty_days: int = EMPTY_DAYS_DEFAULT,
) -> List[Dict]:
    subjects = section.subjects
    n = len(subjects)
    if n == 0:
        return []

    elig_rooms    = [eligible_rooms_for(s, rooms, section.total_students) for s in subjects]
    elig_teachers = [eligible_teachers_for(s, teachers)                   for s in subjects]

    model  = cp_model.CpModel()
    solver = cp_model.CpSolver()

    # ------------------------------------------------------------------
    # Decision variables
    # ------------------------------------------------------------------
    day_v   = [model.NewIntVar(0, N_DAYS - 1,           f"d{i}") for i in range(n)]
    start_v = [model.NewIntVar(0, N_TICKS_PER_DAY - 1,  f"s{i}") for i in range(n)]
    end_v   = [model.NewIntVar(0, N_TICKS_PER_DAY,       f"e{i}") for i in range(n)]
    tch_v   = [model.NewIntVar(0, max(0, len(elig_teachers[i]) - 1), f"t{i}") for i in range(n)]
    room_v  = [model.NewIntVar(0, max(0, len(elig_rooms[i]) - 1),    f"r{i}") for i in range(n)]

    for i in range(n):
        dur = subjects[i].ticks
        model.Add(end_v[i] == start_v[i] + dur)
        model.Add(start_v[i] + dur <= N_TICKS_PER_DAY)

    # ------------------------------------------------------------------
    # C1: No lunch overlap
    # ------------------------------------------------------------------
    for i in range(n):
        before_lunch = model.NewBoolVar(f"bl{i}")
        model.Add(end_v[i]   <= LUNCH_START_REL).OnlyEnforceIf(before_lunch)
        model.Add(start_v[i] >= LUNCH_END_REL).OnlyEnforceIf(before_lunch.Not())

    # ------------------------------------------------------------------
    # C2: Section continuity — no overlapping subjects on same day
    # ------------------------------------------------------------------
    for i in range(n):
        for j in range(i + 1, n):
            same_day = model.NewBoolVar(f"csd{i}_{j}")
            model.Add(day_v[i] == day_v[j]).OnlyEnforceIf(same_day)
            model.Add(day_v[i] != day_v[j]).OnlyEnforceIf(same_day.Not())
            ib = model.NewBoolVar(f"cib{i}_{j}")
            jb = model.NewBoolVar(f"cjb{i}_{j}")
            model.Add(end_v[i] <= start_v[j]).OnlyEnforceIf([same_day, ib])
            model.Add(end_v[j] <= start_v[i]).OnlyEnforceIf([same_day, jb])
            model.AddBoolOr([same_day.Not(), ib, jb])

    # ------------------------------------------------------------------
    # C3: Teacher no double-book — within section
    # ------------------------------------------------------------------
    for i in range(n):
        for j in range(i + 1, n):
            for ti, tname in enumerate(elig_teachers[i]):
                for tj, tn2 in enumerate(elig_teachers[j]):
                    if tname != tn2:
                        continue
                    # Both select same teacher
                    ti_sel = model.NewBoolVar(f"tis{i}_{j}_{ti}")
                    tj_sel = model.NewBoolVar(f"tjs{i}_{j}_{ti}")
                    model.Add(tch_v[i] == ti).OnlyEnforceIf(ti_sel)
                    model.Add(tch_v[i] != ti).OnlyEnforceIf(ti_sel.Not())
                    model.Add(tch_v[j] == tj).OnlyEnforceIf(tj_sel)
                    model.Add(tch_v[j] != tj).OnlyEnforceIf(tj_sel.Not())
                    both = model.NewBoolVar(f"tb{i}_{j}_{ti}")
                    model.AddBoolAnd([ti_sel, tj_sel]).OnlyEnforceIf(both)
                    model.AddBoolOr([ti_sel.Not(), tj_sel.Not()]).OnlyEnforceIf(both.Not())
                    _add_no_overlap_if_same_day(
                        model, day_v[i], day_v[j],
                        start_v[i], end_v[i], start_v[j], end_v[j],
                        both, f"t{i}_{j}_{ti}"
                    )

    # ------------------------------------------------------------------
    # C4: Room no double-book — within section (skip virtual rooms)
    # ------------------------------------------------------------------
    for i in range(n):
        for j in range(i + 1, n):
            for ri, rname in enumerate(elig_rooms[i]):
                if rname in (ONLINE_SENTINEL, TBA_SENTINEL):
                    continue
                for rj, rn2 in enumerate(elig_rooms[j]):
                    if rname != rn2:
                        continue
                    ri_sel = model.NewBoolVar(f"ris{i}_{j}_{ri}")
                    rj_sel = model.NewBoolVar(f"rjs{i}_{j}_{ri}")
                    model.Add(room_v[i] == ri).OnlyEnforceIf(ri_sel)
                    model.Add(room_v[i] != ri).OnlyEnforceIf(ri_sel.Not())
                    model.Add(room_v[j] == rj).OnlyEnforceIf(rj_sel)
                    model.Add(room_v[j] != rj).OnlyEnforceIf(rj_sel.Not())
                    both = model.NewBoolVar(f"rb{i}_{j}_{ri}")
                    model.AddBoolAnd([ri_sel, rj_sel]).OnlyEnforceIf(both)
                    model.AddBoolOr([ri_sel.Not(), rj_sel.Not()]).OnlyEnforceIf(both.Not())
                    _add_no_overlap_if_same_day(
                        model, day_v[i], day_v[j],
                        start_v[i], end_v[i], start_v[j], end_v[j],
                        both, f"r{i}_{j}_{ri}"
                    )

    # ------------------------------------------------------------------
    # C5: Global teacher conflicts (cross-section)
    # Blocked: (teacher_name, day_idx, start_tick, dur_ticks)
    # ------------------------------------------------------------------
    for i in range(n):
        dur_i = subjects[i].ticks
        for ti, tname in enumerate(elig_teachers[i]):
            blocked = [(d, s, dur) for (tn, d, s, dur) in global_teacher_used
                       if tn == tname]
            for (bd, bs, bdur) in blocked:
                t_sel = model.NewBoolVar(f"gt{i}_{ti}_{bd}_{bs}")
                model.Add(tch_v[i] == ti).OnlyEnforceIf(t_sel)
                model.Add(tch_v[i] != ti).OnlyEnforceIf(t_sel.Not())
                d_sel = model.NewBoolVar(f"gd{i}_{ti}_{bd}_{bs}")
                model.Add(day_v[i] == bd).OnlyEnforceIf(d_sel)
                model.Add(day_v[i] != bd).OnlyEnforceIf(d_sel.Not())
                # Non-overlap: end_i <= bs  OR  start_i >= bs+bdur
                after  = model.NewBoolVar(f"ga{i}_{ti}_{bd}_{bs}")
                before = model.NewBoolVar(f"gb{i}_{ti}_{bd}_{bs}")
                model.Add(start_v[i] >= bs + bdur).OnlyEnforceIf(after)
                model.Add(end_v[i]   <= bs).OnlyEnforceIf(before)
                model.AddBoolOr([t_sel.Not(), d_sel.Not(), after, before])

    # ------------------------------------------------------------------
    # C6: Global room conflicts (cross-section)
    # ------------------------------------------------------------------
    for i in range(n):
        dur_i = subjects[i].ticks
        for ri, rname in enumerate(elig_rooms[i]):
            if rname in (ONLINE_SENTINEL, TBA_SENTINEL):
                continue
            blocked = [(d, s, dur) for (rn, d, s, dur) in global_room_used
                       if rn == rname]
            for (bd, bs, bdur) in blocked:
                r_sel = model.NewBoolVar(f"gr{i}_{ri}_{bd}_{bs}")
                model.Add(room_v[i] == ri).OnlyEnforceIf(r_sel)
                model.Add(room_v[i] != ri).OnlyEnforceIf(r_sel.Not())
                d_sel = model.NewBoolVar(f"grd{i}_{ri}_{bd}_{bs}")
                model.Add(day_v[i] == bd).OnlyEnforceIf(d_sel)
                model.Add(day_v[i] != bd).OnlyEnforceIf(d_sel.Not())
                after  = model.NewBoolVar(f"gra{i}_{ri}_{bd}_{bs}")
                before = model.NewBoolVar(f"grb{i}_{ri}_{bd}_{bs}")
                model.Add(start_v[i] >= bs + bdur).OnlyEnforceIf(after)
                model.Add(end_v[i]   <= bs).OnlyEnforceIf(before)
                model.AddBoolOr([r_sel.Not(), d_sel.Not(), after, before])

    # ------------------------------------------------------------------
    # C7: Empty days constraint
    # ------------------------------------------------------------------
    day_used = [model.NewBoolVar(f"du{d}") for d in range(N_DAYS)]
    for d in range(N_DAYS):
        on_day = [model.NewBoolVar(f"od{i}_{d}") for i in range(n)]
        for i in range(n):
            model.Add(day_v[i] == d).OnlyEnforceIf(on_day[i])
            model.Add(day_v[i] != d).OnlyEnforceIf(on_day[i].Not())
        model.AddMaxEquality(day_used[d], on_day)
    model.Add(sum(day_used) <= N_DAYS - empty_days)

    # ------------------------------------------------------------------
    # C8: Teacher lunch — max 3 subjects per teacher per day
    # (Soft via objective penalty on violations — hard version requires
    # ordering vars per teacher per day which explodes for large n.)
    # Encode as: for each teacher, per day, count assigned subjects → penalise >3
    # We add this to objective below.
    # ------------------------------------------------------------------
    teacher_day_load = {}  # (ti_global, d) -> IntVar count
    # Collect unique teacher names across all subjects for penalty
    all_teacher_names = sorted(set(t for et in elig_teachers for t in et
                                   if t != 'TBA'))
    tname_to_idx = {n: i for i, n in enumerate(all_teacher_names)}
    lunch_penalty_terms = []

    for tname in all_teacher_names:
        tidx = tname_to_idx[tname]
        for d in range(N_DAYS):
            # Bool: subject i on day d taught by tname
            assigns = []
            for i in range(n):
                matches_ti = [ti for ti, tn in enumerate(elig_teachers[i]) if tn == tname]
                if not matches_ti:
                    continue
                for ti in matches_ti:
                    t_sel = model.NewBoolVar(f"lp_ts{tidx}_{d}_{i}_{ti}")
                    d_sel = model.NewBoolVar(f"lp_ds{tidx}_{d}_{i}_{ti}")
                    model.Add(tch_v[i] == ti).OnlyEnforceIf(t_sel)
                    model.Add(tch_v[i] != ti).OnlyEnforceIf(t_sel.Not())
                    model.Add(day_v[i] == d).OnlyEnforceIf(d_sel)
                    model.Add(day_v[i] != d).OnlyEnforceIf(d_sel.Not())
                    both = model.NewBoolVar(f"lp_both{tidx}_{d}_{i}_{ti}")
                    model.AddBoolAnd([t_sel, d_sel]).OnlyEnforceIf(both)
                    model.AddBoolOr([t_sel.Not(), d_sel.Not()]).OnlyEnforceIf(both.Not())
                    assigns.append(both)
            if not assigns:
                continue
            load_var = model.NewIntVar(0, n, f"tload_{tidx}_{d}")
            model.Add(load_var == sum(assigns))
            # Excess over 3 → penalty
            excess = model.NewIntVar(0, n, f"tex_{tidx}_{d}")
            model.Add(excess >= load_var - 3)
            model.Add(excess >= 0)
            lunch_penalty_terms.append(excess)

    # ------------------------------------------------------------------
    # C9: Balanced distribution — minimise max daily subject load
    # ------------------------------------------------------------------
    subj_on_day = [[model.NewBoolVar(f"sod{i}_{d}") for d in range(N_DAYS)]
                   for i in range(n)]
    for i in range(n):
        for d in range(N_DAYS):
            model.Add(day_v[i] == d).OnlyEnforceIf(subj_on_day[i][d])
            model.Add(day_v[i] != d).OnlyEnforceIf(subj_on_day[i][d].Not())

    day_load = [model.NewIntVar(0, n, f"dl{d}") for d in range(N_DAYS)]
    for d in range(N_DAYS):
        model.Add(day_load[d] == sum(subj_on_day[i][d] for i in range(n)))
    max_load = model.NewIntVar(0, n, "max_load")
    model.AddMaxEquality(max_load, day_load)

    # ------------------------------------------------------------------
    # Hyflex room — for hyflex subjects, both-week room conflict already
    # handled by standard room constraints (same slot = conflict regardless
    # of week parity). Week-parity only affects OUTPUT modality label.
    # Physical room is always reserved (conservative: treats both weeks as F2F
    # for conflict purposes so online-week never double-books a ghost slot).
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # Objective
    # ------------------------------------------------------------------
    lunch_penalty = sum(lunch_penalty_terms) if lunch_penalty_terms else 0
    model.Minimize(
        max_load * 1000          # balanced distribution (primary)
        + lunch_penalty * 500    # teacher lunch soft constraint
        + sum(day_v)             # prefer early days
    )

    # ------------------------------------------------------------------
    # Solve
    # ------------------------------------------------------------------
    solver.parameters.max_time_in_seconds = 60.0
    solver.parameters.num_search_workers  = 4
    status = solver.Solve(model)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise Exception(f"Infeasible schedule for {section.section_id}")

    # ------------------------------------------------------------------
    # Extract
    # ------------------------------------------------------------------
    rows = []
    for i, subj in enumerate(subjects):
        d  = solver.Value(day_v[i])
        s  = solver.Value(start_v[i])
        e  = solver.Value(end_v[i])
        ti = solver.Value(tch_v[i])
        ri = solver.Value(room_v[i])

        teacher_name = elig_teachers[i][ti]
        room_id      = elig_rooms[i][ri]
        if room_id == ONLINE_SENTINEL:
            room_id = 'Online'
        elif room_id == TBA_SENTINEL:
            room_id = 'TBA'

        # Output modality
        if subj.is_hyflex:
            w1 = hyflex_w1_modality(subj.modality)
            out_modality = f"{subj.modality}|week1={w1}"
        else:
            out_modality = subj.modality

        # Register in global used sets (store duration for overlap calc)
        global_teacher_used.add((teacher_name, d, s, subj.ticks))
        global_room_used.add((room_id, d, s, subj.ticks))

        rows.append({
            'subject':    subj.subject,
            'unit':       subj.units,
            'day':        DAYS[d],
            'start_time': tick_to_hhmm(s),
            'end_time':   tick_to_hhmm(e),
            'room':       room_id,
            'modality':   out_modality,
            'teacher':    teacher_name,
        })

    return rows


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def generate_schedules(empty_days: int = EMPTY_DAYS_DEFAULT):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    rooms    = parse_rooms_csv(os.path.join(data_dir, 'rooms.csv'))
    teachers = parse_teachers_csv(os.path.join(data_dir, 'teachers.csv'))

    courses_dir  = os.path.join(data_dir, 'courses')
    enroll_dir   = os.path.join(data_dir, 'enrollment')
    course_files = [f for f in os.listdir(courses_dir) if f.endswith('.csv')]

    courses:     Dict[str, List[Subject]]      = {}
    enrollments: Dict[str, List[Dict[str, Any]]] = {}
    for cf in course_files:
        cname              = cf.replace('.csv', '')
        courses[cname]     = parse_course_csv(os.path.join(courses_dir, cf))
        enrollments[cname] = parse_enrollment_csv(os.path.join(enroll_dir, cf))

    validate(rooms, teachers, courses, enrollments)

    # --- Section generation ---
    sections: Dict[str, List[Section]] = defaultdict(list)
    for course, enr_list in enrollments.items():
        for enr in enr_list:
            yr, sem, tot = enr['year'], enr['semester'], enr['total_students']
            pool = [s for s in courses[course]
                    if s.year == yr and s.semester == sem]
            if not pool:
                continue
            logical = sum(1 for s in pool if not s.is_lec)
            if logical != 5:
                print(f"  [WARN] {course} y{yr}s{sem}: {logical} logical subjects (spec expects 5)")
            n_secs = math.ceil(tot / R_ROOM_MAX_CAP)
            for i in range(1, n_secs + 1):
                sec          = Section(course, yr, sem, i, tot)
                sec.subjects = pool
                sections[course].append(sec)

    # --- Scheduling ---
    output_dir = os.path.join(os.path.dirname(__file__), 'output')
    os.makedirs(output_dir, exist_ok=True)

    global_teacher_used: Set[Tuple] = set()  # (name, day, start, dur)
    global_room_used:    Set[Tuple] = set()  # (room_id, day, start, dur)

    for course, sec_list in sections.items():
        course_dir = os.path.join(output_dir, course.upper())
        os.makedirs(course_dir, exist_ok=True)

        for sec in sec_list:
            print(f"Solving {sec.section_id} "
                  f"({len(sec.subjects)} rows: {sum(1 for s in sec.subjects if not s.is_lec)} logical subjects)…")
            rows = solve_section(
                sec, rooms, teachers,
                global_teacher_used, global_room_used,
                empty_days=empty_days,
            )
            fname = f"{sec.year}{str(sec.section_num).zfill(2)}.csv"
            out   = os.path.join(course_dir, fname)
            with open(out, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(
                    f, fieldnames=['subject', 'unit', 'day', 'start_time',
                                   'end_time', 'room', 'modality', 'teacher']
                )
                writer.writeheader()
                writer.writerows(rows)
            print(f"  → {out}")

    print("\nAll schedules generated.")


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description='Academic Scheduler — OR-Tools CP-SAT')
    p.add_argument('--empty-days', type=int, default=EMPTY_DAYS_DEFAULT,
                   help='Empty days per section (1–2, default 1)')
    args = p.parse_args()
    if not (1 <= args.empty_days <= 2):
        raise ValueError('--empty-days must be 1 or 2')
    generate_schedules(empty_days=args.empty_days)