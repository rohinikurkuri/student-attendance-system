import os
from datetime import datetime

import customtkinter
import pandas as pd
from tkinter import ttk, messagebox, filedialog


class ReportsView(customtkinter.CTkFrame):
    def __init__(self, parent, database):
        super().__init__(parent, corner_radius=18)
        self.database = database
        self.configure(fg_color="#F8FAFC")

        header = customtkinter.CTkLabel(self, text="Attendance Reports", font=customtkinter.CTkFont(size=26, weight="bold"), text_color="#0F172A")
        header.pack(anchor="w", padx=20, pady=(20, 10))

        filter_frame = customtkinter.CTkFrame(self, fg_color="#FFFFFF", corner_radius=18)
        filter_frame.pack(fill="x", padx=20, pady=(0, 12))

        self.report_type = customtkinter.StringVar(value="daily")
        self.start_date = customtkinter.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        self.end_date = customtkinter.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        self.class_name = customtkinter.StringVar(value="")
        self.section = customtkinter.StringVar(value="")
        self.student_id = customtkinter.StringVar(value="")

        customtkinter.CTkLabel(filter_frame, text="Report Type").grid(row=0, column=0, padx=12, pady=8, sticky="w")
        report_combo = ttk.Combobox(filter_frame, values=["daily", "weekly", "monthly", "student", "class", "date_range"], textvariable=self.report_type, state="readonly", width=18)
        report_combo.grid(row=0, column=1, padx=12, pady=8, sticky="ew")

        customtkinter.CTkLabel(filter_frame, text="Start Date").grid(row=0, column=2, padx=12, pady=8, sticky="w")
        customtkinter.CTkEntry(filter_frame, textvariable=self.start_date, width=18).grid(row=0, column=3, padx=12, pady=8, sticky="ew")

        customtkinter.CTkLabel(filter_frame, text="End Date").grid(row=1, column=0, padx=12, pady=8, sticky="w")
        customtkinter.CTkEntry(filter_frame, textvariable=self.end_date, width=18).grid(row=1, column=1, padx=12, pady=8, sticky="ew")

        customtkinter.CTkLabel(filter_frame, text="Class").grid(row=1, column=2, padx=12, pady=8, sticky="w")
        customtkinter.CTkEntry(filter_frame, textvariable=self.class_name, width=18).grid(row=1, column=3, padx=12, pady=8, sticky="ew")

        customtkinter.CTkLabel(filter_frame, text="Section").grid(row=1, column=4, padx=12, pady=8, sticky="w")
        customtkinter.CTkEntry(filter_frame, textvariable=self.section, width=18).grid(row=1, column=5, padx=12, pady=8, sticky="ew")

        customtkinter.CTkLabel(filter_frame, text="Student ID").grid(row=1, column=6, padx=12, pady=8, sticky="w")
        customtkinter.CTkEntry(filter_frame, textvariable=self.student_id, width=22).grid(row=1, column=7, padx=12, pady=8, sticky="ew")

        action_frame = customtkinter.CTkFrame(self, fg_color="#FFFFFF", corner_radius=18)
        action_frame.pack(fill="x", padx=20, pady=(0, 12))

        generate_btn = customtkinter.CTkButton(action_frame, text="Generate Report", command=self.generate_report, fg_color="#2563EB", hover_color="#1D4ED8")
        generate_btn.grid(row=0, column=0, padx=12, pady=12)
        csv_btn = customtkinter.CTkButton(action_frame, text="Export CSV", command=self.export_csv)
        csv_btn.grid(row=0, column=1, padx=12, pady=12)
        excel_btn = customtkinter.CTkButton(action_frame, text="Export Excel", command=self.export_excel)
        excel_btn.grid(row=0, column=2, padx=12, pady=12)
        print_btn = customtkinter.CTkButton(action_frame, text="Print Report", command=self.print_report, fg_color="#7C3AED", hover_color="#6D28D9")
        print_btn.grid(row=0, column=3, padx=12, pady=12)

        table_frame = customtkinter.CTkFrame(self, fg_color="#FFFFFF", corner_radius=18)
        table_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.table = ttk.Treeview(table_frame, columns=("student", "class", "section", "date", "status", "attendance_percent"), show="headings")
        self.table.heading("student", text="Student")
        self.table.heading("class", text="Class")
        self.table.heading("section", text="Section")
        self.table.heading("date", text="Date")
        self.table.heading("status", text="Status")
        self.table.heading("attendance_percent", text="Attendance %")
        self.table.pack(fill="both", expand=True, padx=12, pady=12)

        self.report_rows = []
        self.generate_report()

    def generate_report(self):
        start = self.start_date.get().strip() or None
        end = self.end_date.get().strip() or None
        class_name = self.class_name.get().strip() or None
        section = self.section.get().strip() or None
        student_id = self.student_id.get().strip() or None

        rows = self.database.get_attendance_records(
            report_type=self.report_type.get(),
            start_date=start,
            end_date=end,
            class_name=class_name,
            section=section,
            student_id=student_id,
        )

        self.report_rows = []
        for row in rows:
            student_name = self.database.get_student_name_by_id(row["student_id"])
            counted = 1
            pct = 100 if row["status"] in ("Present", "Late") else 0
            self.report_rows.append({
                "student": student_name,
                "class": row["class_name"],
                "section": row["section"],
                "date": row["attendance_date"],
                "status": row["status"],
                "attendance_percent": pct,
            })

        self.populate_table(self.report_rows)

    def populate_table(self, rows):
        for item in self.table.get_children():
            self.table.delete(item)
        for row in rows:
            self.table.insert("", "end", values=(row["student"], row["class"], row["section"], row["date"], row["status"], f"{row['attendance_percent']}%"))

    def export_csv(self):
        if not self.report_rows:
            messagebox.showwarning("No Data", "There is no report data to export.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if not path:
            return
        pd.DataFrame(self.report_rows).to_csv(path, index=False)
        messagebox.showinfo("Export Successful", f"Report exported to:\n{path}")

    def export_excel(self):
        if not self.report_rows:
            messagebox.showwarning("No Data", "There is no report data to export.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
        if not path:
            return
        pd.DataFrame(self.report_rows).to_excel(path, index=False)
        messagebox.showinfo("Export Successful", f"Report exported to:\n{path}")

    def print_report(self):
        if not self.report_rows:
            messagebox.showwarning("No Data", "There is no report data to print.")
            return
        export_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "exports")
        os.makedirs(export_dir, exist_ok=True)
        output_file = os.path.join(export_dir, f"attendance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        with open(output_file, "w", encoding="utf-8") as file:
            file.write("Attendance Report\n")
            file.write("=" * 40 + "\n")
            for row in self.report_rows:
                file.write(f"{row['student']} | {row['class']} | {row['section']} | {row['date']} | {row['status']} | {row['attendance_percent']}%\n")
        messagebox.showinfo("Print Ready", f"Report generated as text file:\n{output_file}\n\nUse your system print dialog to print it.")
