import os
import json
from flask import Flask, render_template, request, redirect, url_for, session
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai

app = Flask(__name__)
app.secret_key = "MGIC_NCC_2026_ULTIMATE_FINAL_VERSION"

# --- 1. रेंडर की तिजोरी से चाबियाँ उठाना (The Authentication) ---
def get_sheet(sheet_name):
    # रेंडर से गूगल शीट की चाबी उठाना
    json_key = os.environ.get('SERVICE_ACCOUNT_JSON')
    if not json_key:
        raise ValueError("SERVICE_ACCOUNT_JSON missing in Render!")
    
    creds_dict = json.loads(json_key)
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    # आपकी शीट का नाम (URL से पहचाना गया)
    return client.open("NCC_Smart_Portal_Data").worksheet(sheet_name)

# --- 2. प्रोफेशनल डिजाइन (UI/CSS) ---
UI_STYLE = '''
<style>
    body { font-family: 'Segoe UI', sans-serif; background: #f0f2f5; margin: 0; text-align: center; color: #333; }
    .header { background: linear-gradient(135deg, #003366, #00509d); color: white; padding: 15px 25px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 10px rgba(0,0,0,0.2); }
    .main-card { background: white; padding: 25px; margin: 20px auto; border-radius: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); width: 85%; max-width: 400px; border-bottom: 6px solid #003366; transition: 0.3s; }
    .main-card:hover { transform: translateY(-5px); }
    .btn { background: #003366; color: white; padding: 12px 25px; border-radius: 10px; text-decoration: none; display: inline-block; font-weight: bold; border: none; cursor: pointer; }
    .content-box { background: white; margin: 15px auto; padding: 20px; border-radius: 15px; width: 90%; text-align: left; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
    input { padding: 12px; border-radius: 8px; border: 1px solid #ccc; width: 80%; margin-bottom: 10px; }
</style>
'''

# --- 3. लॉगिन का रास्ता ---
@app.route('/')
def login_page():
    if 'user' in session: return redirect('/dashboard')
    return UI_STYLE + '<div style="padding-top:100px;"><h2>MGIC NCC पोर्टल</h2><form action="/login" method="post"><input name="id" placeholder="Reg No" required><br><input name="pw" type="password" placeholder="Password" required><br><button type="submit" class="btn">लॉगिन</button></form></div>'

@app.route('/login', methods=['POST'])
def login():
    u_id, u_pw = request.form.get('id').strip(), request.form.get('pw').strip()
    try:
        records = get_sheet("Cadet_Master").get_all_records()
        for row in records:
            if str(row.get('Reg_No')) == u_id and str(row.get('Password')) == u_pw:
                session['user'] = row.get('Name')
                return redirect('/dashboard')
        return "गलत आईडी/पासवर्ड! <a href='/'>Retry</a>"
    except Exception as e: return f"कनेक्शन एरर: {str(e)}"

# --- 4. डैशबोर्ड (सिर्फ 3 मुख्य बटन) ---
@app.route('/dashboard')
def dashboard():
    if 'user' not in session: return redirect('/')
    return UI_STYLE + f'''
    <div class="header"><span>जय हिंद, {session['user']}!</span><a href="/logout" style="color:white; text-decoration:none; font-weight:bold;">Log Out</a></div>
    <div style="padding-top:20px;">
        <div class="main-card" onclick="window.location.href='/subjects_list'"><h2>📘 विषय (Subjects)</h2><p>वीडियो और नोट्स देखें</p></div>
        <div class="main-card" onclick="window.location.href='/quiz_main'"><h2>📝 क्विज (Quiz)</h2><p>प्रैक्टिस टेस्ट दें</p></div>
        <div class="main-card" onclick="window.location.href='/ai'"><h2>🤖 एआई सूबेदार</h2><p>सवाल पूछें</p></div>
    </div>
    '''

# --- 5. विषयों की लिस्ट और कंटेंट ---
@app.route('/subjects_list')
def subjects_list():
    if 'user' not in session: return redirect('/')
    lib = get_sheet("Content_Library").get_all_records()
    topics = sorted(list(set([row['Topic_Name'] for row in lib])))
    html = '<div class="header"><h2>सभी विषय</h2><a href="/dashboard" style="color:white;">Back</a></div>'
    for t in topics:
        html += f'<div class="main-card" onclick="window.location.href=\'/view_subject/{t}\'"><h3>{t}</h3></div>'
    return UI_STYLE + html

@app.route('/view_subject/<name>')
def view_subject(name):
    if 'user' not in session: return redirect('/')
    lib = get_sheet("Content_Library").get_all_records()
    content_html = f'<div class="header"><h2>{name}</h2><a href="/subjects_list" style="color:white;">Back</a></div>'
    for v in lib:
        if v['Topic_Name'] == name:
            v_id = v['Link'].split("v=")[-1] if "v=" in v['Link'] else v['Link'].split("/")[-1]
            content_html += f'''
            <div class="content-box">
                <p style="font-size:17px; line-height:1.6;">{v.get('Description', 'कोई नोट्स उपलब्ध नहीं हैं।')}</p>
                <iframe width="100%" height="230" src="https://www.youtube.com/embed/{v_id}" frameborder="0" allowfullscreen style="border-radius:12px; margin-top:10px;"></iframe>
            </div>
            '''
    return UI_STYLE + content_html

# --- 6. क्विज सेक्शन (आपकी शीट के हिसाब से) ---
@app.route('/quiz_main')
def quiz_main():
    if 'user' not in session: return redirect('/')
    questions = get_sheet("Quiz_Data").get_all_records()
    q_html = f'<div class="header"><h2>प्रैक्टिस क्विज</h2><a href="/dashboard" style="color:white;">Back</a></div>'
    for i, q in enumerate(questions):
        q_html += f'''
        <div class="content-box">
            <p><strong>Q{i+1}: {q["Question"]}</strong></p>
            <label><input type="radio" name="q{i}"> {q["Option_A"]}</label><br>
            <label><input type="radio" name="q{i}"> {q["Option_B"]}</label><br>
            <label><input type="radio" name="q{i}"> {q["Option_C"]}</label><br>
            <label><input type="radio" name="q{i}"> {q["Option_D"]}</label>
        </div>
        '''
    q_html += '<button class="btn" style="margin:20px;" onclick="alert(\'स्कोर सबमिट हो गया!\')">सबमिट करें</button><br><br>'
    return UI_STYLE + q_html

# --- 7. एआई सूबेदार (Gemini Integration) ---
@app.route('/ai', methods=['GET', 'POST'])
def ai():
    if 'user' not in session: return redirect('/')
    ans = ""
    if request.method == 'POST':
        api_key = os.environ.get('GEMINI_API_KEY')
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"आप MGIC NCC के एक सीनियर सूबेदार मेजर हैं। कैडेट्स को अनुशासित लहजे में हिंदी में जवाब दें: {request.form.get('q')}"
        try:
            res = model.generate_content(prompt)
            ans = res.text
        except: ans = "सिग्नल में बाधा है, फिर से पूछें।"
    return UI_STYLE + f'''
    <div class="header"><h2>एआई सूबेदार</h2><a href="/dashboard" style="color:white;">Back</a></div>
    <div class="content-box">
        <form method="post">
            <input name="q" placeholder="पूछें, कैडेट..." required style="width:70%;">
            <button type="submit" class="btn">Ask</button>
        </form>
        <div style="margin-top:20px; border-left:5px solid #003366; padding-left:15px; color:#444;">
            <strong>जवाब:</strong><p>{ans}</p>
        </div>
    </div>
    '''

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
