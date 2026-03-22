import os
import json
from flask import Flask, render_template, request, redirect, url_for, session
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai

app = Flask(__name__)
app.secret_key = "MGIC_NCC_ULTIMATE_SUCCESS_2026"

# --- 1. रेंडर की तिजोरी से डेटा खींचने का 'ऑटोमेशन' ---

def get_gspread_client():
    # रेंडर की एनवायरनमेंट से चाबी उठाना
    json_key = os.environ.get('SERVICE_ACCOUNT_JSON')
    if not json_key:
        raise ValueError("SERVICE_ACCOUNT_JSON missing in Render Environment!")
    
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = json.loads(json_key)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)

def get_ai_instructor(prompt):
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        return "AI चाबी (API Key) नहीं मिली!"
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    # AI को इंस्ट्रक्टर की तरह व्यवहार करने का आदेश
    full_prompt = f"आप महात्मा गांधी इंटर कॉलेज के एक सीनियर NCC सूबेदार हैं। अनुशासित और मददगार लहजे में हिंदी में जवाब दें: {prompt}"
    try:
        response = model.generate_content(full_prompt)
        return response.text
    except:
        return "माफ़ करना कैडेट, सिग्नल में गड़बड़ है।"

# --- 2. मुख्य रूट्स (पोर्टल के फंक्शन्स) ---

@app.route('/')
def login_page():
    if 'user' in session: return redirect('/dashboard')
    # प्रोफेशनल लॉगिन पेज (Inline HTML)
    return '''
    <body style="text-align:center; font-family:sans-serif; background:#f0f2f5; padding-top:100px;">
        <img src="https://upload.wikimedia.org/wikipedia/commons/1/12/NCC_logo.png" width="80"><br>
        <h2>MGIC NCC स्मार्ट पोर्टल</h2>
        <form action="/login" method="post" style="display:inline-block; background:white; padding:30px; border-radius:15px; box-shadow:0 4px 10px rgba(0,0,0,0.1);">
            <input type="text" name="reg_no" placeholder="Reg No (TEST001)" required style="width:250px; padding:10px; margin-bottom:15px; border:1px solid #ccc; border-radius:5px;"><br>
            <input type="password" name="password" placeholder="Password" required style="width:250px; padding:10px; margin-bottom:15px; border:1px solid #ccc; border-radius:5px;"><br>
            <button type="submit" style="width:272px; padding:10px; background:#003366; color:white; border:none; border-radius:5px; cursor:pointer;">लॉगिन करें</button>
        </form>
    </body>
    '''

@app.route('/login', methods=['POST'])
def login():
    reg_no = request.form.get('reg_no').strip()
    password = request.form.get('password').strip()
    try:
        client = get_gspread_client()
        sheet = client.open("NCC_Smart_Portal_Data").worksheet("Cadet_Master")
        records = sheet.get_all_records()
        for row in records:
            if str(row['Reg_No']) == reg_no and str(row['Password']) == password:
                session['user'] = row['Name']
                return redirect('/dashboard')
        return "विवरण सही नहीं हैं! <a href='/'>Retry</a>"
    except Exception as e:
        return f"गूगल शीट कनेक्शन फेल: {str(e)}"

@app.route('/dashboard')
def dashboard():
    if 'user' not in session: return redirect('/')
    return f'''
    <body style="font-family:sans-serif; background:#f4f7f6; padding:20px;">
        <nav style="background:#003366; color:white; padding:15px; border-radius:10px; display:flex; justify-content:space-between; align-items:center;">
            <span>जय हिंद, {session['user']}!</span>
            <a href="/logout" style="color:white; text-decoration:none; border:1px solid white; padding:5px 10px; border-radius:5px;">Logout</a>
        </nav>
        <div style="display:flex; gap:20px; margin-top:30px; flex-wrap:wrap;">
            <div style="background:white; padding:20px; border-radius:10px; flex:1; min-width:250px; box-shadow:0 2px 5px rgba(0,0,0,0.1);">
                <h3>🤖 AI सूबेदार</h3>
                <p>NCC ट्रेनिंग से जुड़े सवाल पूछें</p>
                <a href="/ai" style="display:inline-block; padding:10px 20px; background:#004080; color:white; text-decoration:none; border-radius:5px;">पूछें</a>
            </div>
            <div style="background:white; padding:20px; border-radius:10px; flex:1; min-width:250px; box-shadow:0 2px 5px rgba(0,0,0,0.1);">
                <h3>📝 ऑनलाइन टेस्ट</h3>
                <p>क्विज और तैयारी जांचें</p>
                <a href="/quiz" style="display:inline-block; padding:10px 20px; background:#004080; color:white; text-decoration:none; border-radius:5px;">शुरू करें</a>
            </div>
        </div>
    </body>
    '''

@app.route('/ai', methods=['GET', 'POST'])
def ai_page():
    if 'user' not in session: return redirect('/')
    ans = ""
    if request.method == 'POST':
        ans = get_ai_instructor(request.form.get('q'))
    return f'''
    <body style="font-family:sans-serif; padding:20px; background:#eef2f3;">
        <h3>🤖 AI सूबेदार मेजर (MGIC NCC)</h3>
        <form method="post" style="margin-bottom:20px;">
            <input name="q" placeholder="पूछें, कैडेट..." style="width:70%; padding:10px;">
            <button style="padding:10px 20px; background:#003366; color:white; border:none;">Ask</button>
        </form>
        <div style="background:white; padding:15px; border-radius:10px; min-height:100px; border-left:5px solid #003366;">
            <strong>जवाब:</strong><p>{ans}</p>
        </div>
        <br><a href="/dashboard">वापस डैशबोर्ड पर</a>
    </body>
    '''

@app.route('/quiz')
def quiz():
    if 'user' not in session: return redirect('/')
    return "<h3>क्विज सेक्शन जल्द ही चालू होगा (Google Sheet से कनेक्ट हो रहा है...)</h3><a href='/dashboard'>Back</a>"

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == "__main__":
    # रेंडर के डायनामिक पोर्ट को हैंडल करना
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
