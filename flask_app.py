from flask import Flask, render_template, request, redirect, url_for
from flask_mail import Mail, Message
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

app = Flask(__name__)
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

# Flask-Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'employmentexchange406@gmail.com'  
app.config['MAIL_PASSWORD'] = 'wvdeodgvpyneqxrt'     
app.config['MAIL_DEFAULT_SENDER'] = 'employmentexchange406@gmail.com'

mail = Mail(app)

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
        ])
        registration_id = len(sheet.col_values(1)) - 1
        event_name, event_date, event_time, event_venue = get_event_details()
        # Compose the email
        message_body = f"""Dear {fullname},
        
        Greetings from Office of the Commissioner, Labour & Employment, Regional Employment Exchange, Govt. of Goa.
        
        Congratulations! Your registration for {event_name} has been successfully completed.
        
        📌 Registration Details:
        • Name: {fullname}
        • Registration ID: {registration_id}
        • Event Date: {event_date}
        • Event Time: {event_time}
        • Venue: {event_venue}

        Thank you for taking this step. We look forward to seeing you!

        Regards, 
        Regional Employment Exchange, 
        Model Career Centre,
        Panaji Goa 
        """
        
        # Send the email
        try:
            msg = Message("Registration Confirmation",
                          recipients=[email])
            msg.body = message_body
            mail.send(msg)
        except Exception as e:
            print("Email sending failed:", e)
            
        return redirect('/?success=true')
        
    success = request.args.get('success') == 'true'
    return render_template('form.html', success=success)

  
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
        # Fetch only necessary rows instead of get_all_records
    all_values = sheet.get_all_values()
    headers = all_values[0]
    rows = all_values[1:]
    
    
    total_registrations = len(rows)
    
    
    # Index mapping for columns
    gender_idx = headers.index("Gender")
    category_idx = headers.index("Category")
    employment_idx = headers.index("Employment Status")
    empcard_idx = headers.index("Employment Card")
    
    
    # Aggregate counts
    gender_counts = {}
    category_counts = {}
    employment_counts = {}
    empcard_counts = {}
    
    
    for row in rows:
     gender = row[gender_idx]
    category = row[category_idx]
    employment_status = row[employment_idx]
    empcard_status = row[empcard_idx]
    
    
    gender_counts[gender] = gender_counts.get(gender, 0) + 1
    category_counts[category] = category_counts.get(category, 0) + 1
    employment_counts[employment_status] = employment_counts.get(employment_status, 0) + 1
    empcard_counts[empcard_status] = empcard_counts.get(empcard_status, 0) + 1
    
    
    return render_template('admin_report.html',
    total_registrations=total_registrations,
    gender_counts=gender_counts,
    category_counts=category_counts,
    employment_counts=employment_counts,
    empcard_counts=empcard_counts)
    # --- Logout Admin ---
@app.route('/logout',methods=['GET', 'POST'])
def logout():
    session.pop('logged_in', None)
    return redirect (url_for('admin'))

if __name__ == '__main__':
 app.run(host='0.0.0.0', port=5000)

