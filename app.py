import os
import json
from flask import Flask, render_template, request, redirect, url_for, session
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai
from datetime import datetime

app = Flask(__name__)
app.secret_key = "MGIC_NCC_2026_V4_LIBRARIAN"

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

# --- 2. स्मार्ट लॉगर ---
def log_usage(reg_no, action, query="-"):
    try:
        sheet = get_sheet("Usage_Logs")
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([now, reg_no, action, query])
    except: pass

# --- 3. डिजाइन (iPhone 11 Optimized) ---
UI_STYLE = '''
<style>
    body { font-family: 'Segoe UI', sans-serif; background: #f4f7f6; margin: 0; padding-bottom: 50px; text-align: center; color: #333; }
    .header { background: linear-gradient(135deg, #003366, #00509d); color: white; padding: 15px; display: flex; justify-content: space-between; align-items: center; position: sticky; top: 0; z-index: 1000; box-shadow: 0 2px 8px rgba(0,0,0,0.2); }
    .notice-bar { background: #ffcc00; color: #000; padding: 10px; font-weight: bold; font-size: 13px; overflow: hidden; white-space: nowrap; }
    .notice-text { display: inline-block; animation: marquee 15s linear infinite; }
    @keyframes marquee { 0% { transform: translateX(100%); } 100% { transform: translateX(-100%); } }
    .main-card { background: white; padding: 20px; margin: 15px auto; border-radius: 15px; box-shadow: 0 3px 10px rgba(0,0,0,0.1); width: 88%; max-width: 400px; border-left: 6px solid #003366; text-align: left; transition: 0.2s; cursor: pointer; }
    .main-card:active { transform: scale(0.98); }
    .btn { background: #003366; color: white; padding: 12px 20px; border-radius: 8px; text-decoration: none; font-weight: bold; border: none; cursor: pointer; }
    .book-btn { background: #28a745; color: white; padding: 10px 15px; border-radius: 8px; text-decoration: none; font-size: 14px; display: inline-block; margin-top: 10px; font-weight: bold; }
    .mic-btn { background: #ff5500; color: white; width: 45px; height: 45px; border-radius: 50%; border: none; font-size: 20px; vertical-align: middle; margin-left: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.2); }
    .content-box { background: white; margin: 15px auto; padding: 15px; border-radius: 12px; width: 90%; text-align: left; box-shadow: 0 2px 5px rgba(0,0,0,0.05); border-top: 4px solid #ff5500; }
    input { padding: 12px; border-radius: 8px; border: 1px solid #ddd; width: 65%; font-size: 16px; vertical-align: middle; }
</style>
'''

# --- 4. रूट्स (Login/Dashboard) ---
@app.route('/')
def login_page():
    if 'user' in session: return redirect('/dashboard')
    return UI_STYLE + '<div style="padding-top:100px;"><h2>🇮🇳 MGIC NCC पोर्टल</h2><form action="/login" method="post"><input name="id" placeholder="Reg No" required><br><br><input name="pw" type="password" placeholder="Password" required><br><br><button type="submit" class="btn">लॉगिन करें</button></form></div>'

@app.route('/login', methods=['POST'])
def login():
    u_id, u_pw = request.form.get('id', '').strip(), request.form.get('pw', '').strip()
    try:
        records = get_sheet("Cadet_Master").get_all_records()
        for row in records:
            if str(row.get('Reg_No')) == u_id and str(row.get('Password')) == u_pw:
                session.update({'user': row.get('Name'), 'reg_no': u_id, 'rank': row.get('Rank', 'Cadet')})
                log_usage(u_id, "Login Success")
                return redirect('/dashboard')
        return "गलत पासवर्ड! <a href='/'>Retry</a>"
    except Exception as e: return f"Error: {str(e)}"

@app.route('/dashboard')
def dashboard():
    if 'user' not in session: return redirect('/')
    try:
        notice = next((i['Value'] for i in get_sheet("Admin_Settings").get_all_records() if i['Feature'] == 'Notice'), "जय हिंद!")
    except: notice = "सूचना उपलब्ध नहीं है।"
    return UI_STYLE + f'''
    <div class="header"><span>जय हिंद, {session['rank']} {session['user']}</span><a href="/logout" style="color:white; font-size:12px;">Logout</a></div>
    <div class="notice-bar"><div class="notice-text">{notice}</div></div>
    <div style="padding-top:10px;">
        <div class="main-card" onclick="location.href='/subjects_list'"><h2>📘 ट्रेनिंग लाइब्रेरी</h2><p>वीडियो और नोट्स देखें</p></div>
        <div class="main-card" onclick="location.href='/ai'" style="border-left-color:#ff5500;"><h2>🤖 एआई सूबेदार</h2><p>कुछ भी सर्च करें (Multi-Lang)</p></div>
        <div class="main-card" onclick="location.href='/quiz_main'"><h2>📝 प्रैक्टिस टेस्ट</h2><p>मॉक टेस्ट दें</p></div>
    </div>
    '''

