# Academic Scheduling System Specifications (CSP Revision)

## 1. Entities and Attributes

### Teacher ($T$)
* Expertise ($T_{expertise}$): List of Subjects/Skills they can teach (e.g., BSIT, BSBA).
* Availability ($T_{availability}$): Set of available windows $(Day, StartTime, EndTime)$ mapped to $V_{slot}$.

### Rooms ($R$)
* Categories ($R_{type}$):
    * Regular: For Lecture/General subjects.
    * Science Lab: For specialized Science experiments.
    * Computer Lab: For IT/Technical subjects.
* Capacity ($C_{roomCapacity}$): Constant $\le 30$.
* Configuration: Defined by `<floor number><room-letter>` (e.g., 1A, 2B).

### Course and Year Level ($C$)
* Programs: BSBA, BSE, BSA, BSIT, BEED, BSED.
* Sections ($C_{section}$): Unique identifiers `<course>-<year-level><section-number>`.
* Year/Semester: 1st–4th Year, 1st/2nd Semester.

---

## 2. Subject Logic ($S$)

Subjects are categorized into two structural types which determine their Units and Modality.

| Subject Structure ($S_{structure}$) | Components | Units ($U$) | Modality ($M_{modality}$) | Room Requirement ($R_{req}$) |
| :--- | :--- | :--- | :--- | :--- |
| Split Subject | Component A: Lab | 2 Units | F2F | Science/Computer Lab |
| | Component B: Lecture | 1 Unit | Online | Virtual / N/A |
| Single Subject | Standard | 1.5 or 3 Units | F2F or Online | Regular Room (if F2F) |

---

## 3. Constraints (The Solver Rules)

### A. Resource Conflict Constraints (Hard)
* 1. Teacher Conflict: $V_{slot}(A_1) \cap V_{slot}(A_2) = \emptyset$ if $T(A_1) = T(A_2)$.
* 2. Room Conflict: $V_{slot}(A_1) \cap V_{slot}(A_2) = \emptyset$ if $R(A_1) = R(A_2)$.
* 3. Time Overlap Prevention: No overlapping intervals between slots.

### B. Subject & Curriculum Constraints (Hard)
* 4. Expertise Match: $S_{requirement} \in T_{expertise}$.
* 5. Structural Requirement: Strict adherence to Split (2 assignments) vs Single (1 assignment).
* 6. Split-Subject Day Separation: $Day(Lab) \neq Day(Lecture)$.
* 7. Complete Weekly Assignment: All curriculum subjects must be assigned.

### C. Section & Room Logic (Hard)
* 8. Section Continuity: $V_{slot}(S_x) \cap V_{slot}(S_y) = \emptyset$ for the same $C_{section}$.
* 9. Maximum Daily Section Load: Total units per day $\le 9$.
* 10. Room Type Exclusion: $Online$ modality uses "Virtual" rooms only.

### D. Temporal & Modality Constraints (Hard)
* 11. Temporal Range ($V_{operatingHours}$): 07:30 to 21:00.
* 12. Time Granularity ($V_{granularity}$): All times must be divisible by 30 minutes.
* 13. Randomized Placement: Stochastic assignment within valid constraints.
* 14. Modality Threshold ($V_{timeThreshold}$): $M_{modality}$ consistency based on $Gap(S_1, S_2)$.
* 15. Teacher Rest/Burnout: Prioritize 1–3 hours rest after 3-unit blocks or modality shifts.

### E. Optimization Preferences (Soft Constraints)
* 16. Teacher Lunch Break: Gap after 4 consecutive hours.
* 17. Compact Schedule: Minimize gaps for $C_{section}$.
* 18. Balanced Distribution: Spread units across the week.
* 19. Room-Subject Affinity: Specialized equipment matching.

---

### 4.2. Procedural Generation Logic (Dynamic)

The following parameters are procedurally generated to create a diverse search space for the CSP solver. All generation is bounded by configurable constraints to ensure the resulting data remains realistic for academic use.

* Teacher Profile Generation:
    * Expertise Assignment: Each teacher is randomly assigned 1 to 4 unique expertise tags from the predefined program list (`BSBA`, `BSE`, `BSA`, `BSIT`, `BEED`, `BSED`).
    * Availability Generation: Randomly generates "Available Windows" per teacher. The system ensures that total availability exceeds the average workload to maintain solvability.

* Program-to-Subject Mapping (Curriculum Generation):
    * Curriculum Definition: The system generates a dictionary mapping each Course to a Set of Subjects.
    * Subject Generation Logic:
        * For each Course in $\{BSBA, BSE, BSA, BSIT, BEED, BSED\}$, a set of 8–10 subjects is instantiated.
        * Each Subject object includes: `SubjectName`, `Units`, `S_structure` (Split/Single), and `R_req`.

* Section Population ($N_{sections}$):
    * Range: Configurable between 4 and 16 sections per program.
    * Identifier Generation: Creates unique `<course>-<year>-<section>` strings (e.g., `BSIT-101`).
    * Workload Injection: For every generated section, the system performs a lookup in the Program-to-Subject Mapping and assigns the corresponding set of subjects to that section's specific $V_{assignment}$ pool.

* Constraint Parameter Randomization:
    * Modality Bias: A global `online_ratio` determines the probability of a Single subject being assigned an `Online` modality.
    * Gap Threshold ($V_{timeThreshold}$): Randomized per simulation between 4 and 8 hours to test student/teacher schedule flexibility.

### 4.3. Global Configuration Variables
These constants act as "knobs" for the CSP solver to adjust behavior per institution:

| Variable | Description | Default / Range |
| :--- | :--- | :--- |
| $V_{sections}$ | Number of sections per program. | 4 – 16 |
| $V_{floors}$ | Total floors in building. | User Defined |
| $V_{roomsPerFloor}$ | Total rooms per floor level. | User Defined |
| $V_{modalityRatio}$ | Ratio of Online vs F2F single subjects. | Percentage (e.g., 30/70) |