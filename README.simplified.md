# Academic Scheduling System Specifications (CSP Revision — Plain English Variables with Math Intact)

## Entities and Attributes

### Teacher ($T$)
- Expertise: variable $V_{teacherExpertise}$ is a list of subjects the teacher can teach (for example, WebSys, Rizal, ArchOrg).
- Availability: variable $V_{teacherAvailability}$ describes the teacher's available time in a week. Each available time is described by Day, StartTime, EndTime and is associated with $V_{schedule}$.

Teacher lunch break: 1-4 hours

### Rooms ($R$)
- Categories: variable $R_{roomCategory}$ indicates the room category and may be one of Regular, Science Lab, or Computer Lab.
  - Regular: for lecture or general subjects.
  - Science Lab: for science related.
  - Computer Lab: for IT or technical subjects.
  - Virtual: if the current modality is online, then there is no f2f in that schedule.
- Capacity: variable $V_{roomCapacity}$ is a numeric capacity value with a maximum of 30.

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
| Split Subject | Component A: Lab | 2 Units | $V_{modality}$ | $R_{roomCategory}$ |
|  | Component B: Lecture | 1 Unit | Online | Online Class |
| Single Subject | Standard | 1.5 or 3 Units | $V_{modality}$ | $R_{roomCategory}$ |

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

### Class Modality ($V_{modality}$)

- Online Class
- F2F Class

### Schedule ($V_{schedule}$)

---

## Constraints (The Solver Rules)

1. Section Continuity: each section in $C_{courseSection}$ must not have overlapping $S_{schedule}$.
1. Teacher Lunch Break: prefer to schedule a break after 3 subjects for teacher.
1. Time Overlap Prevention: no two scheduled time intervals may overlap.
1. Balanced Distribution: prefer to distribute a section's schedule units evenly across the week while leaving $e_{emptyDays}$ empty days.
1. School Operation Hours $O_{operatingHours} = (\text{startTime}, \text{endTime})$: all scheduled times must fall within 07:30am and 9:00pm.
1. Complete Weekly Subject Schedule: every subject in the course must be assigned to an appropriate schedule during the week.
    - Example:
        - A section has subjects of [WebSys, ArcOrg, QMethods, Rizal], each subject must have a schedule in a week,
            - WebSys in Tuesday
            - ArcOrg and QMethods in Wednesday
            - Rizal in Sunday

---

## Additional Configuration Variables

| Variable | Description | Default / Range |
| :--- | :--- | :--- |
| $s_{sections}$ | Number of sections per courses. | 4 – 16 |
| $f_{floors}$ | Total number of floors in the building. | User defined |
| $r_{roomsPerFloor}$ | Total rooms per floor level. | User defined |
| $m_{modalityRatio}$ | Ratio of Online vs Face-to-Face for Single subjects. | Percentage (for example, 30/70) |
| $e_{emptyDays}$ | Number of days which not a single subject in section is not scheduled | 1-2 days |