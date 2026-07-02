from fileinput import filename
import io
from flask import Flask, render_template, request, redirect, url_for
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pytz
import os
import json
import base64
import pandas as pd
from functools import wraps
from flask import session
from datetime import timedelta
from flask import send_file,request,jsonify
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__)
#@app.before_request
#def maintenance_mode():
#    return render_template("closed.html")
app.secret_key = 'super_secret_admin_key_0987654321'
app.permanent_session_lifetime = timedelta(minutes=30)

def get_event_name():
    return event_meta_sheet.acell('A2').value or "Your Event"

def get_event_date():
    return event_meta_sheet.acell('B2').value or "Event Date"

def get_event_time():
    return event_meta_sheet.acell('C2').value or "Event Time"

def get_event_venue():
    return event_meta_sheet.acell('D2').value or "Venue"

def set_event_details(name, date, time, venue):
     event_meta_sheet.update('A2:D2', [[name, date, time, venue]])


# Google Sheets setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
#creds = ServiceAccountCredentials.from_json_keyfile_name("flaskformdataproject-38167ba1ba59.json", scope)
creds_json = base64.b64decode(os.environ["GOOGLE_CREDS"]).decode("utf-8")
creds_dict = json.loads(creds_json)
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open("Placement_Form_Responses").sheet1
event_meta_sheet = client.open("Placement_Form_Responses").worksheet("Event_Details")


def get_event_details():
 """Fetch only one row (A2:D2) instead of whole sheet"""
 row = event_meta_sheet.row_values(2)
 name = row[0] if len(row) > 0 else "Your Event"
 date = row[1] if len(row) > 1 else "Event Date"
 time = row[2] if len(row) > 2 else "Event Time"
 venue = row[3] if len(row) > 3 else "Venue"
 return name, date, time, venue


def set_event_details(name, date, time, venue):
 event_meta_sheet.update('A2:D2', [[name, date, time, venue]])

