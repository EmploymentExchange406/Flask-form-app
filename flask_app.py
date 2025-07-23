from flask import Flask, render_template, request, redirect
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

app = Flask(__name__)

# Google Sheets setup
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('registration-466210-4946687b0717.json', scope)
client = gspread.authorize(creds)
sheet = client.open("My_Form_Responses").sheet1

@app.route('/', methods=['GET', 'POST'])
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
        employment_card = request.form.get('employment_card', '')

        # VALIDATIONS
        if not (mobile.isdigit() and len(mobile) == 10):
            return "Error: Mobile number must be exactly 10 digits."
        if not experience.isdigit():
            return "Error: Experience must be a number."

        # Date and time
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
         
        # Add to Google Sheet
        sheet.append_row([
            fullname, address, taluka, state, email, mobile,
            qualification, gender, category, experience,
            employment, employment_card, timestamp
        ])
        return redirect('/')

    return render_template('form.html')

if __name__ == '__main__':
    app.run(debug=True)
from flask import Flask, render_template, request, redirect
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

app = Flask(__name__)

