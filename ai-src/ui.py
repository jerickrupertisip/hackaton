import FreeSimpleGUI as sg
import csv
import os

# --- Dynamic Data Discovery ---
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
COURSES_DIR = os.path.join(DATA_DIR, 'courses')

# --- Helper: List all course CSVs ---
def get_course_files():
    return [f for f in os.listdir(COURSES_DIR) if f.endswith('.csv')]

# --- Helper: Get course codes (e.g., BSIT, BEED, etc.) ---
def get_course_codes():
    return [f.replace('.csv', '').upper() for f in get_course_files()]

# --- Helper: Parse CSV headers for a course ---
def get_course_schema(course_code):
    path = os.path.join(COURSES_DIR, f"{course_code.lower()}.csv")
    if not os.path.exists(path):
        return []
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        try:
            headers = next(reader)
            return [h.replace('_', ' ').title() for h in headers]
        except StopIteration:
            return []

# --- Helper: Parse options for certain fields (from all courses) ---
def get_field_options(field):
    # Aggregate all unique values for a field across all course CSVs
    values = set()
    for code in get_course_codes():
        path = os.path.join(COURSES_DIR, f"{code.lower()}.csv")
        if not os.path.exists(path):
            continue
        with open(path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if field in row:
                    values.add(row[field])
    return sorted(values)

# --- Internal Data Storage ---
raw_data_storage = {"Teachers": [], "Rooms": [], "Courses": {}}

# --- Static schemas for Teachers and Rooms (from CSVs) ---
TEACHERS_CSV = os.path.join(DATA_DIR, 'teachers.csv')
ROOMS_CSV = os.path.join(DATA_DIR, 'rooms.csv')

def get_teachers_schema():
    with open(TEACHERS_CSV, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        return [h.replace('_', ' ').title() for h in next(reader)]

def get_rooms_schema():
    with open(ROOMS_CSV, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        return [h.replace('_', ' ').title() for h in next(reader)]

# --- Dynamic schema dictionary ---
def get_schema(category, course_code=None):
    if category == "Teachers":
        return get_teachers_schema()
    elif category == "Rooms":
        return get_rooms_schema()
    elif category == "Courses" and course_code:
        return get_course_schema(course_code)
    return []

# --- Dynamic options dictionary (for dropdowns) ---
def get_options(field, category, course_code=None):
    if category == "Courses" and course_code:
        # Use field options from all courses for consistency
        return get_field_options(field)
    # For Teachers/Rooms, no dropdowns by default
    return []

# --- Internal Data Storage ---
raw_data_storage = {"Teachers": [], "Rooms": [], "Courses": []}

schema = {
    "Teachers": ["Teacher Name", "Expertise", "Availability"],
    "Rooms": ["Room ID", "Category", "Capacity", "Floor"],
    "Courses": ["Subject", "Year", "Semester", "Units", "Preferred Room", "Modality"]
}

options = {
    "Category": ["Regular", "Science Lab", "Computer Lab"],
    "Year": ["1st", "2nd", "3rd", "4th"],
    "Semester": ["1st", "2nd"],
    "Modality": ["f2f", "online", "hyflex_a", "hyflex_b"],
    "Preferred Room": ["Regular", "Science Lab", "Computer Lab", "Online"]
}



# --- CSV Functions (Dynamic) ---
def save_to_raw_csv(category, data_list, course_code=None):
    if category == "Courses" and course_code:
        path = os.path.join(COURSES_DIR, f"{course_code.lower()}.csv")
        schema_headers = get_course_schema(course_code)
    elif category == "Teachers":
        path = TEACHERS_CSV
        schema_headers = get_teachers_schema()
    elif category == "Rooms":
        path = ROOMS_CSV
        schema_headers = get_rooms_schema()
    else:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([h.lower().replace(" ", "_") for h in schema_headers])
        writer.writerows(data_list)

def load_from_raw_csv(category, course_code=None):
    if category == "Courses" and course_code:
        path = os.path.join(COURSES_DIR, f"{course_code.lower()}.csv")
    elif category == "Teachers":
        path = TEACHERS_CSV
    elif category == "Rooms":
        path = ROOMS_CSV
    else:
        return []
    if not os.path.exists(path):
        return []
    with open(path, mode='r', newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        try:
            next(reader)  # skip header
            # Only include rows that have at least one non-empty cell (ignoring pure blank lines)
            return [row for row in reader if any(cell.strip() for cell in row)]
        except StopIteration:
            return []



# --- UI Helpers ---
def create_input_fields(num_fields):
    FIELD_H = 62
    inner = []
    for i in range(num_fields):
        field_layout = [
            [sg.Text("", key=f"-L{i}-", font=("Arial", 10, "bold"), pad=((8, 5), (8, 2)))],
            [sg.Input(key=f"-I{i}-", size=(44, 1), pad=((8, 5), (0, 8)), visible=True),
             sg.Combo([], key=f"-C{i}-", size=(43, 1), pad=((8, 5), (0, 8)), visible=False, readonly=True)]
        ]
        inner.append([
            sg.Column(
                field_layout,
                key=f"-COL{i}-",
                visible=False,
                pad=(0, 0),
                size=(None, FIELD_H)
            )
        ])
    scrollable_col = sg.Column(
        inner,
        scrollable=True,
        vertical_scroll_only=True,
        size=(480, 175),
        expand_x=True,
        key="-FORM-SCROLL-",
        pad=(5, 5)
    )
    return [[scrollable_col]]



# --- Main Layout ---
sg.theme('SystemDefaultForReal')

course_codes = get_course_codes()
default_course = course_codes[0] if course_codes else "BSIT"
categories = ["Teachers", "Rooms", "Courses"]
current_cat = "Teachers"
current_course = default_course

def get_max_cols():
    # Find the max number of columns among all schemas
    max_cols = len(get_teachers_schema())
    max_cols = max(max_cols, len(get_rooms_schema()))
    for code in course_codes:
        max_cols = max(max_cols, len(get_course_schema(code)))
    return max_cols

MAX_COLS = get_max_cols()
placeholder_headings = [" " * (i + 1) for i in range(MAX_COLS)]

layout = [
    [sg.Text("Academic Scheduling System", font=("Arial", 16, "bold"))],
    [sg.Button("Manage Teachers"), sg.Button("Manage Rooms"),
     sg.Button("Manage Courses"),
     sg.Combo(course_codes, default_course, key="-COURSE_SELECT-", readonly=True, visible=True, enable_events=True),
     sg.VerticalSeparator(), sg.Button("Load Saved Progress", button_color="grey")],

    [sg.HSeparator(pad=(0, 15))],

    [sg.Text("Currently Editing: ", font=("Arial", 10, "italic")),
     sg.Text("Teachers", key="-CAT_DISPLAY-", text_color="#1a73e8", font=("Arial", 11, "bold")),
     sg.Text("", key="-COURSE_DISPLAY-", text_color="#e6731a", font=("Arial", 11, "bold"))],

    [sg.Table(
        values=[],
        headings=placeholder_headings,
        auto_size_columns=True,
        num_rows=10,
        key="-TABLE-",
        expand_x=True,
        enable_events=True,
        col_widths=[18] * MAX_COLS,
        justification='left'
    )],

    [sg.Frame("Entry Form", create_input_fields(MAX_COLS), border_width=1, expand_x=True, pad=(0, 20))],

    [sg.Button("Add Record", button_color="#28a745", size=(15, 1)),
     sg.Button("Remove Selected", button_color="#dc3545", size=(15, 1)),
     sg.Push(),
     sg.Button("SAVE TO CSV", size=(15, 1), button_color="#007bff")],

    [sg.HSeparator(pad=(0, 15))],
    [sg.Button("RUN SCHEDULER", size=(25, 2), button_color=("white", "#343a40")),
     sg.Push(), sg.Button("Exit", size=(10, 2))]
]

window = sg.Window("Academic Scheduler v2.0", layout, finalize=True)



def refresh_ui():
    window["-CAT_DISPLAY-"].update(current_cat)
    window["-COURSE_DISPLAY-"].update(f"({current_course})" if current_cat == "Courses" else "")

    # --- Update table headings and data ---
    if current_cat == "Courses":
        current_headings = get_schema(current_cat, current_course)
        data = raw_data_storage["Courses"].get(current_course, [])
    else:
        current_headings = get_schema(current_cat)
        data = raw_data_storage[current_cat]
    num_cols = len(current_headings)
    padded_headings = current_headings + [" " * (i + 1) for i in range(MAX_COLS - num_cols)]

    padded_data = []
    for row in data:
        padded_row = list(row) + [""] * (MAX_COLS - len(row))
        padded_data.append(padded_row)

    window["-TABLE-"].update(values=padded_data)

    try:
        tv = window["-TABLE-"].Widget
        for i, heading in enumerate(padded_headings):
            col_id = f"#{i + 1}"
            tv.heading(col_id, text=heading)
            if i >= num_cols:
                tv.column(col_id, width=0, minwidth=0, stretch=False)
            else:
                tv.column(col_id, width=120, minwidth=40, stretch=True)
    except Exception:
        pass

    # --- Reset form scroll to top ---
    try:
        window["-FORM-SCROLL-"].Widget.canvas.yview_moveto(0)
    except Exception:
        pass

    # --- Show/hide field slots based on current category ---
    current_labels = current_headings
    for i in range(MAX_COLS):
        if i < len(current_labels):
            label_text = current_labels[i]
            window[f"-L{i}-"].update(value=label_text)
            window[f"-COL{i}-"].update(visible=True)
            opts = get_options(label_text.replace(' ', '_').lower(), current_cat, current_course if current_cat == "Courses" else None)
            if opts:
                window[f"-I{i}-"].update(value="", visible=False)
                window[f"-C{i}-"].update(values=opts, value=opts[0], visible=True)
            else:
                window[f"-I{i}-"].update(value="", visible=True)
                window[f"-C{i}-"].update(visible=False)
        else:
            window[f"-COL{i}-"].update(visible=False)

    # Force the scrollable canvas to recompute its scroll region
    try:
        canvas = window["-FORM-SCROLL-"].Widget.canvas
        canvas.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))
    except Exception:
        pass

# --- Initial Data Load ---
raw_data_storage["Teachers"] = load_from_raw_csv("Teachers")
raw_data_storage["Rooms"] = load_from_raw_csv("Rooms")
raw_data_storage["Courses"] = {code: load_from_raw_csv("Courses", code) for code in course_codes}

refresh_ui()

while True:
    event, values = window.read()

    if event in (sg.WIN_CLOSED, "Exit"):
        break

    if event in ["Manage Teachers", "Manage Rooms", "Manage Courses"]:
        current_cat = event.split(" ")[1]
        refresh_ui()

    if event == "-COURSE_SELECT-":
        if current_cat == "Courses":
            current_course = values["-COURSE_SELECT-"]
            refresh_ui()

    if event == "Load Saved Progress":
        raw_data_storage["Teachers"] = load_from_raw_csv("Teachers")
        raw_data_storage["Rooms"] = load_from_raw_csv("Rooms")
        raw_data_storage["Courses"] = {code: load_from_raw_csv("Courses", code) for code in course_codes}
        refresh_ui()
        sg.popup_quick_message("Data Restored.")

    if event == "Add Record":
        if current_cat == "Courses":
            schema_fields = get_schema(current_cat, current_course)
        else:
            schema_fields = get_schema(current_cat)
        row_data = []
        for i in range(len(schema_fields)):
            label = schema_fields[i]
            opts = get_options(label.replace(' ', '_').lower(), current_cat, current_course if current_cat == "Courses" else None)
            val = values[f"-C{i}-"] if opts else values[f"-I{i}-"]
            row_data.append(val)

        if any(str(v).strip() for v in row_data):
            if current_cat == "Courses":
                raw_data_storage["Courses"].setdefault(current_course, []).append(row_data)
            else:
                raw_data_storage[current_cat].append(row_data)
            refresh_ui()
            # Clear plain text inputs only
            for i in range(MAX_COLS):
                try:
                    if window[f"-I{i}-"].visible:
                        window[f"-I{i}-"].update("")
                except Exception:
                    pass
        else:
            sg.popup_error("Fields are empty!")

    if event == "Remove Selected":
        selected = values["-TABLE-"]
        if selected:
            idx = selected[0]
            if current_cat == "Courses":
                if idx < len(raw_data_storage["Courses"].get(current_course, [])):
                    raw_data_storage["Courses"][current_course].pop(idx)
            else:
                if idx < len(raw_data_storage[current_cat]):
                    raw_data_storage[current_cat].pop(idx)
            refresh_ui()

    if event == "SAVE TO CSV":
        if current_cat == "Courses":
            save_to_raw_csv(current_cat, raw_data_storage["Courses"].get(current_course, []), current_course)
            sg.popup("Saved", f"{current_course} data saved.")
        else:
            save_to_raw_csv(current_cat, raw_data_storage[current_cat])
            sg.popup("Saved", f"{current_cat} data saved.")

window.close()