# --- 5. एआई सूबेदार (The Smart Librarian) ---
@app.route('/ai', methods=['GET', 'POST'])
def ai():
    if 'user' not in session: return redirect('/')
    results = []
    user_q = ""
    if request.method == 'POST':
        user_q = request.form.get('q', '')
        try:
            genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))
            model = genai.GenerativeModel('models/gemini-1.5-flash')
            
            # लाइब्रेरी का डेटा लाना
            library_data = get_sheet("Content_Library").get_all_records()
            all_topics = ", ".join([row['Topic_Name'] for row in library_data])
            
            # AI सिर्फ टॉपिक मैच करेगा
            prompt = f"कैडेट का सवाल: '{user_q}'. इन उपलब्ध टॉपिक्स में से सबसे सही मैच चुनें: {all_topics}. सिर्फ टॉपिक का नाम लिखें।"
            matched_topic = model.generate_content(prompt).text.strip()
            
            # मैच होने वाले डेटा को निकालना
            for row in library_data:
                if matched_topic.lower() in row['Topic_Name'].lower() or user_q.lower() in row['Topic_Name'].lower():
                    results.append(row)
            
            log_usage(session['reg_no'], "AI Search", user_q)
        except Exception as e:
            print(f"AI Error: {e}")

    res_html = ""
    for r in results:
        v_link = r.get('Link', '')
        v_id = v_link.split("v=")[-1] if "v=" in v_link else v_link.split("/")[-1]
        b_link = r.get('Book_Link', '')
        book_btn = f'<a href="{b_link}" class="book-btn" target="_blank">📘 Read Handbook</a>' if b_link else ""
        
        res_html += f'''
        <div class="content-box">
            <h3>{r.get('Topic_Name')}</h3>
            <p>{r.get('Description','')}</p>
            <iframe width="100%" height="200" src="https://www.youtube.com/embed/{v_id}" frameborder="0" style="border-radius:10px;"></iframe>
            <div style="margin-top:10px;">{book_btn}</div>
        </div>
        '''

    return UI_STYLE + f'''
    <div class="header"><h2>एआई सूबेदार</h2><a href="/dashboard" style="color:white;">Back</a></div>
    <div style="padding:15px;">
        <form method="post" id="searchForm">
            <input name="q" id="qInput" placeholder="टॉपिक बोलें या लिखें..." value="{user_q}" required>
            <button type="button" class="mic-btn" onclick="startDictation()">🎤</button>
            <br><br><button type="submit" class="btn">खोजें (Search)</button>
        </form>
        <div id="resultsArea">{res_html if results else '<p style="color:gray; margin-top:20px;">कैडेट, अपना सवाल ऊपर टाइप करें।</p>' if user_q else ""}</div>
    </div>
    <script>
        function startDictation() {{
            if (window.hasOwnProperty('webkitSpeechRecognition')) {{
                var recognition = new webkitSpeechRecognition();
                recognition.lang = "hi-IN";
                recognition.onresult = function(e) {{ 
                    document.getElementById('qInput').value = e.results[0][0].transcript;
                    document.getElementById('searchForm').submit();
                }};
                recognition.start();
            }} else {{ alert("Mic not supported"); }}
        }}
    </script>
    '''

@app.route('/subjects_list')
def subjects_list():
    if 'user' not in session: return redirect('/')
    lib = get_sheet("Content_Library").get_all_records()
    topics = sorted(list(set([row.get('Topic_Name') for row in lib if row.get('Topic_Name')])))
    html = '<div class="header"><h2>विषय सूची</h2><a href="/dashboard" style="color:white;">Back</a></div>'
    for t in topics: html += f'<div class="main-card" onclick="location.href=\'/view_subject/{t}\'"><h3>{t}</h3></div>'
    return UI_STYLE + html

@app.route('/view_subject/<name>')
def view_subject(name):
    if 'user' not in session: return redirect('/')
    lib = get_sheet("Content_Library").get_all_records()
    html = f'<div class="header"><h2>{name}</h2><a href="/subjects_list" style="color:white;">Back</a></div>'
    for v in lib:
        if v.get('Topic_Name') == name:
            v_link = v.get('Link','')
            v_id = v_link.split("v=")[-1] if "v=" in v_link else v_link.split("/")[-1]
            b_link = v.get('Book_Link', '')
            book_btn = f'<a href="{b_link}" class="book-btn" target="_blank">📘 Read Handbook</a>' if b_link else ""
            html += f'<div class="content-box"><p>{v.get("Description","")}</p><iframe width="100%" height="220" src="https://www.youtube.com/embed/{v_id}" frameborder="0" allowfullscreen style="border-radius:10px;"></iframe>{book_btn}</div>'
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
