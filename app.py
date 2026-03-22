import os
import json
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai

app = Flask(__name__)
app.secret_key = "MGIC_NCC_PORTAL_ULTIMATE_2026"

# --- 1. CONFIGURATION & SETUP ---

# AI Setup (Gemini) - Render से Key उठाना
GEMINI_KEY = os.environ.get('GEMINI_API_KEY')
if not GEMINI_KEY:
    raise ValueError("Error: GEMINI_API_KEY not found in Render Environment!")
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Google Sheets Setup - Render से JSON चाबी उठाना
def get_gspread_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    json_key = os.environ.get('SERVICE_ACCOUNT_JSON')
    if not json_key:
        raise ValueError("Error: SERVICE_ACCOUNT_JSON not found in Render Environment!")
    
    creds_dict = json.loads(json_key)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)

# आपकी Google Sheet का नाम
SHEET_NAME = "NCC_Smart_Portal_Data"

# डिजाइन के लिए ऑनलाइन फोटो लिंक्स (इन्हें आप बदल भी सकते हैं)
BG_IMAGE = "https://images.unsplash.com/photo-1599661046289-e31897846e41?q=80&w=1920" # Indian Flag/Army Background
LOGO_IMAGE = "https://upload.wikimedia.org/wikipedia/commons/thumb/1/12/NCC_logo.png/220px-NCC_logo.png" # NCC Logo

# --- 2. HTML TEMPLATES (Inline for complete structure) ---

HTML_HEADER = f"""
<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MGIC NCC स्मार्ट पोर्टल</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {{
            background: url('{BG_IMAGE}') no-repeat center center fixed;
            background-size: cover;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            color: #333;
        }}
        .overlay {{
            background: rgba(255, 255, 255, 0.85);
            min-height: 100vh;
        }}
        .navbar {{ background-color: #003366 !important; }} /* Navy Blue */
        .card {{
            border: none;
            border-radius: 15px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }}
        .card:hover {{ transform: translateY(-5px); }}
        .btn-primary {{ background-color: #004080; border: none; }}
        .btn-primary:hover {{ background-color: #0059b3; }}
    </style>
</head>
<body>
<div class="overlay">
"""

HTML_FOOTER = """
</div>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

NAVBAR = f"""
<nav class="navbar navbar-expand-lg navbar-dark bg-dark">
  <div class="container-fluid">
    <img src="{LOGO_IMAGE}" alt="NCC Logo" height="40" class="d-inline-block align-text-top me-2">
    <a class="navbar-brand" href="/dashboard">MGIC NCC पोर्टल</a>
    <span class="navbar-text text-light me-3">जय हिंद, {{ user_name }}!</span>
    <a href="/logout" class="btn btn-outline-light btn-sm">लॉगआउट</a>
  </div>
