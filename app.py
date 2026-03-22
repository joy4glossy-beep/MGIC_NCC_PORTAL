import os
import json
from flask import Flask, render_template, request, redirect, url_for, session
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai
from datetime import datetime

app = Flask(__name__)
app.secret_key = "MGIC_NCC_2026_V3_6_STABLE"

# --- 1. रेंडर और गूगल शीट का पक्का कनेक्शन ---
def get_sheet(sheet_name):
    json_key = os.environ.get('SERVICE_ACCOUNT_JSON')
    if not json_key:
        raise ValueError("SERVICE_ACCOUNT_JSON missing in Render!")
    
    creds_dict = json.loads(json_key)
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client.open("NCC_Smart_Portal_Data").worksheet(sheet_name)

# --- 2. स्मार्ट लॉगर फंक्शन ---
def log_usage(reg_no, action, query="-"):
    try:
        sheet = get_sheet("Usage_Logs")
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([now, reg_no, action, query])
    except:
        pass

# --- 3. डिजाइन (CSS) ---
UI_STYLE = '''
<style>
    body { font-family: 'Segoe UI', sans-serif; background: #f0f2f5; margin: 0; padding-bottom: 50px; text-align: center; color: #333; -webkit-font-smoothing: antialiased; }
    .header { background: linear-gradient(135deg, #003366, #00509d); color: white; padding: 15px 20px; display: flex; justify-content: space-between; align-items: center; position: sticky; top: 0; z-index: 1000; box-shadow: 0 2px 10px rgba(0,0,0,0.2); }
    .notice-bar { background: #ffcc00; color: #000; padding: 10px; font-weight: bold; font-size: 14px; overflow: hidden; white-space: nowrap; border-bottom: 2px solid #e6b800; }
    .notice-text { display: inline-block; animation: marquee 15s linear infinite; }
    @keyframes marquee { 0% { transform: translateX(100%); } 100% { transform: translateX(-100%); } }
    .main-card { background: white; padding: 20px; margin: 15px auto; border-radius: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); width: 85%; max-width: 400px; border-left: 8px solid #003366; transition: 0.3s; cursor: pointer; text-align: left; }
    .btn { background: #003366; color: white; padding: 12px 25px; border-radius: 10px; text-decoration: none; font-weight: bold; border: none; cursor: pointer; display: inline-block; }
    .mic-btn { background: #ff5500; color: white; width: 50px; height: 50px; border-radius: 50%; border: none; font-size: 24px; cursor: pointer; margin-left: 10px; vertical-align: middle; box-shadow: 0 2px 5px rgba(0,0,0,0.2); }
    .content-box { background: white; margin: 15px auto; padding: 20px; border-radius: 15px; width: 90%; text-align: left; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
    input { padding: 12px; border-radius: 10px; border: 1px solid #ddd; width: 70%; margin-bottom: 10px; font-size: 16px; vertical-align: middle; }
</style>
'''

# --- 4. लॉगिन/डैशबोर्ड ---
@app.route('/')
def login_page():
    if 'user' in session: return redirect('/dashboard')
    return UI_STYLE + '<div style="padding-top:80px;"><h2>🇮🇳 MGIC NCC पोर्टल</h2><form action="/login" method="post"><input name="id" placeholder="Reg No" required><br><input name="pw" type="password" placeholder="Password" required><br><button type="submit" class="btn">लॉगिन करें</button></form></div>'

@app.route('/login', methods=['POST'])
def login():
    u_id, u_pw = request.form.get('id').strip(), request.form.get('pw').strip()
    try:
        records = get_sheet("Cadet_Master").get_all_records()
        for row in records:
            if str(row.get('Reg_No')) == u_id and str(row.get('Password')) == u_pw:
                session['user'] = row.get('Name')
                session['reg_no'] = u_id
                session['rank'] = row.get('Rank', 'Cadet')
                log_usage(u_id, "Login Success")
                return redirect('/dashboard')
        return "विवरण गलत है! <a href='/'>Retry</a>"
    except Exception as e: return f"Error: {str(e)}"

