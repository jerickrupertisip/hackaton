# Academic Scheduling System Specifications

## Entities and Attributes

### Teacher ($T$)
- Expertise: variable $V_{teacherExpertise}$ is a list of subjects the teacher can teach (for example, WebSys, Rizal, ArchOrg).
- Availability: variable $V_{teacherAvailability}$ describes the teacher's available time in a week. Each available time is described by Day, StartTime, EndTime and is associated with $V_{schedule}$.

### Rooms ($R$)
- Categories: variable $R_{roomCategory}$ indicates the room category and may be one of Regular, Science Lab, or Computer Lab.
  - Regular: for lecture or general subjects.
  - Science Lab: for science related.
  - Computer Lab: for IT or technical subjects.
  - Online: if the current modality is online, then there is no room in that schedule.

Rooms Setup:
- Computer Lab: Is located in any floors
    - identifier format: `Lab <lab-number>` (eg, Lab 1, Lab 2, Lab 3)
- Regular Room and Science Lab: Each floor has 1-26 unique Rooms, A through Z
    - identifier format: `<floor-number><room-letter>` (eg, 4A, 2B, 5C)

### Course and Year Level ($C$)
- Courses: variable $V_{courses}$ lists the courses BSBA, BSE, BSA, BSIT, BEED, BSED.
- Sections: variable $V_{courseSection}$ contains unique section identifiers in the pattern <course>-<year-level><section-number>.
- Year and Semester: variable $V_{yearSemester}$ indicates year levels 1st through 4th and semester 1st or 2nd.

### Section

Section identifier format: `<course>-<year-level><section>`
- sections are generated from the enrollment totals in `./data/enrollment/<course>.csv` — each row (year, semester) provides `total_students`, and the scheduler computes required sections from that value using the formula $\lceil \text{totalStudent} / R_{roomMaxCapacity} \rceil = \text{totalSections}$.
- For example: BSIT-105, BSIT-205, BSIT-107, BSIT-307

## Subject ($S$)

Subjects are described by a structural type that determines units and modality.

| Subject Structure ($V_{subjectStructure}$) | Components | Units ($V_{units}$) | Modality ($V_{modality}$) | Room Requirement ($V_{roomRequirement}$) |
| :--- | :--- | :--- | :--- | :--- |
| Split Subject | Component A: Lab | 2 Units | $V_{modality}$ or $H_{hyflex}$ | $R_{roomCategory}$ |
|  | Component B: Lecture | 1 Unit | Online | Online Class |
| Single Subject | Standard | 1.5 or 3 Units | $V_{modality}$ or $H_{hyflex}$ | $R_{roomCategory}$ |

Subject Setup:
- Subject has prefered room $R$
- Each Subject follows the Structural Type: Split Subject or Single Subject
- Subjects are categorized in Courses.
    - Example
        - BSIT has WebSys, ArcOrg, QMethods, Rizal, Capstone, SysArc, DBMS, etc...
        - BSBA has... idk.

#### Hyflex ($H_{hyflex}$)

- Hyflex eligibility: A Single Subject or a Split Subject's Component A: Lab may be designated Hyflex.
- Definition: Hyflex means the subject's modality alternates by week rather than being fixed for every scheduled meeting.
- Hyflex variants:
  - Hyflex-A: Week pattern = F2F, Online, F2F, Online, ...
  - Hyflex-B: Week pattern = Online, F2F, Online, F2F, ...
- Scheduling implications:
  - The scheduled time slot (day/time) for a Hyflex subject remains fixed in the weekly timetable, but the actual modality for that slot alternates by calendar week according to the Hyflex variant.
  - Room assignment and conflict detection must therefore consider week parity (or an equivalent week-indexing mechanism) so that occupancy is resolved per-week rather than only per-time-slot.
  - Teacher and section continuity constraints still apply: a teacher cannot be double-booked in the same week and time even if one of the classes is online that week.
  - Hyflex subjects must be tracked as a repeating weekly pattern with an initial phase (Hyflex-A starts F2F on week 1; Hyflex-B starts Online on week 1).

### Class Modality ($V_{modality}$)

- Online Class
- F2F Class
- Hyflex (weekly alternating modality; see Hyflex section)

### Schedule ($V_{schedule}$)

---

## Constraints (The Solver Rules)

