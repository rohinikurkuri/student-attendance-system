import customtkinter
from tkinter import ttk, messagebox


class StudentsView(customtkinter.CTkFrame):
    def __init__(self, parent, database):
        super().__init__(parent, corner_radius=18)
        self.database = database
        self.selected_student_id = None
        self.configure(fg_color="#F8FAFC")

        header = customtkinter.CTkLabel(self, text="Student Management", font=customtkinter.CTkFont(size=26, weight="bold"), text_color="#0F172A")
        header.pack(anchor="w", padx=20, pady=(20, 10))

        self.search_var = customtkinter.StringVar()
        search_frame = customtkinter.CTkFrame(self, corner_radius=14, fg_color="#FFFFFF")
        search_frame.pack(fill="x", padx=20, pady=(0, 12))

        customtkinter.CTkLabel(search_frame, text="Search Student", anchor="w").pack(anchor="w", padx=16, pady=(14, 4))
        self.search_entry = customtkinter.CTkEntry(search_frame, placeholder_text="Name, roll number, class, or student ID")
        self.search_entry.pack(fill="x", padx=16, pady=(0, 14))
        self.search_entry.bind("<KeyRelease>", self.on_search)

        form_frame = customtkinter.CTkFrame(self, corner_radius=18, fg_color="#FFFFFF")
        form_frame.pack(fill="x", padx=20, pady=(0, 10))

        fields = [
            ("Student ID", "student_id", "CTkEntry"),
            ("Roll Number", "roll_number", "CTkEntry"),
            ("Full Name", "full_name", "CTkEntry"),
            ("Class", "class_name", "CTkEntry"),
            ("Section", "section", "CTkEntry"),
            ("Contact Number", "contact_number", "CTkEntry"),
            ("Enrollment Date", "enrollment_date", "DateEntry"),
        ]

        self.form_fields = {}
        for index, (label_text, field_name, field_type) in enumerate(fields):
            row = customtkinter.CTkFrame(form_frame, fg_color="transparent")
            row.grid(row=index // 2, column=index % 2, padx=12, pady=8, sticky="ew")
            form_frame.grid_columnconfigure(0, weight=1)
            form_frame.grid_columnconfigure(1, weight=1)

            customtkinter.CTkLabel(row, text=label_text, anchor="w").pack(anchor="w", pady=(0, 6))
            if field_type == "DateEntry":
                value = customtkinter.CTkEntry(row, width=260, height=38)
            else:
                value = customtkinter.CTkEntry(row, width=260, height=38)
            value.pack(fill="x")
            self.form_fields[field_name] = value

        self.form_fields["student_id"].configure(state="disabled")

        actions = customtkinter.CTkFrame(self, fg_color="#FFFFFF", corner_radius=18)
        actions.pack(fill="x", padx=20, pady=(0, 10))
        save_btn = customtkinter.CTkButton(actions, text="Save Student", command=self.save_student, fg_color="#2563EB", hover_color="#1D4ED8")
        save_btn.grid(row=0, column=0, padx=12, pady=12)
        clear_btn = customtkinter.CTkButton(actions, text="Clear", command=self.clear_form, fg_color="#64748B", hover_color="#475569")
        clear_btn.grid(row=0, column=1, padx=12, pady=12)
        delete_btn = customtkinter.CTkButton(actions, text="Delete Selected", command=self.delete_selected, fg_color="#DC2626", hover_color="#B91C1C")
        delete_btn.grid(row=0, column=2, padx=12, pady=12)

        table_container = customtkinter.CTkFrame(self, fg_color="#FFFFFF", corner_radius=18)
        table_container.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.table = ttk.Treeview(table_container, columns=("student_id", "roll_number", "full_name", "class_name", "section", "contact_number", "enrollment_date"), show="headings")
        self.table.heading("student_id", text="Student ID")
        self.table.heading("roll_number", text="Roll No")
        self.table.heading("full_name", text="Full Name")
        self.table.heading("class_name", text="Class")
        self.table.heading("section", text="Section")
        self.table.heading("contact_number", text="Contact")
        self.table.heading("enrollment_date", text="Enrollment Date")
        self.table.pack(fill="both", expand=True, padx=12, pady=12)
        self.table.bind("<<TreeviewSelect>>", self.on_table_select)

        self.refresh_students()

    def on_search(self, event=None):
        query = self.search_entry.get().strip()
        students = self.database.search_students(query)
        self.populate_table(students)

    def populate_table(self, students):
        for item in self.table.get_children():
            self.table.delete(item)
        for student in students:
            self.table.insert(
                "",
                "end",
                values=(
                    student["student_id"],
                    student["roll_number"],
                    student["full_name"],
                    student["class_name"],
                    student["section"],
                    student["contact_number"],
                    student["enrollment_date"],
                ),
            )

    def refresh_students(self):
        self.populate_table(self.database.search_students(""))

    def clear_form(self):
        for key in self.form_fields:
            if key == "student_id":
                self.form_fields[key].configure(state="normal")
                self.form_fields[key].delete(0, "end")
                self.form_fields[key].configure(state="disabled")
            else:
                self.form_fields[key].delete(0, "end")
        self.selected_student_id = None

    def on_table_select(self, event=None):
        selected = self.table.selection()
        if not selected:
            return
        values = self.table.item(selected[0], "values")
        self.selected_student_id = values[0]
        self.form_fields["student_id"].configure(state="normal")
        self.form_fields["student_id"].delete(0, "end")
        self.form_fields["student_id"].insert(0, values[0])
        self.form_fields["student_id"].configure(state="disabled")
        self.form_fields["roll_number"].delete(0, "end")
        self.form_fields["roll_number"].insert(0, values[1])
        self.form_fields["full_name"].delete(0, "end")
        self.form_fields["full_name"].insert(0, values[2])
        self.form_fields["class_name"].delete(0, "end")
        self.form_fields["class_name"].insert(0, values[3])
        self.form_fields["section"].delete(0, "end")
        self.form_fields["section"].insert(0, values[4])
        self.form_fields["contact_number"].delete(0, "end")
        self.form_fields["contact_number"].insert(0, values[5])
        self.form_fields["enrollment_date"].delete(0, "end")
        self.form_fields["enrollment_date"].insert(0, values[6])

    def save_student(self):
        record = {
            "student_id": self.form_fields["student_id"].get().strip() if self.form_fields["student_id"].cget("state") == "normal" else self.selected_student_id,
            "roll_number": self.form_fields["roll_number"].get().strip(),
            "full_name": self.form_fields["full_name"].get().strip(),
            "class_name": self.form_fields["class_name"].get().strip(),
            "section": self.form_fields["section"].get().strip(),
            "contact_number": self.form_fields["contact_number"].get().strip(),
            "enrollment_date": self.form_fields["enrollment_date"].get().strip(),
        }

        missing = [key for key, value in record.items() if key != "student_id" and not value]
        if missing:
            messagebox.showerror("Validation Error", "Please fill all required fields before saving.")
            return

        try:
            if self.selected_student_id:
                self.database.update_student(self.selected_student_id, record)
                messagebox.showinfo("Updated", "Student record updated successfully.")
            else:
                self.database.add_student(record)
                messagebox.showinfo("Saved", "Student record saved successfully.")
        except Exception as exc:
            messagebox.showerror("Database Error", f"Unable to save student: {exc}")
            return

        self.refresh_students()
        self.clear_form()

    def delete_selected(self):
        if not self.selected_student_id:
            messagebox.showwarning("No Selection", "Select a student to delete.")
            return

        confirm = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this student and all attendance records?")
        if not confirm:
            return

        try:
            self.database.delete_student(self.selected_student_id)
            messagebox.showinfo("Deleted", "Student deleted successfully.")
            self.clear_form()
            self.refresh_students()
        except Exception as exc:
            messagebox.showerror("Deletion Error", f"Unable to delete student: {exc}")
