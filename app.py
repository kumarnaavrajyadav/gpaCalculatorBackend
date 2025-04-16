from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

app = Flask(__name__)
CORS(app)  # enable CORS if calling API from a different domain

# Mapping marks to grade point
def marks_to_grade_point(total_marks):
    """
    Convert total marks (0-100) to a grade point.
    
    Scale (example):
    - 90 to 100: 10 (A+)
    - 80 to 89:  9  (A)
    - 70 to 79:  8  (B+)
    - 60 to 69:  7  (B)
    - 50 to 59:  6  (C)
    - 40 to 49:  5  (D)
    - below 40:  0  (F)
    """
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

# Route to generate PDF report from provided data
@app.route('/generate_pdf', methods=['POST'])
def generate_pdf():
    try:
        data = request.json
        student_name = data.get('student_name', 'Student')
        subjects = data.get('subjects', [])
        
        if not subjects:
            return jsonify({"error": "No subject data provided!"}), 400

        # Prepare data calculations
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
        
        # Create PDF in memory using ReportLab
        buffer = io.BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        
        # Title and Student Name
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
        
        # Draw subject rows
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
            # Add new page if needed
            if y < 50:
                pdf.showPage()
                y = height - 50

        # Overall GPA Section
        y -= 20
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(50, y, f"Overall GPA: {overall_gpa:.2f}")

        pdf.save()
        buffer.seek(0)

        # Return the PDF as a downloadable file
        return send_file(buffer, as_attachment=True, download_name='grade_report.pdf', mimetype='application/pdf')

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
