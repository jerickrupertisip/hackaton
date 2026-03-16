# Academic Scheduling System Specifications

## 1. Entities and Attributes

### Teacher ($T$)
- Expertise: variable $V_{teacherExpertise}$ is a list of subjects or skills the teacher can teach (for example, BSIT, BSBA).
- Availability: variable $V_{teacherAvailability}$ describes the teacher's available time windows. Each window is described by Day, StartTime, EndTime and is associated with $V_{slot}$.