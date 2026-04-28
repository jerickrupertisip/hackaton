CREATE TABLE room_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
);

CREATE TABLE rooms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category_id INTEGER NOT NULL,
    capacity INTEGER NOT NULL,
    floor INTEGER NOT NULL,
    FOREIGN KEY(category_id) REFERENCES room_categories(id)
);

CREATE TABLE subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    year INTEGER NOT NULL,
    semester INTEGER NOT NULL,
    units REAL NOT NULL,
    preferred_room INTEGER NOT NULL,
    modality TEXT,
    CHECK(units IN (1.5, 2, 3)),
    CHECK(modality IN ('hyflex_a', 'hyflex_b', 'online', 'face_to_face')),
    FOREIGN KEY(preferred_room) REFERENCES rooms(id)
);

CREATE TABLE enrollments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    year INTEGER NOT NULL,
    semester INTEGER NOT NULL,
    total_students INTEGER NOT NULL
);

CREATE TABLE teachers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    availability INTEGER NOT NULL,
    CHECK(availability IN (0, 1))
);

CREATE TABLE expertise (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    teacher_id INTEGER NOT NULL,
    subject_id INTEGER NOT NULL,
    FOREIGN KEY(teacher_id) REFERENCES teachers(id),
    FOREIGN KEY(subject_id) REFERENCES subjects(id)
);