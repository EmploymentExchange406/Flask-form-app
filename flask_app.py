from flask import Flask, render_template, request, redirect
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pytz
import os
import json
import base64


app = Flask(__name__)

# Google Sheets setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
#creds = ServiceAccountCredentials.from_json_keyfile_name("flaskformdataproject-38167ba1ba59.json", scope)
creds_json = base64.b64decode(os.environ["GOOGLE_CREDS"]).decode("utf-8")
creds_dict = json.loads(creds_json)
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open("Placement_Form_Responses").sheet1

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
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
         
        # Add to Google Sheet
        sheet.append_row([
            fullname, address, taluka, state, email, mobile,
            qualification, gender, category, experience,
            employment, employmentCard, employmentCardNumber, timestamp
        ])
        return redirect('/?success=true')

    return render_template('form.html',success=True)

if __name__ == '__main__':
  app.run(host='0.0.0.0', port=5000)