1. Section Continuity: each section in $C_{courseSection}$ must not have overlapping $S_{schedule}$.
1. Teacher Lunch Break: 1-4 hours; prefer to schedule a break after 3 subjects for teacher.
1. Time Overlap Prevention: no two scheduled time intervals may overlap.
1. Balanced Distribution: prefer to distribute a section's schedule units evenly across the week while leaving $e_{emptyDays}$ empty days.
1. School Operation Hours $O_{operatingHours} = (\text{startTime}, \text{endTime})$: all scheduled times must fall within 07:30am and 9:00pm.
1. Complete Weekly Subject Schedule: every subject in the course must be assigned to an appropriate schedule during the week.
    - Example:
        - A section has subjects of [WebSys, ArcOrg, QMethods, Rizal], each subject must have a schedule in a week,
            - WebSys in Tuesday
            - ArcOrg and QMethods in Wednesday
            - Rizal in Sunday
1. Hyflex-aware Room Allocation: when a subject is Hyflex, room allocation and conflict checks must be evaluated per calendar week according to the Hyflex pattern. Room occupancy and conflicts should be resolved with awareness of the Hyflex weekly modality pattern.
1. Teacher Availability: all scheduled classes must align with the teacher's $V_{teacherAvailability}$.

---

## Additional Configuration Variables

| Variable | Description | Default / Range |
| :--- | :--- | :--- |
| $s_{sections}$ | Number of sections per courses. | 4 – 16 |
| $f_{floors}$ | Total number of floors in the building. | User defined |
| $r_{roomsPerFloor}$ | Total rooms per floor level. | User defined |
| $m_{modalityRatio}$ | Ratio of Online vs Face-to-Face for Single subjects. | Percentage (for example, 30/70) |
| $e_{emptyDays}$ | Number of days which not a single subject in section is not scheduled | 1-2 days |
| $R_{roomMaxCapacity}$ | Number of students allowed in Room | 30 (Fixed) |

## CSV Input and Output Formats

### Course CSV (Input)
- Purpose: Defines the subjects offered per course, year, and semester.
- Files Location: `./data/courses/<course>.csv`
- Fields:
  - `subject` → unique subject identifier
  - `year` → year level (1–4)
  - `semester` → semester (1 or 2)
  - `units` → numeric value (1.5, 2, or 3)
  - `preferred_room` → required room category (Regular, Science Lab, Computer Lab, Online)
  - `modality` → delivery mode (f2f, online, hyflex_a, hyflex_b)

### Teacher CSV (Input)
- Purpose: Defines teacher expertise and availability.
- Files Location: `./data/teachers.csv`
- Fields:
  - `teacher` → teacher’s name (Firstname Lastname)
  - `expertise` → list of subjects the teacher can teach
  - `availability` → weekly availability slots (Day, StartTime, EndTime)

### Schedule CSV (Output)
- Purpose: Generated by the solver; contains the final timetable for each section.
- Files Location: `./output/<course>-<year-level><section>.csv`
- Fields:
  - `subject` → subject name (must match Course CSV)
  - `unit` → number of units (must match Course CSV)
  - `day` → scheduled day of the week
  - `start_time` → class start time (HH:MM)
  - `end_time` → class end time (HH:MM)
  - `room` → assigned room (must match Course CSV `preferred_room`)
  - `modality` → delivery mode (must match Course CSV `modality`)
  - `teacher` → assigned teacher (must match Teacher CSV expertise and availability)

### Room CSV (Input)
- Purpose: Canonical inventory of physical and Online rooms used by the scheduler.
- Files Location: `./data/rooms.csv`
- Fields:
  - `room_id` → unique room identifier (e.g., `Lab 1`, `2A`, `Online`)
  - `category` → room category (Computer Lab, Regular, Science Lab, Online)
  - `capacity` → integer maximum students (physical rooms typically ≤ 30, if Online, then 0)
  - `floor` → integer floor number or 0 for Online

### Sections Enrollment CSV Input
- Purpose: Store total student counts per course, year, and semester for section‑generation and capacity checks.
- The number of courses in `./data/courses/` must be the same number as in `./data/enrollment/` 
- Files Location: `./data/enrollment/<course>.csv`

- Fields:  
  - `year` → year level
  - `semester` → semester
  - `total_students` → integer total enrolled students for that course/year/semester

### Notes
- Each section per semester has exactly 5 subjects.
- Sections within the same semester share the same subjects but differ in schedule times and room assignments.
- `<sub>Lec>` subjects are always online with `Online` room.
- Hyflex subjects alternate modality weekly but keep a fixed time slot.
- Dependency Rule:
  - The Schedule CSV output depends directly on the Course CSV and Teacher CSV.
  - `unit`, `room`, and `modality` values in the output must exactly match the Course CSV definitions.
  - `teacher` assignments must align with Teacher CSV expertise and availability.
  - The solver integrates these inputs to generate conflict-free schedules that respect all constraints.
