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
  - Virtual: if the current modality is online, then there is no f2f in that schedule.
- Capacity: variable $V_{roomCapacity}$ is a numeric capacity value.

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
- For example: BSIT-105, BSIT-205, BSIT-107, BSIT-307s

## Subject ($S$)

Subjects are described by a structural type that determines units and modality.

| Subject Structure ($V_{subjectStructure}$) | Components | Units ($V_{units}$) | Modality ($V_{modality}$) | Room Requirement ($V_{roomRequirement}$) |
| :--- | :--- | :--- | :--- | :--- |
| Split Subject | Component A: Lab | 2 Units | $V_{modality}$ or $H_{hyflex}$ | $R_{roomCategory}$ |
|  | Component B: Lecture | 1 Unit | Online | Online Class |
| Single Subject | Standard | 1.5 or 3 Units | $V_{modality}$ or $H_{hyflex}$ | $R_{roomCategory}$ |

Subject Setup:
- Each course has a list of Room Category Requirements (or'ed)
    - examples
        - WebSys subject required "Computer Lab",
        - RizalLifeWorks subject required "Regular Room"
        - QMethods subject required "Computer Lab" or "Regular Room"
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
1. Room Capacity Limit: room assignments must not exceed $V_{roomCapacity}$ (maximum of 30).
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