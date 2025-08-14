from flask import Flask, render_template, request, redirect, url_for
from flask_mail import Mail, Message
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pytz
import os
import json
import base64
from functools import wraps
from flask import session

app = Flask(__name__)
app.secret_key = 'super_secret_admin_key_0987654321'

def get_event_name():
    try:
        with open('event_name.txt', 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        return "Default Event"

def set_event_name(event_name):
    with open('event_name.txt', 'w') as f:
        f.write(event_name)
        
def get_event_date():
    try:
        with open("event_date.txt", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""

def set_event_date(date):
    with open("event_date.txt", "w") as f:
        f.write(date)

def get_event_time():
    try:
        with open("event_time.txt", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""

def set_event_time(time):
    with open("event_time.txt", "w") as f:
        f.write(time)        

def get_event_venue():
    try:
        with open("venue.txt", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""

def set_event_venue(venue):
    with open("venue.txt", "w") as f:
        f.write(venue)

# Google Sheets setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("flaskformdataproject-38167ba1ba59.json", scope)
#creds_json = base64.b64decode(os.environ["GOOGLE_CREDS"]).decode("utf-8")
#creds_dict = json.loads(creds_json)
#creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open("Placement_Form_Responses").sheet1
event_meta_sheet = client.open("Placement_Form_Responses").worksheet("Sheet2")

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
        all_data = sheet.get_all_records()
        last_entry = all_data[-1]
        
        fullname = last_entry["FULL NAME"]
        email = last_entry["EMAIL ID"]
        registration_id = len(all_data)  # Serial number
        event_date = get_event_date()
        time = get_event_time()
        venue = get_event_venue()
        
        # Read event name from text file
        try:
            with open("event_name.txt", "r") as f:
                event_name = f.read().strip()
        except:
            event_name = "Your Event"  # Fallback in case file not found   
        
        # Compose the email
        message_body = f"""Dear {fullname},
        
        Greetings from Office of the Commissioner, Labour & Employment, Regional Employment Exchange, Govt. of Goa.
        
        Congratulations! Your registration for {event_name} has been successfully completed.
        
        📌 Registration Details:
        • Name: {fullname}
        • Registration ID: {registration_id}
        • Date of Event: {event_date}
        • Time: {time}
        • Venue: {venue}
        
        
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
                session['logged_in'] = True
            else:
                return "Incorrect password"

        if 'logged_in' not in session:
            return render_template('admin_login.html')

    current_event = get_event_name()
    current_date = get_event_date()
    current_time = get_event_time()
    current_venue = get_event_venue()

    if request.method == 'POST' and 'event_name' in request.form:
        new_event = request.form['event_name']
        set_event_name(new_event)
        current_event = new_event

    if 'event_date' in request.form:
            new_date = request.form['event_date']
            set_event_date(new_date)
            current_date = new_date

    if 'event_time' in request.form:
           new_time = request.form['event_time']
           set_event_time(new_time)
           current_time = new_time        

    if 'venue' in request.form:
           new_venue = request.form['venue']
           set_event_venue(new_venue)
           current_venue = new_venue

    return render_template('admin.html', event_name=current_event,event_date=current_date,time=current_time,venue=current_venue)

# --- Logout Admin ---
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect (url_for('admin'))

if __name__ == '__main__':
 app.run(host='0.0.0.0', port=5000)

