from flask import Flask, request, render_template, redirect, url_for, session
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
import pytz
import os
from email.mime.text import MIMEText
import base64
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

app = Flask(__name__)
app.secret_key = 'super_secret_admin_key_0987654321'
app.permanent_session_lifetime = timedelta(minutes=30)

# -----------------------
# Google Sheets Setup
# -----------------------
SCOPE_SHEETS = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("flaskformdataproject-38167ba1ba59.json", SCOPE_SHEETS)
client = gspread.authorize(creds)
sheet = client.open("Placement_Form_Responses").sheet1
event_meta_sheet = client.open("Placement_Form_Responses").worksheet("Event_Details")

# -----------------------
# Gmail API Setup
# -----------------------
SCOPES_GMAIL = ["https://www.googleapis.com/auth/gmail.send"]
CREDENTIALS_FILE = "credentials.json"  # OAuth client secrets
TOKEN_FILE = "token.json"

def get_gmail_service():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES_GMAIL)
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES_GMAIL)
        creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
    return build("gmail", "v1", credentials=creds)

def send_email(to, subject, body):
    service = get_gmail_service()
    message = MIMEText(body)
    message['to'] = to
    message['subject'] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    service.users().messages().send(userId='me', body={'raw': raw}).execute()

# -----------------------
# Event Helpers
# -----------------------
def get_event_details():
    row = event_meta_sheet.row_values(2)
    name = row[0] if len(row) > 0 else "Your Event"
    date = row[1] if len(row) > 1 else "Event Date"
    time = row[2] if len(row) > 2 else "Event Time"
    venue = row[3] if len(row) > 3 else "Venue"
    return name, date, time, venue

def set_event_details(name, date, time, venue):
    event_meta_sheet.update('A2:D2', [[name, date, time, venue]])

# -----------------------
# Flask Routes
# -----------------------
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

        # Validation
        if not (mobile.isdigit() and len(mobile) == 10):
            return "Error: Mobile number must be exactly 10 digits."
        try:
            experience = float(experience)
        except ValueError:
            return "Error: Experience must be a number."

        ist = pytz.timezone('Asia/Kolkata')
        timestamp = datetime.now(ist).strftime("%Y-%m-%d %H:%M:%S")

        # Append to Google Sheet
        sheet.append_row([
            fullname, address, taluka, state, email, mobile,
            qualification, gender, category, experience,
            employment, employmentCard, employmentCardNumber, timestamp
        ])
        registration_id = len(sheet.col_values(1)) - 1
        event_name, event_date, event_time, event_venue = get_event_details()

        # Email content
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
Panaji Goa"""

        # Send email
        try:
            send_email(email, "Registration Confirmation", message_body)
        except Exception as e:
            print("Email sending failed:", e)

        return redirect('/?success=true')

    success = request.args.get('success') == 'true'
    return render_template('form.html', success=success)

# -----------------------
# Admin Routes
# -----------------------
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

        set_event_details(new_event_name, new_event_date, new_event_time, new_event_venue)
        current_event, current_date, current_time, current_venue = new_event_name, new_event_date, new_event_time, new_event_venue
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
    headers = all_values[0]
    rows = all_values[1:]
    
    total_registrations = len(rows)
    gender_idx = headers.index("Gender")
    category_idx = headers.index("Category")
    employment_idx = headers.index("Employment Status")
    empcard_idx = headers.index("Employment Card")

    gender_counts, category_counts, employment_counts, empcard_counts = {}, {}, {}, {}

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

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
