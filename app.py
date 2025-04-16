from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import xlsxwriter

app = Flask(__name__)
CORS(app)  # Enable CORS to accept requests from your React app

# --- Existing Grade Report Endpoint ---
def marks_to_grade_point(total_marks):
    if total_marks >= 90:
        return 10
    elif total_marks >= 80:
        return 9
    elif total_marks >= 70:
        return 8
    elif total_marks >= 60:
        return 7
    elif total_marks >= 50:
        return 6
    elif total_marks >= 40:
        return 5
    else:
        return 0

@app.route('/generate_pdf', methods=['POST'])
def generate_pdf():
    try:
        data = request.json
        student_name = data.get('student_name', 'Student')
        subjects = data.get('subjects', [])

        if not subjects:
            return jsonify({"error": "No subject data provided!"}), 400

        report_data = []
        total_points = 0

        for subject in subjects:
            subject_name = subject.get('subject_name', 'Unnamed Subject')
            fa1 = float(subject.get('FA1', 0))
            fa2 = float(subject.get('FA2', 0))
            sa  = float(subject.get('SA', 0))
            total = fa1 + fa2 + sa  # out of 100
            grade_point = marks_to_grade_point(total)
            total_points += grade_point

            report_data.append({
                'subject_name': subject_name,
                'FA1': fa1,
                'FA2': fa2,
                'SA': sa,
                'total': total,
                'grade_point': grade_point
            })

        overall_gpa = total_points / len(subjects)

        buffer = io.BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawString(50, height - 50, "Grade Calculator Report")
        pdf.setFont("Helvetica", 12)
        pdf.drawString(50, height - 70, f"Student Name: {student_name}")

        # Table headers
        pdf.setFont("Helvetica-Bold", 12)
        headers = ["Subject", "FA1 (20)", "FA2 (20)", "SA (60)", "Total (100)", "Grade Pt."]
        x_positions = [50, 150, 230, 310, 390, 480]
        y_start = height - 100
        for idx, header in enumerate(headers):
            pdf.drawString(x_positions[idx], y_start, header)

        pdf.setFont("Helvetica", 11)
        y = y_start - 20
        for sub in report_data:
            pdf.drawString(x_positions[0], y, sub['subject_name'])
            pdf.drawString(x_positions[1], y, f"{sub['FA1']}")
            pdf.drawString(x_positions[2], y, f"{sub['FA2']}")
            pdf.drawString(x_positions[3], y, f"{sub['SA']}")
            pdf.drawString(x_positions[4], y, f"{sub['total']}")
            pdf.drawString(x_positions[5], y, f"{sub['grade_point']}")
            y -= 20
            if y < 50:
                pdf.showPage()
                y = height - 50

        y -= 20
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(50, y, f"Overall GPA: {overall_gpa:.2f}")

        pdf.save()
        buffer.seek(0)

        return send_file(buffer, as_attachment=True, download_name='grade_report.pdf', mimetype='application/pdf')

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- New Attendance Report Endpoints ---

@app.route('/generate_attendance_pdf', methods=['POST'])
def generate_attendance_pdf():
    try:
        data = request.json
        class_name = data.get('className', 'Class')
        attendance_date = data.get('attendanceDate', '')
        students = data.get('students', [])

        buffer = io.BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawString(50, height - 50, f"Attendance Report - {class_name}")
        pdf.setFont("Helvetica", 12)
        pdf.drawString(50, height - 70, f"Date & Time: {attendance_date}")

        # Table headers
        pdf.setFont("Helvetica-Bold", 12)
        headers = ["Student Name", "PRN", "Division", "Status"]
        x_positions = [50, 200, 300, 400]
        y_start = height - 100
        for idx, header in enumerate(headers):
            pdf.drawString(x_positions[idx], y_start, header)

        pdf.setFont("Helvetica", 11)
        y = y_start - 20
        for student in students:
            pdf.drawString(x_positions[0], y, student.get('name', ''))
            pdf.drawString(x_positions[1], y, student.get('prn', ''))
            pdf.drawString(x_positions[2], y, student.get('division', ''))
            pdf.drawString(x_positions[3], y, student.get('status', ''))
            y -= 20
            if y < 50:
                pdf.showPage()
                y = height - 50

        pdf.save()
        buffer.seek(0)
        return send_file(buffer, as_attachment=True, download_name='attendance_report.pdf', mimetype='application/pdf')
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/generate_attendance_excel', methods=['POST'])
def generate_attendance_excel():
    try:
        data = request.json
        class_name = data.get('className', 'Class')
        attendance_date = data.get('attendanceDate', '')
        students = data.get('students', [])

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {"in_memory": True})
        worksheet = workbook.add_worksheet("Attendance Report")

        # Write Title and Date/Time
        worksheet.write(0, 0, f"Attendance Report - {class_name}")
        worksheet.write(1, 0, f"Date & Time: {attendance_date}")

        # Write table headers starting at row 3
        headers = ["Student Name", "PRN", "Division", "Status"]
        for col, header in enumerate(headers):
            worksheet.write(3, col, header)

        row = 4
        for student in students:
            worksheet.write(row, 0, student.get("name", ""))
            worksheet.write(row, 1, student.get("prn", ""))
            worksheet.write(row, 2, student.get("division", ""))
            worksheet.write(row, 3, student.get("status", ""))
            row += 1

        workbook.close()
        output.seek(0)
        return send_file(
            output,
            as_attachment=True,
            download_name="attendance_report.xlsx",
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