</nav>
<div class="container mt-4">
"""

# --- 3. ROUTES & LOGIC ---

@app.route('/')
def login_page():
    if 'user' in session: return redirect('/dashboard')
    
    return HTML_HEADER + f"""
    <div class="container d-flex justify-content-center align-items-center" style="min-height: 100vh;">
        <div class="card p-5 text-center" style="max-width: 400px; width: 100%;">
            <img src="{LOGO_IMAGE}" alt="NCC Logo" height="100" class="mx-auto d-block mb-3">
            <h2 class="mb-4" style="color: #003366;">कैडेट लॉगिन</h2>
            <form action="/login" method="post">
                <input type="text" name="reg_no" class="form-control mb-3" placeholder="Reg No (e.g., TEST001)" required>
                <input type="password" name="password" class="form-control mb-3" placeholder="पासवर्ड (e.g., 123)" required>
                <button type="submit" class="btn btn-primary w-100">लॉगिन करें</button>
            </form>
            <p class="mt-3 text-muted">MGIC NCC इकाई</p>
        </div>
    </div>
    """ + HTML_FOOTER

@app.route('/login', methods=['POST'])
def login():
    reg_no = request.form.get('reg_no').strip()
    password = request.form.get('password').strip()
    
    try:
        client = get_gspread_client()
        sheet = client.open(SHEET_NAME).worksheet("Cadet_Master")
        records = sheet.get_all_records()
        
        for row in records:
            if str(row['Reg_No']) == reg_no and str(row['Password']) == password:
                session['user'] = reg_no
                session['user_name'] = row['Name']
                return redirect('/dashboard')
        
        return HTML_HEADER + "<div class="container text-center mt-5"><h3>गलत Reg No या Password!</h3><a href="/" class="btn btn-primary">फिर से कोशिश करें</a></div>" + HTML_FOOTER
    except Exception as e:
        return f"लॉगिन एरर: {str(e)}"

@app.route('/dashboard')
def dashboard():
    if 'user' not in session: return redirect('/')
    
    return HTML_HEADER + NAVBAR.replace("{{ user_name }}", session['user_name']) + """
        <h2 class="mb-4">आपका डैशबोर्ड</h2>
        <div class="row g-4">
            <div class="col-md-4">
                <div class="card text-center p-3">
                    <h3>🤖 AI सूबेदार</h3>
                    <p>NCC से जुड़े सवाल पूछें</p>
                    <a href="/ai_teacher" class="btn btn-primary">पूछें</a>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card text-center p-3">
                    <h3>📝 ऑनलाइन टेस्ट</h3>
                    <p>अपनी तैयारी जांचें</p>
                    <a href="/quiz" class="btn btn-primary">टेस्ट दें</a>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card text-center p-3">
                    <h3>📚 लाइब्रेरी</h3>
                    <p>स्टडी मटेरियल और नोट्स</p>
                    <a href="/library" class="btn btn-primary">पढ़ें</a>
                </div>
            </div>
        </div>
    </div>
    """ + HTML_FOOTER

# --- 4. FEATURE ROUTES (AI, QUIZ, LIBRARY) ---

@app.route('/ai_teacher', methods=['GET', 'POST'])
def ai_teacher():
    if 'user' not in session: return redirect('/')
    
    response = ""
    if request.method == 'POST':
        question = request.form.get('question')
        try:
            # AI को NCC के माहौल में ढालना
            prompt = f"आप एक सीनियर NCC इंस्ट्रक्टर (सूबेदार) हैं। इस कैडेट के सवाल का हिंदी में अनुशासित जवाब दें: {question}"
            ai_response = model.generate_content(prompt)
            response = ai_response.text
        except:
            response = "माफ़ करना कैडेट, नेटवर्क में कुछ गड़बड़ है।"

    return HTML_HEADER + NAVBAR.replace("{{ user_name }}", session['user_name']) + f"""
        <h3>🤖 AI सूबेदार मेजर</h3>
        <form method="post" class="mb-4">
            <input type="text" name="question" class="form-control mb-2" placeholder="अपना सवाल यहाँ लिखें..." required>
            <button type="submit" class="btn btn-primary">पूछें</button>
        </form>
        {{% if response %}}
        <div class="card p-3 bg-light">
            <strong>जवाब:</strong><p>{{ response }}</p>
        </div>
        {{% endif %}}
    </div>
    """.replace("{{ response }}", response) + HTML_FOOTER

@app.route('/quiz')
def quiz():
    if 'user' not in session: return redirect('/')
    
    try:
        client = get_gspread_client()
        sheet = client.open(SHEET_NAME).worksheet("Quiz_Data")
        questions = sheet.get_all_records()
        
        quiz_html = ""
        for i, q in enumerate(questions):
            quiz_html += f"""
            <div class="card mb-3 p-3">
                <h5>Q{i+1}: {q['Question']}</h5>
                <input type="radio" name="q{i}" value="A"> {q['Option_A']}<br>
                <input type="radio" name="q{i}" value="B"> {q['Option_B']}<br>
                <input type="radio" name="q{i}" value="C"> {q['Option_C']}<br>
                <input type="radio" name="q{i}" value="D"> {q['Option_D']}<br>
            </div>
            """
        
        return HTML_HEADER + NAVBAR.replace("{{ user_name }}", session['user_name']) + f"""
            <h3>📝 ऑनलाइन टेस्ट</h3>
            <form action="/submit_quiz" method="post">
                {quiz_html}
                <button type="submit" class="btn btn-success">सबमिट करें</button>
            </form>
        </div>
        """ + HTML_FOOTER
    except:
        return "टेस्ट लोड नहीं हो पाया।"

@app.route('/library')
def library():
    if 'user' not in session: return redirect('/')
    
    try:
        client = get_gspread_client()
        sheet = client.open(SHEET_NAME).worksheet("Content_Library")
        topics = sheet.get_all_records()
        
        lib_html = ""
        for topic in topics:
            lib_html += f"""
            <div class="col-md-6">
                <div class="card mb-3 p-3">
                    <h4>{topic['Topic_Name']}</h4>
                    <p>{topic['Description']}</p>
                    <a href="{topic['Link']}" target="_blank" class="btn btn-outline-primary btn-sm">पढ़ें</a>
                </div>
            </div>
            """
            
        return HTML_HEADER + NAVBAR.replace("{{ user_name }}", session['user_name']) + f"""
            <h3>📚 कंटेंट लाइब्रेरी</h3>
            <div class="row">{lib_html}</div>
        </div>
        """ + HTML_FOOTER
    except:
        return "लाइब्रेरी लोड नहीं हो पाई।"

@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('user_name', None)
    return redirect('/')

if __name__ == "__main__":
    app.run(debug=True)