@app.route("/", methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
            fullname = request.form.get('fullname', '')
            address = request.form.get('address', '')
            taluka = request.form.get('taluka', '')
            state = request.form.get('state', '')
            email = request.form.get('email', '')
            mobile = request.form.get('mobile', '')
            qualification = request.form.get('qualification', '')
            gender = request.form.get('gender', '')
            category = request.form.get('category', '')
            experience = request.form.get('experience', '')
            employment = request.form.get('employment', '')
            employmentCard = request.form.get('employmentCard', '')
            employmentCardNumber = request.form.get('employmentCardNumber','')
    
            # VALIDATIONS
            if not (mobile.isdigit() and len(mobile) == 10):
                return "Error: Mobile number must be exactly 10 digits."
            try : experience = float(experience)
            except ValueError:
             return "Error: Experience must be a number."
    
            # Date and time
            ist = pytz.timezone('Asia/Kolkata')
            timestamp = datetime.now(ist).strftime("%Y-%m-%d %H:%M:%S")
             
            # Add to Google Sheet
            sheet.append_row([
                fullname, address, taluka, state, email, mobile,
                qualification, gender, category, experience,
                employment, employmentCard, employmentCardNumber, timestamp
            ], table_range="A1:O1")
    
            # Use row number as registration ID
            registration_id = len(sheet.col_values(1)) - 1

        # Redirect to self with success + registration info
            return redirect(url_for("index", success="true", reg_id=registration_id, name=fullname))

    success = request.args.get("success") == "true"
    reg_id = request.args.get("reg_id")
    name = request.args.get("name")
    return render_template("form.html", success=success, reg_id=reg_id, name=name)
    
 # Event details
event_name, event_date, event_time, event_venue = get_event_details()
    
@app.route("/download_ticket/<int:reg_id>")
def download_ticket(reg_id):
    fullname = request.args.get("name", "Participant")
    event_name, event_date, event_time, event_venue = get_event_details()

    # 1️⃣ Open your custom image template
    template_path = "templates/Pass.png"  # Replace with your image file
    image = Image.open(template_path).convert("RGB")  # Ensure it's in RGB mode for PDF

    # 2️⃣ Prepare to draw text
    draw = ImageDraw.Draw(image)
    # Choose a font and size (adjust path or use default)
    try:
        font = ImageFont.truetype("font/arialbd.ttf", size=40)
    except:
        font = ImageFont.load_default()

    # 3️⃣ Draw the dynamic data on the image
    # Adjust x, y coordinates to match your template
    draw.text((520,652), event_name, fill="black", font=font)
    draw.text((520,794), fullname, fill="black", font=font)
    draw.text((725,923), str(reg_id), fill="black", font=font)
    draw.text((520,1050), event_date, fill="black", font=font)
    draw.text((520,1165), event_time, fill="black", font=font)
    draw.text((520,1300), event_venue, fill="black", font=font)

    # 4️⃣ Save the image as PDF in memory
    output_stream = io.BytesIO()
    image.save(output_stream, format="PNG")
    output_stream.seek(0)

    # 5️⃣ Send the PDF to user
    return send_file(
        output_stream,
        as_attachment=True,
        download_name=f"ticket_{reg_id}.PNG",
        mimetype="application/png"
    )
     # --- Admin Login & Update Event 
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if 'logged_in' not in session:
        if request.method == 'POST':
            password = request.form['password']
            if password == 'admin123':
                session.permanent = True
                session['logged_in'] = True
                return redirect(url_for('admin_panel'))
            else:
                return "Incorrect password"

        if 'logged_in' not in session:
            return render_template('admin_login.html')
        
    return redirect(url_for('admin_panel'))

@app.route('/admin-panel')
def admin_panel():
    if 'logged_in' not in session:
        return redirect(url_for('admin'))

    return render_template('admin_panel.html')

@app.route('/set_event', methods=['GET', 'POST'])
def set_event():
    if 'logged_in' not in session:
        return redirect(url_for('admin'))

    # Load current event details from Google Sheet
    current_event_row = event_meta_sheet.row_values(2)
    current_event = current_event_row[0] if len(current_event_row) > 0 else ''
    current_date = current_event_row[1] if len(current_event_row) > 1 else ''
    current_time = current_event_row[2] if len(current_event_row) > 2 else ''
    current_venue = current_event_row[3] if len(current_event_row) > 3 else ''
    message = None

    if request.method == "POST":
        new_event_name = request.form.get("event_name")
        new_event_date = request.form.get("event_date")
        new_event_time = request.form.get("event_time")
        new_event_venue = request.form.get("venue")

        # Save to Google Sheet
        set_event_details(new_event_name, new_event_date, new_event_time, new_event_venue)

        # Update variables for display
        current_event = new_event_name
        current_date = new_event_date
        current_time = new_event_time
        current_venue = new_event_venue

        message = "✅ Event details updated successfully!"

    return render_template("admin.html",
        event_name=current_event,
        event_date=current_date,
        event_time=current_time,
        venue=current_venue,
        message=message
    )

@app.route('/generate-report', methods=['GET', 'POST'])
def generate_report():
    all_values = sheet.get_all_values()
    if not all_values:
        return "❌ No data found in sheet."

    headers = all_values[0]
    rows = all_values[1:]
    total_registrations = len(rows)

    # Convert headers to lowercase for flexible matching
    headers_lower = [h.lower().strip() for h in headers]

    try:
        gender_idx = headers_lower.index("gender")
        category_idx = headers_lower.index("category")
        employment_idx = headers_lower.index("employment status")
        empcard_idx = headers_lower.index("registered for employment card")
    except ValueError as e:
        return f"❌ Missing column: {e}"

    gender_counts = {}
    category_counts = {}
    employment_counts = {}
    empcard_counts = {}

    for row in rows:
        if len(row) <= max(gender_idx, category_idx, employment_idx, empcard_idx):
            continue

        gender = row[gender_idx]
        category = row[category_idx]
        employment_status = row[employment_idx]
        empcard_status = row[empcard_idx]

        gender_counts[gender] = gender_counts.get(gender, 0) + 1
        category_counts[category] = category_counts.get(category, 0) + 1
        employment_counts[employment_status] = employment_counts.get(employment_status, 0) + 1
        empcard_counts[empcard_status] = empcard_counts.get(empcard_status, 0) + 1

    return render_template(
        'generate_report.html',
        total_registrations=total_registrations,
        gender_counts=gender_counts,
        category_counts=category_counts,
        employment_counts=employment_counts,
        empcard_counts=empcard_counts
    )

    # --- Logout Admin ---
@app.route('/logout',methods=['GET', 'POST'])
def logout():
    session.pop('logged_in', None)
    return redirect (url_for('admin'))

if __name__ == '__main__':
 app.run(host='0.0.0.0', port=5000)