@app.route('/dashboard')
def dashboard():
    if 'user' not in session: return redirect('/')
    try:
        settings = get_sheet("Admin_Settings").get_all_records()
        notice = next((item['Value'] for item in settings if item['Feature'] == 'Notice'), "जय हिंद!")
    except: notice = "सूचना उपलब्ध नहीं है।"

    return UI_STYLE + f'''
    <div class="header"><span>जय हिंद, {session['rank']} {session['user']}!</span><a href="/logout" style="color:white; text-decoration:none;">Logout</a></div>
    <div class="notice-bar"><div class="notice-text">{notice}</div></div>
    <div style="padding-top:10px;">
        <div class="main-card" onclick="window.location.href='/subjects_list'"><h2>📘 ट्रेनिंग लाइब्रेरी</h2><p>वीडियो और नोट्स देखें</p></div>
        <div class="main-card" onclick="window.location.href='/quiz_main'"><h2>📝 प्रैक्टिस टेस्ट</h2><p>स्कोर चेक करें</p></div>
        <div class="main-card" onclick="window.location.href='/ai'" style="border-left-color: #ff5500;"><h2>🤖 एआई सूबेदार</h2><p>बोलकर या लिखकर पूछें</p></div>
    </div>
    '''

# --- 5. एआई सूबेदार (Fixed Path & Brackets) ---
@app.route('/ai', methods=['GET', 'POST'])
def ai():
    if 'user' not in session: return redirect('/')
    ans = ""
    if request.method == 'POST':
        user_q = request.form.get('q')
        try:
            genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))
            model = genai.GenerativeModel('models/gemini-1.5-flash')
            res = model.generate_content(f"आप MGIC NCC के सूबेदार मेजर हैं। कैडेट {session['user']} का सवाल: {user_q}")
            ans = res.text
            log_usage(session['reg_no'], "AI Query", user_q)
        except Exception as e: ans = f"त्रुटि: {str(e)}"

    return UI_STYLE + f'''
    <div class="header"><h2>एआई सूबेदार</h2><a href="/dashboard" style="color:white;">Back</a></div>
    <div class="content-box">
        <form method="post">
            <input name="q" id="qInput" placeholder="पूछें, कैडेट..." required autofocus>
            <button type="button" class="mic-btn" onclick="startDictation()">🎤</button>
            <br><br><button type="submit" class="btn">Ask</button>
        </form>
        <div style="margin-top:20px; border-left:4px solid #ff5500; padding:10px; background:#fffcf5;">
            <strong>जवाब:</strong><p style="white-space: pre-wrap;">{ans}</p>
        </div>
    </div>
    <script>
        function startDictation() {{
            if (window.hasOwnProperty('webkitSpeechRecognition')) {{
                var recognition = new webkitSpeechRecognition();
                recognition.lang = "hi-IN";
                recognition.onresult = function(e) {{
                    document.getElementById('qInput').value = e.results[0][0].transcript;
                }};
                recognition.start();
            }} else {{ alert("Voice not supported."); }}
        }}
    </script>
    '''

@app.route('/subjects_list')
def subjects_list():
    if 'user' not in session: return redirect('/')
    lib = get_sheet("Content_Library").get_all_records()
    topics = sorted(list(set([row.get('Topic_Name') for row in lib if row.get('Topic_Name')])))
    html = '<div class="header"><h2>विषय सूची</h2><a href="/dashboard" style="color:white;">Back</a></div>'
    for t in topics: html += f'<div class="main-card" onclick="window.location.href=\'/view_subject/{t}\'"><h3>{t}</h3></div>'
    return UI_STYLE + html

@app.route('/view_subject/<name>')
def view_subject(name):
    if 'user' not in session: return redirect('/')
    lib = get_sheet("Content_Library").get_all_records()
    html = f'<div class="header"><h2>{name}</h2><a href="/subjects_list" style="color:white;">Back</a></div>'
    for v in lib:
        if v.get('Topic_Name') == name:
            v_id = v.get('Link', '').split("v=")[-1] if "v=" in v.get('Link','') else v.get('Link','').split("/")[-1]
            html += f'<div class="content-box"><p>{v.get("Description","")}</p><iframe width="100%" height="220" src="https://www.youtube.com/embed/{v_id}" frameborder="0" allowfullscreen style="border-radius:10px;"></iframe></div>'
    return UI_STYLE + html

@app.route('/quiz_main')
def quiz_main():
    if 'user' not in session: return redirect('/')
    questions = get_sheet("Quiz_Data").get_all_records()
    html = f'<div class="header"><h2>NCC क्विज</h2><a href="/dashboard" style="color:white;">Back</a></div>'
    for i, q in enumerate(questions[:10]):
        html += f'<div class="content-box"><p><strong>{i+1}. {q.get("Question")}</strong></p><input type="radio"> {q.get("Option_A")}<br><input type="radio"> {q.get("Option_B")}<br><input type="radio"> {q.get("Option_C")}<br><input type="radio"> {q.get("Option_D")}</div>'
    return UI_STYLE + html + '<div style="padding:20px;"><button class="btn" onclick="alert(\'Score Saved!\')">Submit</button></div>'

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
