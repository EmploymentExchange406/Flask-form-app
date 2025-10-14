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
sheet = client.open("Placement_Form_Responses").worksheet("Career Conclave")
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
            email = request.form.get('email', '')
            mobile = request.form.get('mobile', '')
            gender = request.form.get('gender', '')
            category = request.form.get('category', '')
            birth = request.form.get('birth', '')
            college = request.form.get('college', '')
            # VALIDATIONS
            if not (mobile.isdigit() and len(mobile) == 10):
                return "Error: Mobile number must be exactly 10 digits."
            # Date and time
            ist = pytz.timezone('Asia/Kolkata')
            timestamp = datetime.now(ist).strftime("%Y-%m-%d %H:%M:%S")
             
            # Add to Google Sheet
            sheet.append_row([
                fullname, address, taluka, email, mobile,
                gender, category, birth, college, timestamp
            ])
    
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

from flask import request, send_file
from PIL import Image, ImageDraw, ImageFont
import io
import os # We'll use os.path.exists for a safer font check

# --- CONFIGURATION CONSTANTS (Adjust these based on your 'Certificate.png') ---
# 1. Coordinates for the name's *center* point.
# Based on the image, the name "Aditya Babu Shetye" is roughly centered horizontally.
NAME_CENTER_X = 1080  # This seems to be your target X coordinate
NAME_Y_POSITION = 680 # This is your current Y coordinate

# 2. Maximum allowed width for the name in pixels.
# Estimate the available space. For a centered name, this is roughly 2x the distance
# from the center point to the edge of the text area. Let's estimate 1200 pixels max.
MAX_NAME_WIDTH = 1400

# 3. Font sizing limits
MAX_FONT_SIZE = 130  # Your current starting size
MIN_FONT_SIZE = 60   # Don't go smaller than this

# 4. Font path
FONT_PATH = "font/CORALIE.ttf"

# --------------------------------------------------------------------------------

def get_fitting_font_size(draw, name, font_path, max_width):
    """
    Iteratively finds the largest font size that makes the 'name' fit within 'max_width'.
    
    Args:
        draw (ImageDraw.Draw): The drawing context for text measurement.
        name (str): The text string to measure.
        font_path (str): The path to the TrueType font file.
        max_width (int): The maximum allowable width in pixels.

    Returns:
        ImageFont: The PIL font object with the largest fitting size.
    """
    current_size = MAX_FONT_SIZE
    
    # Safely load the font, falling back to default if path is invalid
    if not os.path.exists(font_path):
        return ImageFont.load_default()

    while current_size >= MIN_FONT_SIZE:
        try:
            # 1. Load the font at the current size
            font = ImageFont.truetype(font_path, size=current_size)
        except Exception:
            # Fallback if font file is corrupt, etc.
            return ImageFont.load_default() 
        
        # 2. Measure the text length
        # textlength is the most reliable measurement for width
        text_width = draw.textlength(name, font=font)
        
        # 3. Check if it fits
        if text_width <= max_width:
            return font  # Found the perfect fit!

        # 4. If it doesn't fit, try a smaller size
        current_size -= 5 # Decrease by a step (e.g., 5 points) for efficiency
        
    # If the loop finishes and it still doesn't fit (i.e., we hit MIN_FONT_SIZE)
    # return the font at the minimum size.
    return ImageFont.truetype(font_path, size=MIN_FONT_SIZE)


@app.route("/download_ticket/<int:reg_id>")
def download_ticket(reg_id):
    fullname = request.args.get("name", "Participant")

    # 1️⃣ Open your custom image template
    template_path = "templates/Certificate.png"
    image = Image.open(template_path).convert("RGB")
    draw = ImageDraw.Draw(image)

    # 2️⃣ DYNAMIC FONT SIZE ADJUSTMENT
    # Determine the font and its size that best fits the name
    fitting_font = get_fitting_font_size(draw, fullname, FONT_PATH, MAX_NAME_WIDTH)
    
    # 3️⃣ Calculate the new X position for CENTERING
    # Use the fitting font to measure the final width
    final_text_width = draw.textlength(fullname, font=fitting_font)
    
    # Calculate the starting X coordinate for centering:
    # X_start = X_Center - (Text_Width / 2)
    x_start_position = NAME_CENTER_X - (final_text_width / 2)

    # 4️⃣ Draw the dynamic data on the image
    draw.text(
        (x_start_position, NAME_Y_POSITION),  # Use the calculated X for centering
        fullname, 
        fill="black", 
        font=fitting_font                        # Use the calculated font object
    )

    # 5️⃣ Save the image as PDF in memory
    output_stream = io.BytesIO()
    image.save(output_stream, format="PDF")
    output_stream.seek(0)

    # 6️⃣ Send the PDF to user
    return send_file(
        output_stream,
        as_attachment=True,
        download_name=f"ticket_{reg_id}.pdf",
        mimetype="application/pdf"
    )
    
#@app.route("/download_ticket/<int:reg_id>")
#def download_ticket(reg_id):
#    fullname = request.args.get("name", "Participant")
#
#    # 1️⃣ Open your custom image template
#    template_path = "templates/Certificate.png"  # Replace with your image file
#    image = Image.open(template_path).convert("RGB")  # Ensure it's in RGB mode for PDF
#
#    # 2️⃣ Prepare to draw text
#    draw = ImageDraw.Draw(image)
#    # Choose a font and size (adjust path or use default)
#    try:
#        font = ImageFont.truetype("font/CORALIE.ttf", size=130)
#    except:
#        font = ImageFont.load_default()
#
#    # 3️⃣ Draw the dynamic data on the image
#    # Adjust x, y coordinates to match your template
#    draw.text((1080,680), fullname, fill="black", font=font)
#
#    # 4️⃣ Save the image as PDF in memory
#    output_stream = io.BytesIO()
#    image.save(output_stream, format="PDF")
#    output_stream.seek(0)
#
#    # 5️⃣ Send the PDF to user
#    return send_file(
#        output_stream,
#        as_attachment=True,
#        download_name=f"ticket_{reg_id}.pdf",
#        mimetype="application/pdf"
#    )
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

