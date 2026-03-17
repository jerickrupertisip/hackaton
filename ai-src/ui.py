import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv
import os
from csp import generate_schedules

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
raw_data_storage = {"Teachers": [], "Rooms": [], "Courses": {}, "Enrollment": {}}

# --- Static schemas for Teachers and Rooms (from CSVs) ---
TEACHERS_CSV = os.path.join(DATA_DIR, 'teachers.csv')
ROOMS_CSV = os.path.join(DATA_DIR, 'rooms.csv')
ENROLLMENT_DIR = os.path.join(DATA_DIR, 'enrollment')
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'output')

def get_teachers_schema():
    with open(TEACHERS_CSV, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        return [h.replace('_', ' ').title() for h in next(reader)]

def get_rooms_schema():
    with open(ROOMS_CSV, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        return [h.replace('_', ' ').title() for h in next(reader)]

def get_enrollment_schema():
    # Fixed schema for enrollment CSVs
    return ["Year", "Semester", "Total Students"]

# --- Dynamic schema dictionary ---
def get_schema(category, course_code=None):
    if category == "Teachers":
        return get_teachers_schema()
    elif category == "Rooms":
        return get_rooms_schema()
    elif category == "Courses" and course_code:
        return get_course_schema(course_code)
    elif category == "Enrollment" and course_code:
        return get_enrollment_schema()
    return []

# --- Dynamic options dictionary (for dropdowns) ---
def get_options(field, category, course_code=None):
    if category == "Courses" and course_code:
        # Use field options from all courses for consistency
        return get_field_options(field)
    elif category == "Enrollment" and course_code:
        if field == "year":
            return ["1", "2", "3", "4"]
        elif field == "semester":
            return ["1", "2"]
        else:
            return []
    elif category == "Rooms" and field == "category":
        # Room category dropdown
        return ["Regular", "Science Lab", "Computer Lab", "Online"]
    return []

def load_output_csv(course_code):
    course_dir = os.path.join(OUTPUT_DIR, course_code.upper())
    if not os.path.exists(course_dir):
        return []
    files = [f for f in os.listdir(course_dir) if f.endswith('.csv')]
    if not files:
        return []
    # Get headers from first file
    path = os.path.join(course_dir, files[0])
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        headers = next(reader)
    sections_data = []
    for file in files:
        section_num = file.replace('.csv', '')
        section = f"{course_code}-{section_num}"
        path = os.path.join(course_dir, file)
        data = []
        with open(path, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)  # skip header
            for row in reader:
                if any(cell.strip() for cell in row):
                    data.append(row)
        sections_data.append((section, headers, data))
    return sections_data

# --- CSV Functions (Dynamic) ---
def save_to_raw_csv(category, data_list, course_code=None):
    if category == "Courses" and course_code:
        path = os.path.join(COURSES_DIR, f"{course_code.lower()}.csv")
        schema_headers = get_course_schema(course_code)
    elif category == "Enrollment" and course_code:
        path = os.path.join(ENROLLMENT_DIR, f"{course_code.lower()}.csv")
        schema_headers = get_enrollment_schema()
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
    elif category == "Enrollment" and course_code:
        path = os.path.join(ENROLLMENT_DIR, f"{course_code.lower()}.csv")
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







def select_subjects():
    all_subjects = sorted(get_field_options("subject"))
    current_expertise = fields[1][2].get().strip()
    if current_expertise:
        pre_selected = [s.strip() for s in current_expertise.split(",")]
    else:
        pre_selected = []

    subject_window = tk.Toplevel(root)
    subject_window.title("Select Subjects")
    subject_window.grab_set()
    subject_window.focus()
    listbox = tk.Listbox(subject_window, selectmode=tk.MULTIPLE, height=10, width=50)
    for subject in all_subjects:
        listbox.insert(tk.END, subject)
        if subject in pre_selected:
            listbox.selection_set(listbox.size() - 1)
    listbox.pack(pady=10)

    def ok():
        selected = [listbox.get(i) for i in listbox.curselection()]
        if selected:
            expertise_str = ", ".join(selected)
            fields[1][2].config(state="normal")
            fields[1][2].delete(0, tk.END)
            fields[1][2].insert(0, expertise_str)
            fields[1][2].config(state="readonly")
        subject_window.destroy()

    def cancel():
        subject_window.destroy()

    btn_frame = tk.Frame(subject_window)
    btn_frame.pack()
    tk.Button(btn_frame, text="OK", command=ok).pack(side=tk.LEFT, padx=5)
    tk.Button(btn_frame, text="Cancel", command=cancel).pack(side=tk.LEFT, padx=5)


# --- Main Layout ---
course_codes = get_course_codes()
default_course = course_codes[0] if course_codes else "BSIT"
categories = ["Teachers", "Rooms", "Courses", "Enrollment"]
current_cat = "Teachers"
current_course = default_course

def get_max_cols():
    # Find the max number of columns among all schemas
    max_cols = len(get_teachers_schema())
    max_cols = max(max_cols, len(get_rooms_schema()))
    for code in course_codes:
        max_cols = max(max_cols, len(get_course_schema(code)))
        max_cols = max(max_cols, len(get_enrollment_schema()))
    max_cols = max(max_cols, 9)  # For output with Section column
    return max_cols

MAX_COLS = get_max_cols()
placeholder_headings = [" " * (i + 1) for i in range(MAX_COLS)]

root = tk.Tk()
root.title("Academic Scheduler v2.0")
# root.geometry("800x600")  # Remove fixed size to let it auto-size

# Tab control
tab_control = ttk.Notebook(root)
tab1 = ttk.Frame(tab_control)
tab2 = ttk.Frame(tab_control)
tab_control.add(tab1, text="Inputs")
tab_control.add(tab2, text="Outputs")
tab_control.pack(expand=1, fill="both")

# Tab 1: Inputs
title_label = tk.Label(tab1, text="Academic Scheduling System", font=("Arial", 16, "bold"))
title_label.pack(pady=10)

button_frame = tk.Frame(tab1)
button_frame.pack(pady=5)
manage_teachers_btn = tk.Button(button_frame, text="Manage Teachers")
manage_rooms_btn = tk.Button(button_frame, text="Manage Rooms")
manage_courses_btn = tk.Button(button_frame, text="Manage Courses")
manage_enrollment_btn = tk.Button(button_frame, text="Manage Enrollment")
course_select = ttk.Combobox(button_frame, values=course_codes, state="readonly")
course_select.set(default_course)

manage_teachers_btn.pack(side=tk.LEFT, padx=5)
manage_rooms_btn.pack(side=tk.LEFT, padx=5)
manage_courses_btn.pack(side=tk.LEFT, padx=5)
manage_enrollment_btn.pack(side=tk.LEFT, padx=5)
course_select.pack(side=tk.LEFT, padx=5)

sep1 = ttk.Separator(tab1, orient='horizontal')
sep1.pack(fill='x', pady=15)

current_display = tk.Label(tab1, text="Currently Editing: Teachers", font=("Arial", 10, "italic"))
current_display.pack(pady=5, anchor='center')

# Table
table_frame = tk.Frame(tab1)
table_frame.pack(pady=10, fill=tk.BOTH, expand=True)
table = ttk.Treeview(table_frame, columns=placeholder_headings, show="headings", height=10)
table.pack(fill=tk.BOTH, expand=True)

# Form Frame
form_frame = tk.LabelFrame(tab1, text="Entry Form", padx=10, pady=10)
form_frame.pack(fill=tk.BOTH, expand=True, pady=20)

form_scroll = tk.Canvas(form_frame)  # Remove fixed height to allow expansion
form_scroll.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
scrollbar = ttk.Scrollbar(form_frame, orient="vertical", command=form_scroll.yview)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
form_scroll.configure(yscrollcommand=scrollbar.set)

form_inner = tk.Frame(form_scroll)
form_scroll.create_window((0,0), window=form_inner, anchor="nw")

fields = []
for i in range(MAX_COLS):
    frame = tk.Frame(form_inner)
    label = tk.Label(frame, text="", font=("Arial", 10, "bold"))
    label.pack(side=tk.LEFT, padx=(0,10))
    entry = tk.Entry(frame, width=44)
    combo = ttk.Combobox(frame, width=43, state="readonly")
    chk_var = tk.BooleanVar()
    chk = tk.Checkbutton(frame, text="Available", variable=chk_var)
    # Only show Select Subjects button for Teachers Expertise field
    if i == 1:
        button = tk.Button(frame, text="Select Subjects", command=select_subjects)
    else:
        button = tk.Label(frame, text="")  # Placeholder, invisible
    entry.pack_forget()
    combo.pack_forget()
    chk.pack_forget()
    button.pack_forget()
    frame.pack(pady=(8,2), anchor='w')
    fields.append((frame, label, entry, combo, chk, chk_var, button))

# Buttons
button_frame2 = tk.Frame(tab1)
button_frame2.pack(pady=10)
add_btn = tk.Button(button_frame2, text="Add Record", bg="#28a745", width=15)
edit_btn = tk.Button(button_frame2, text="Edit Selected", bg="#ffc107", width=15)
remove_btn = tk.Button(button_frame2, text="Remove Selected", bg="#dc3545", width=15)
cancel_btn = tk.Button(button_frame2, text="Cancel", bg="#6c757d", width=10)
confirm_btn = tk.Button(button_frame2, text="Confirm", bg="#007bff", width=10)
save_csv_btn = tk.Button(button_frame2, text="SAVE TO CSV", bg="#007bff", width=15)
load_progress_btn = tk.Button(button_frame2, text="Load Saved Progress", bg="grey")

add_btn.pack(side=tk.LEFT, padx=5)
edit_btn.pack(side=tk.LEFT, padx=5)
remove_btn.pack(side=tk.LEFT, padx=5)
cancel_btn.pack(side=tk.LEFT, padx=5)
confirm_btn.pack(side=tk.LEFT, padx=5)
save_csv_btn.pack(side=tk.LEFT, padx=5)
load_progress_btn.pack(side=tk.LEFT, padx=5)

sep2 = ttk.Separator(tab1, orient='horizontal')
sep2.pack(fill='x', pady=15)

run_scheduler_btn = tk.Button(tab1, text="RUN SCHEDULER", bg="#343a40", fg="white", width=25, height=2)
exit_btn = tk.Button(tab1, text="Exit", width=10, height=2)
run_scheduler_btn.pack(side=tk.LEFT, padx=10)
exit_btn.pack(side=tk.RIGHT, padx=10)

# Tab 2: Outputs
output_title = tk.Label(tab2, text="Output Visualization", font=("Arial", 16, "bold"))
output_title.pack(pady=10)

output_course_select = ttk.Combobox(tab2, values=course_codes, state="readonly")
output_course_select.set(default_course)
output_course_select.pack(pady=5)

output_notebook = ttk.Notebook(tab2)
output_notebook.pack(fill=tk.BOTH, expand=True)

# --- Edit Mode State ---
edit_mode = False
selected_index = None

def refresh_ui():
    current_display.config(text=f"Currently Editing: {current_cat} ({current_course})" if current_cat in ["Courses", "Enrollment"] else f"Currently Editing: {current_cat}")
    course_select.config(state="disabled" if edit_mode else "readonly")
    course_select.pack_forget() if not (current_cat in ["Courses", "Enrollment"]) else course_select.pack(side=tk.LEFT, padx=5)

    # --- Update table headings and data ---
    if current_cat in ["Courses", "Enrollment"]:
        current_headings = get_schema(current_cat, current_course)
        data = raw_data_storage[current_cat].get(current_course, [])
    else:
        current_headings = get_schema(current_cat)
        data = raw_data_storage[current_cat]
    num_cols = len(current_headings)

    # Clear table
    for item in table.get_children():
        table.delete(item)
    # Set columns dynamically
    table['columns'] = current_headings
    # Set headings
    for i, heading in enumerate(current_headings):
        table.heading(i, text=heading)
        table.column(i, width=120, minwidth=40)

    # Insert data
    for row in data:
        padded_row = list(row) + [""] * (MAX_COLS - len(row))
        table.insert("", tk.END, values=padded_row)

    # --- Reset form scroll ---
    form_scroll.yview_moveto(0)

    # --- Show/hide field slots ---
    for i in range(MAX_COLS):
        if i < len(current_headings):
            label_text = current_headings[i]
            fields[i][1].config(text=label_text)
            opts = get_options(label_text.replace(' ', '_').lower(), current_cat, current_course if current_cat in ["Courses", "Enrollment"] else None)
            if opts:
                fields[i][2].pack_forget()
                fields[i][3].config(values=opts)
                fields[i][3].set(opts[0])
                fields[i][3].pack(side=tk.LEFT)
                fields[i][4].pack_forget()
                fields[i][6].pack_forget()
            elif current_cat == "Teachers" and i == 2:  # Availability checkbox
                fields[i][2].pack_forget()
                fields[i][3].pack_forget()
                fields[i][4].pack(side=tk.LEFT)
                fields[i][6].pack_forget()
            else:
                readonly = (current_cat == "Teachers" and i == 1)  # Expertise field
                fields[i][2].config(state="readonly" if readonly else "normal")
                fields[i][2].pack(side=tk.LEFT)
                fields[i][3].pack_forget()
                fields[i][4].pack_forget()
                # Show Select Subjects button only for Teachers Expertise field
                if current_cat == "Teachers" and i == 1:
                    fields[i][6].pack(side=tk.LEFT, padx=5)
                else:
                    fields[i][6].pack_forget()
        else:
            fields[i][0].pack_forget()

    # --- Update button visibility ---
    add_btn.pack_forget() if edit_mode else add_btn.pack(side=tk.LEFT, padx=5)
    edit_btn.pack_forget() if edit_mode else edit_btn.pack(side=tk.LEFT, padx=5)
    remove_btn.pack_forget() if edit_mode else remove_btn.pack(side=tk.LEFT, padx=5)
    cancel_btn.pack_forget() if not edit_mode else cancel_btn.pack(side=tk.LEFT, padx=5)
    confirm_btn.pack_forget() if not edit_mode else confirm_btn.pack(side=tk.LEFT, padx=5)
    save_csv_btn.pack_forget() if edit_mode else save_csv_btn.pack(side=tk.LEFT, padx=5)

    # --- Populate form if in edit mode ---
    if edit_mode and selected_index is not None and selected_index < len(data):
        row = data[selected_index]
        for i in range(len(current_headings)):
            label_text = current_headings[i]
            opts = get_options(label_text.replace(' ', '_').lower(), current_cat, current_course if current_cat in ["Courses", "Enrollment"] else None)
            if opts:
                fields[i][3].set(row[i])
            elif current_cat == "Teachers" and i == 2:
                fields[i][5].set(row[i] == '1')
            else:
                if current_cat == "Teachers" and i == 1:
                    fields[i][2].config(state="normal")
                    fields[i][2].delete(0, tk.END)
                    fields[i][2].insert(0, row[i])
                    fields[i][2].config(state="readonly")
                else:
                    fields[i][2].delete(0, tk.END)
                    fields[i][2].insert(0, row[i])

    # Update scroll region
    form_inner.update_idletasks()
    form_scroll.config(scrollregion=form_scroll.bbox("all"))

# --- Initial Data Load ---

raw_data_storage["Teachers"] = load_from_raw_csv("Teachers")
raw_data_storage["Rooms"] = load_from_raw_csv("Rooms")
raw_data_storage["Courses"] = {code: load_from_raw_csv("Courses", code) for code in course_codes}
raw_data_storage["Enrollment"] = {code: load_from_raw_csv("Enrollment", code) for code in course_codes}

refresh_ui()

# --- Event Handlers ---
def manage_teachers():
    global current_cat, edit_mode, selected_index
    current_cat = "Teachers"
    edit_mode = False
    selected_index = None
    refresh_ui()

def manage_rooms():
    global current_cat, edit_mode, selected_index
    current_cat = "Rooms"
    edit_mode = False
    selected_index = None
    refresh_ui()

def manage_courses():
    global current_cat, edit_mode, selected_index
    current_cat = "Courses"
    edit_mode = False
    selected_index = None
    refresh_ui()

def manage_enrollment():
    global current_cat, edit_mode, selected_index
    current_cat = "Enrollment"
    edit_mode = False
    selected_index = None
    refresh_ui()

def course_select_changed(event):
    global current_course
    if current_cat in ["Courses", "Enrollment"] and not edit_mode:
        current_course = course_select.get()
        refresh_ui()

def load_saved_progress():
    global raw_data_storage
    raw_data_storage["Teachers"] = load_from_raw_csv("Teachers")
    raw_data_storage["Rooms"] = load_from_raw_csv("Rooms")
    raw_data_storage["Courses"] = {code: load_from_raw_csv("Courses", code) for code in course_codes}
    raw_data_storage["Enrollment"] = {code: load_from_raw_csv("Enrollment", code) for code in course_codes}
    refresh_ui()
    messagebox.showinfo("Data Restored", "Data Restored.")

def add_record():
    if current_cat in ["Courses", "Enrollment"]:
        schema_fields = get_schema(current_cat, current_course)
    else:
        schema_fields = get_schema(current_cat)
    row_data = []
    for i in range(len(schema_fields)):
        label = schema_fields[i]
        opts = get_options(label.replace(' ', '_').lower(), current_cat, current_course if current_cat in ["Courses", "Enrollment"] else None)
        if opts:
            val = fields[i][3].get()
        elif current_cat == "Teachers" and i == 2:
            val = '1' if fields[i][5].get() else '0'
        else:
            val = fields[i][2].get()
        row_data.append(val)

    if any(str(v).strip() for v in row_data):
        if current_cat in ["Courses", "Enrollment"]:
            raw_data_storage[current_cat].setdefault(current_course, []).append(row_data)
        else:
            raw_data_storage[current_cat].append(row_data)
        refresh_ui()
        # Clear plain text inputs
        for i in range(MAX_COLS):
            if fields[i][2].winfo_ismapped():
                fields[i][2].delete(0, tk.END)
    else:
        messagebox.showerror("Error", "Fields are empty!")

def edit_selected():
    selected = table.selection()
    if not selected:
        messagebox.showerror("Error", "No row selected!")
    else:
        global edit_mode, selected_index
        edit_mode = True
        selected_index = table.index(selected[0])
        refresh_ui()

def remove_selected():
    selected = table.selection()
    if selected:
        indices = sorted([table.index(item) for item in selected], reverse=True)
        if current_cat in ["Courses", "Enrollment"]:
            data_list = raw_data_storage[current_cat][current_course]
            for idx in indices:
                if idx < len(data_list):
                    data_list.pop(idx)
        else:
            data_list = raw_data_storage[current_cat]
            for idx in indices:
                if idx < len(data_list):
                    data_list.pop(idx)
        refresh_ui()

def cancel_edit():
    global edit_mode, selected_index
    edit_mode = False
    selected_index = None
    refresh_ui()

def confirm_edit():
    global edit_mode, selected_index
    if current_cat in ["Courses", "Enrollment"]:
        schema_fields = get_schema(current_cat, current_course)
    else:
        schema_fields = get_schema(current_cat)
    row_data = []
    for i in range(len(schema_fields)):
        label = schema_fields[i]
        opts = get_options(label.replace(' ', '_').lower(), current_cat, current_course if current_cat in ["Courses", "Enrollment"] else None)
        if opts:
            val = fields[i][3].get()
        elif current_cat == "Teachers" and i == 2:
            val = '1' if fields[i][5].get() else '0'
        else:
            val = fields[i][2].get()
        row_data.append(val)

    if any(str(v).strip() for v in row_data):
        if current_cat in ["Courses", "Enrollment"]:
            raw_data_storage[current_cat][current_course][selected_index] = row_data
        else:
            raw_data_storage[current_cat][selected_index] = row_data
        # Save to CSV
        if current_cat in ["Courses", "Enrollment"]:
            save_to_raw_csv(current_cat, raw_data_storage[current_cat].get(current_course, []), current_course)
            messagebox.showinfo("Saved", f"{current_course} {current_cat.lower()} data saved.")
        else:
            save_to_raw_csv(current_cat, raw_data_storage[current_cat])
            messagebox.showinfo("Saved", f"{current_cat} data saved.")
        edit_mode = False
        selected_index = None
        refresh_ui()
    else:
        messagebox.showerror("Error", "Fields are empty!")

def save_to_csv():
    save_to_raw_csv("Teachers", raw_data_storage["Teachers"])
    save_to_raw_csv("Rooms", raw_data_storage["Rooms"])
    for course_code in course_codes:
        if course_code in raw_data_storage["Courses"]:
            save_to_raw_csv("Courses", raw_data_storage["Courses"][course_code], course_code)
        if course_code in raw_data_storage["Enrollment"]:
            save_to_raw_csv("Enrollment", raw_data_storage["Enrollment"][course_code], course_code)
    messagebox.showinfo("Saved", "All changes saved to CSVs.")

def output_course_changed(event):
    selected_course = output_course_select.get()
    sections_data = load_output_csv(selected_course)
    # Clear previous tabs
    for tab_id in output_notebook.tabs():
        output_notebook.forget(tab_id)
    for section, headers, data in sections_data:
        frame = ttk.Frame(output_notebook)
        table = ttk.Treeview(frame, columns=headers, show="headings", height=15)
        for i, h in enumerate(headers):
            table.heading(i, text=h)
            table.column(i, width=120, minwidth=40)
        for row in data:
            table.insert("", tk.END, values=row)
        table.pack(fill=tk.BOTH, expand=True)
        output_notebook.add(frame, text=section)

def run_scheduler():
    messagebox.showinfo("Success", "Scheduling complete! Results are now displayed in the Outputs tab.")
    generate_schedules()
    output_course_changed(None)  # Refresh output data
    tab_control.select(1)  # Switch to Output tab

output_course_changed(None)  # Load initial output data

def exit_app():
    root.quit()

def on_tab_changed(event):
    if tab_control.index(tab_control.select()) == 1:  # Output tab
        output_course_changed(None)

# Bind events
tab_control.bind("<<NotebookTabChanged>>", on_tab_changed)
manage_teachers_btn.config(command=manage_teachers)
manage_rooms_btn.config(command=manage_rooms)
manage_courses_btn.config(command=manage_courses)
manage_enrollment_btn.config(command=manage_enrollment)
course_select.bind("<<ComboboxSelected>>", course_select_changed)
load_progress_btn.config(command=load_saved_progress)
add_btn.config(command=add_record)
edit_btn.config(command=edit_selected)
remove_btn.config(command=remove_selected)
cancel_btn.config(command=cancel_edit)
confirm_btn.config(command=confirm_edit)
save_csv_btn.config(command=save_to_csv)
run_scheduler_btn.config(command=run_scheduler)
output_course_select.bind("<<ComboboxSelected>>", output_course_changed)
exit_btn.config(command=exit_app)

root.mainloop()