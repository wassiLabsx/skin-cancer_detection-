from flask import Flask, render_template, request, redirect, session, flash, url_for, send_file
import os
import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
import mysql.connector
from config import Config
from datetime import datetime
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch

app = Flask(__name__)
app.config.from_object(Config)

# Ensure upload folder exists
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# Load model
model = load_model(app.config["MODEL_PATH"]) # Model not loaded yet — will be added after training

#  DB helper 
def get_db():
    return mysql.connector.connect(
        host=app.config["DB_HOST"],
        user=app.config["DB_USER"],
        password=app.config["DB_PASSWORD"],
        database=app.config["DB_NAME"]
    )

def allowed_file(filename):
    return "." in filename and \
           filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]


# LOGIN 
@app.route("/", methods=["GET", "POST"])
def login():
    if "user" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        try:
            db = get_db()
            cursor = db.cursor(dictionary=True)
            cursor.execute(
                "SELECT * FROM users WHERE username = %s AND password = %s",
                (username, password)
            )
            user = cursor.fetchone()
            cursor.close()
            db.close()

            if user:
                session["user"] = username
                session["user_id"] = user["id"]
                flash("Welcome back, " + username + "!", "success")
                return redirect(url_for("dashboard"))
            else:
                flash("Invalid username or password.", "error")

        except Exception as e:
            flash("Database connection error: " + str(e), "error")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


# DASHBOARD 
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute("SELECT COUNT(*) as total FROM patients")
        total = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) as count FROM patients WHERE risk_level = 'Malignant'")
        malignant = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) as count FROM patients WHERE risk_level = 'Benign'")
        benign = cursor.fetchone()["count"]

        cursor.execute("SELECT * FROM patients ORDER BY created_at DESC LIMIT 5")
        recent = cursor.fetchall()

        cursor.close()
        db.close()

        return render_template("dashboard.html",
                               total=total,
                               malignant=malignant,
                               benign=benign,
                               recent=recent)

    except Exception as e:
        flash("Error loading dashboard: " + str(e), "error")
        return render_template("dashboard.html", total=0, malignant=0, benign=0, recent=[])


