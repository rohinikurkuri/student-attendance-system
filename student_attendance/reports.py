import customtkinter
from tkinter import ttk, messagebox


class AttendanceView(customtkinter.CTkFrame):
    def __init__(self, parent, database):
        super().__init__(parent, corner_radius=18)
        self.database = database
        self.configure(fg_color="#F8FAFC")

        header = customtkinter.CTkLabel(self, text="Attendance Management", font=customtkinter.CTkFont(size=26, weight="bold"), text_color="#0F172A")
        header.pack(anchor="w", padx=20, pady=(20, 10))

        filter_frame = customtkinter.CTkFrame(self, fg_color="#FFFFFF", corner_radius=18)
        filter_frame.pack(fill="x", padx=20, pady=(0, 12))

        self.class_var = customtkinter.StringVar(value="Class 10")
        self.section_var = customtkinter.StringVar(value="A")
        self.date_var = customtkinter.StringVar(value="2024-01-15")

        customtkinter.CTkLabel(filter_frame, text="Class", anchor="w").grid(row=0, column=0, padx=12, pady=10, sticky="ew")
        self.class_entry = customtkinter.CTkEntry(filter_frame, textvariable=self.class_var, width=200)
        self.class_entry.grid(row=0, column=1, padx=12, pady=10, sticky="ew")

        customtkinter.CTkLabel(filter_frame, text="Section", anchor="w").grid(row=0, column=2, padx=12, pady=10, sticky="ew")
        self.section_entry = customtkinter.CTkEntry(filter_frame, textvariable=self.section_var, width=180)
        self.section_entry.grid(row=0, column=3, padx=12, pady=10, sticky="ew")

        customtkinter.CTkLabel(filter_frame, text="Date", anchor="w").grid(row=0, column=4, padx=12, pady=10, sticky="ew")
        self.date_entry = customtkinter.CTkEntry(filter_frame, textvariable=self.date_var, width=180)
        self.date_entry.grid(row=0, column=5, padx=12, pady=10, sticky="ew")

        load_btn = customtkinter.CTkButton(filter_frame, text="Load Students", command=self.load_attendance_view, fg_color="#2563EB", hover_color="#1D4ED8")
        load_btn.grid(row=0, column=6, padx=12, pady=10)

        self.action_frame = customtkinter.CTkFrame(self, fg_color="#FFFFFF", corner_radius=18)
        self.action_frame.pack(fill="x", padx=20, pady=(0, 10))

        mark_all_btn = customtkinter.CTkButton(self.action_frame, text="Mark All Present", command=self.mark_all_present)
        mark_all_btn.grid(row=0, column=0, padx=12, pady=12)

        save_btn = customtkinter.CTkButton(self.action_frame, text="Save Attendance", command=self.save_attendance, fg_color="#16A34A", hover_color="#15803D")
        save_btn.grid(row=0, column=1, padx=12, pady=12)

        table_container = customtkinter.CTkFrame(self, fg_color="#FFFFFF", corner_radius=18)
        table_container.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        columns = ("roll_number", "full_name", "status")
        self.table = ttk.Treeview(table_container, columns=columns, show="headings")
        self.table.heading("roll_number", text="Roll Number")
        self.table.heading("full_name", text="Student Name")
        self.table.heading("status", text="Status")
        self.table.pack(fill="both", expand=True, padx=12, pady=12)

        self.load_attendance_view()

    def load_attendance_view(self):
        class_name = self.class_var.get().strip()
        section = self.section_var.get().strip()
        attendance_date = self.date_var.get().strip()

        if not class_name or not section or not attendance_date:
            messagebox.showerror("Validation Error", "Class, section, and date are required.")
            return

        rows = self.database.get_attendance_for_date(class_name, section, attendance_date)
        self.populate_table(rows)

    def populate_table(self, rows):
        for item in self.table.get_children():
            self.table.delete(item)

        for row in rows:
            status = row.get("status", "Absent")
            self.table.insert("", "end", values=(row["roll_number"], row["full_name"], status))

            combo = ttk.Combobox(self.table, values=["Present", "Absent", "Late", "Excused"], state="readonly", width=16)
            self.table.set(self.table.get_children()[-1], "status", status)

    def mark_all_present(self):
        for child_id in self.table.get_children():
            self.table.set(child_id, "status", "Present")

    def save_attendance(self):
        class_name = self.class_var.get().strip()
        section = self.section_var.get().strip()
        attendance_date = self.date_var.get().strip()

        if not class_name or not section or not attendance_date:
            messagebox.showerror("Validation Error", "Please select a class, section, and date.")
            return

        records = []
        for child_id in self.table.get_children():
            values = self.table.item(child_id, "values")
            if len(values) < 3:
                continue
            roll_number, full_name, status = values
            student = self.database.search_students(roll_number)
            if not student:
                continue
            student = student[0]
            records.append({
                "student_id": student["student_id"],
                "class_name": class_name,
                "section": section,
                "attendance_date": attendance_date,
                "status": status,
                "note": "",
            })

        if not records:
            messagebox.showwarning("No Data", "No students are available for the selected class and section.")
            return

        self.database.save_attendance_records(records)
        messagebox.showinfo("Saved", "Attendance records saved successfully.")
