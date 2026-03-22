import os
import json
from flask import Flask, render_template, request, redirect, url_for, session
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai

app = Flask(__name__)
app.secret_key = "MGIC_NCC_ULTIMATE_2026"

# 1. AI और Google Sheets का सेटअप (सीधे रेंडर की तिजोरी से)
def get_ai_model():
    api_key = os.environ.get('GEMINI_API_KEY')
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-1.5-flash')

def get_gspread_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    json_key = os.environ.get('SERVICE_ACCOUNT_JSON')
    creds_dict = json.loads(json_key)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)

# 2. ऑनलाइन फोटो और डिजाइन (NCC Logo)
LOGO_URL = "https://upload.wikimedia.org/wikipedia/commons/thumb/1/12/NCC_logo.png/220px-NCC_logo.png"

# 3. मुख्य रूट्स (Routes)
@app.route('/')
def login_page():
    return f'''
    <body style="text-align:center; background-color:#f0f2f5; font-family:sans-serif; padding-top:50px;">
        <img src="{LOGO_URL}" width="100"><br>
        <h2>MGIC NCC स्मार्ट पोर्टल</h2>
        <form action="/login" method="post" style="display:inline-block; background:white; padding:20px; border-radius:10px; box-shadow:0 4px 8px rgba(0,0,0,0.1);">
            <input type="text" name="reg_no" placeholder="Reg No" required style="margin-bottom:10px; padding:10px; width:200px;"><br>
            <input type="password" name="password" placeholder="Password" required style="margin-bottom:10px; padding:10px; width:200px;"><br>
            <button type="submit" style="padding:10px 20px; background:#003366; color:white; border:none; border-radius:5px; cursor:pointer;">लॉगिन करें</button>
        </form>
    </body>
    '''

@app.route('/login', methods=['POST'])
def login():
    reg_no = request.form.get('reg_no')
    password = request.form.get('password')
    try:
        client = get_gspread_client()
        sheet = client.open("NCC_Smart_Portal_Data").worksheet("Cadet_Master")
        records = sheet.get_all_records()
        for row in records:
            if str(row['Reg_No']) == reg_no and str(row['Password']) == password:
                session['user'] = row['Name']
                return redirect('/dashboard')
        return "गलत विवरण! <a href='/'>Retry</a>"
    except Exception as e:
        return f"त्रुटि: {str(e)}"

@app.route('/dashboard')
def dashboard():
    if 'user' not in session: return redirect('/')
    return f"<h1>जय हिंद, {session['user']}!</h1><p>आपका डैशबोर्ड तैयार है।</p><a href='/ai'>AI सूबेदार से पूछें</a>"

@app.route('/ai', methods=['GET', 'POST'])
def ai_teacher():
    if 'user' not in session: return redirect('/')
    ans = ""
    if request.method == 'POST':
        model = get_ai_model()
        q = request.form.get('q')
        res = model.generate_content(f"You are an NCC Instructor. Answer in Hindi: {q}")
        ans = res.text
    return f"<h3>AI सूबेदार मेजर</h3><form method='post'><input name='q' placeholder='पूछें...'><button>Ask</button></form><p>{ans}</p>"

if __name__ == "__main__":
    app.run()