# PREDICT
@app.route("/predict", methods=["GET", "POST"])
def predict():
    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        age  = request.form.get("age",  "").strip()
        file = request.files.get("image")

        if not name or not age:
            flash("Please fill in all fields.", "warning")
            return redirect(url_for("predict"))

        if not file or file.filename == "":
            flash("Please select an image.", "warning")
            return redirect(url_for("predict"))

        if not allowed_file(file.filename):
            flash("Only PNG, JPG, and JPEG files are allowed.", "warning")
            return redirect(url_for("predict"))

        try:
            # Save image with timestamp prefix to avoid collisions
            filename = datetime.now().strftime("%Y%m%d_%H%M%S_") + file.filename
            path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(path)

            # Preprocess
            img = image.load_img(path, target_size=app.config["IMG_SIZE"])
            img_array = image.img_to_array(img) / 255.0
            img_array = np.expand_dims(img_array, axis=0)

            # Predict
            prediction = model.predict(img_array)[0][0]
            confidence = float(prediction) * 100 if prediction > 0.5 else float(1 - prediction) * 100

            if prediction > 0.5:
                diagnosis  = "Malignant"
                risk_level = "Malignant"
                short_code = "MAL"
            else:
                diagnosis  = "Benign"
                risk_level = "Benign"
                short_code = "BEN"

            # Save to DB
            db = get_db()
            cursor = db.cursor()
            cursor.execute("""
                INSERT INTO patients
                    (name, age, diagnosis, short_code, risk_level, confidence, image_path, created_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (name, int(age), diagnosis, short_code, risk_level,
                  round(confidence, 2), path, session["user"]))
            patient_id = cursor.lastrowid
            db.commit()
            cursor.close()
            db.close()

            return redirect(url_for("result", patient_id=patient_id))

        except Exception as e:
            flash("Prediction error: " + str(e), "error")
            return redirect(url_for("predict"))

    return render_template("predict.html")


#  RESULT 
@app.route("/result/<int:patient_id>")
def result(patient_id):
    if "user" not in session:
        return redirect(url_for("login"))

    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM patients WHERE id = %s", (patient_id,))
        patient = cursor.fetchone()
        cursor.close()
        db.close()

        if not patient:
            flash("Patient record not found.", "error")
            return redirect(url_for("patients"))

        return render_template("result.html", patient=patient)

    except Exception as e:
        flash("Error loading result: " + str(e), "error")
        return redirect(url_for("dashboard"))


#  PATIENTS 
@app.route("/patients")
def patients():
    if "user" not in session:
        return redirect(url_for("login"))

    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM patients ORDER BY created_at DESC")
        data = cursor.fetchall()
        cursor.close()
        db.close()
        return render_template("patients.html", patients=data)

    except Exception as e:
        flash("Error loading patients: " + str(e), "error")
        return render_template("patients.html", patients=[])


#  PDF EXPORT 
@app.route("/patients/<int:patient_id>/pdf")
def export_pdf(patient_id):
    if "user" not in session:
        return redirect(url_for("login"))

    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM patients WHERE id = %s", (patient_id,))
        patient = cursor.fetchone()
        cursor.close()
        db.close()

        if not patient:
            flash("Patient not found.", "error")
            return redirect(url_for("patients"))

        buffer = io.BytesIO()
        doc    = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        story  = []

        # Title
        title_style = ParagraphStyle("CustomTitle", parent=styles["Title"],
                                      fontSize=22, textColor=colors.HexColor("#1e40af"))
        story.append(Paragraph("Skin Cancer Detection Report", title_style))
        story.append(Spacer(1, 0.2 * inch))
        story.append(Paragraph(
            f"Generated: {datetime.now().strftime('%B %d, %Y at %H:%M')} — by Dr. {patient['created_by']}",
            styles["Normal"]
        ))
        story.append(Spacer(1, 0.3 * inch))

        # Patient info table
        table_data = [
            ["Patient Name",  patient["name"]],
            ["Age",           f"{patient['age']} years"],
            ["Diagnosis",     patient["diagnosis"]],
            ["Short Code",    patient["short_code"]],
            ["Risk Level",    patient["risk_level"]],
            ["Confidence",    f"{patient['confidence']}%"],
            ["Analysis Date", str(patient["created_at"])],
            ["Analyzed By",   patient["created_by"]],
        ]
        table = Table(table_data, colWidths=[2 * inch, 4 * inch])
        table.setStyle(TableStyle([
            ("BACKGROUND",  (0, 0), (0, -1), colors.HexColor("#dbeafe")),
            ("FONTNAME",    (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE",    (0, 0), (-1, -1), 11),
            ("PADDING",     (0, 0), (-1, -1), 8),
            ("GRID",        (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(table)
        story.append(Spacer(1, 0.3 * inch))

        # Risk level highlight
        risk_color = (colors.HexColor("#dc2626") if patient["risk_level"] == "Malignant"
                      else colors.HexColor("#d97706") if patient["risk_level"] == "Pre-malignant"
                      else colors.HexColor("#16a34a"))

        risk_style = ParagraphStyle("Risk", parent=styles["Normal"],
                                     fontSize=13, textColor=risk_color,
                                     fontName="Helvetica-Bold")
        story.append(Paragraph(f"Risk Assessment: {patient['risk_level']}", risk_style))
        story.append(Spacer(1, 0.3 * inch))

        # Disclaimer
        disclaimer = ParagraphStyle("Disclaimer", parent=styles["Normal"],
                                     fontSize=9, textColor=colors.grey)
        story.append(Paragraph(
            "Disclaimer: This report is AI-assisted and should not replace professional "
            "medical advice. Always consult a certified dermatologist for final diagnosis.",
            disclaimer
        ))

        doc.build(story)
        buffer.seek(0)

        safe_name = patient["name"].replace(" ", "_")
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"report_{safe_name}_{patient_id}.pdf",
            mimetype="application/pdf"
        )

    except Exception as e:
        flash("PDF error: " + str(e), "error")
        return redirect(url_for("patients"))


if __name__ == "__main__":
    app.run(debug=True)