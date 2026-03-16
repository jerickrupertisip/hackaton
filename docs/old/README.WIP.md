
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

### 4.3. Global Configuration Variables
These constants act as "knobs" for the CSP solver to adjust behavior per institution:

| Variable | Description | Default / Range |
| :--- | :--- | :--- |
| $V_{sections}$ | Number of sections per program. | 4 – 16 |
| $V_{floors}$ | Total floors in building. | User Defined |
| $V_{roomsPerFloor}$ | Total rooms per floor level. | User Defined |
| $V_{modalityRatio}$ | Ratio of Online vs F2F single subjects. | Percentage (e.g., 30/70) |