import google.generativeai as genai
from flask import Flask, render_template, request, redirect, session, jsonify
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os

app = Flask(__name__)
app.secret_key = "MGIC_NCC_2026_ULTIMATE_FINAL"

# --- 1. जेमिनी (Gemini AI) सेटअप ---
genai.configure(api_key="AIzaSyAzeeXAr3RCQ5QNKlzPztcjcvQvgkwGLGY")
model = genai.GenerativeModel('gemini-1.5-flash')

# --- 2. Google Sheet 'पक्का' कनेक्शन (Updated with Latest Credentials) ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
# आपकी लेटेस्ट फाइल का नाम यहाँ सेट कर दिया है
json_file = "mgic-ncc-portal-293fd396bb7b.json"

try:
    base_path = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(base_path, json_file)
    
    # कनेक्शन क्रेडेंशियल्स
    creds = ServiceAccountCredentials.from_json_keyfile_name(json_path, scope)
    client_sheet = gspread.authorize(creds)
    spreadsheet = client_sheet.open("NCC_Smart_Portal_Data")
    print("✅ जय हिंद! MGIC NCC बैकएंड अब पूरी तरह से जुड़ चुका है।")
except Exception as e:
    print(f"❌ कनेक्शन एरर: {e}")
    print("सुझाव: पक्का करें कि फाइल का नाम फोल्डर में 'mgic-ncc-portal-293fd396bb7b.json' ही है।")

# --- 3. यूआई (UI) और डिजाइन फंक्शन ---
def get_header(title):
    return f'''
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; background: #f0f2f5; margin: 0; padding-bottom: 60px; }}
        .header {{ background: linear-gradient(135deg, #1a5276 0%, #002147 100%); color: white; padding: 25px; text-align: center; border-bottom: 6px solid #d9534f; box-shadow: 0 4px 12px rgba(0,0,0,0.2); }}
        .card {{ background: white; border-radius: 15px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); padding: 20px; margin: 20px auto; max-width: 800px; border-left: 8px solid #1a5276; }}
        .btn {{ background: #1a5276; color: white; border: none; padding: 12px 22px; border-radius: 8px; cursor: pointer; font-weight: bold; text-decoration: none; display: inline-block; transition: 0.3s; }}
        .btn:hover {{ background: #d9534f; transform: scale(1.05); }}
    </style>
    <div class="header">
        <h1 style="margin:0;">{title}</h1>
        <p style="margin:5px 0 0 0;"><b>CTO कृष्णा पाल सिंह • MGIC</b></p>
    </div>
    <script>
        function speak(text) {{
            window.speechSynthesis.cancel();
            let speech = new SpeechSynthesisUtterance(text.replace(/<[^>]*>?/gm,""));
            speech.lang = 'hi-IN';
            window.speechSynthesis.speak(speech);
        }}
    </script>
    '''

@app.route('/')
def login_page():
    return '''<body style="background:#002147;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;">
    <div style="background:white;padding:40px;border-radius:25px;text-align:center;width:320px;box-shadow: 0 15px 40px rgba(0,0,0,0.5);">
        <img src="https://www.indiancc.nic.in/wp-content/themes/ncc/images/logo.png" width="90">
        <h2 style="color: #1a5276;">MGIC NCC लॉगिन</h2>
        <form action="/login" method="post">
            <input type="text" name="reg_no" placeholder="रेजिमेंटल नंबर" required style="width:100%; padding:14px; margin:10px 0; border:1px solid #ddd; border-radius:10px;">
            <input type="password" name="pass" placeholder="पासवर्ड" required style="width:100%; padding:14px; margin:10px 0; border:1px solid #ddd; border-radius:10px;">
            <button type="submit" class="btn" style="width:100%; margin-top:10px;">प्रवेश करें</button>
        </form>
    </div></body>'''

@app.route('/login', methods=['POST'])
def login_logic():
    reg_no = str(request.form.get('reg_no')).strip()
    password = str(request.form.get('pass')).strip()
    try:
        master = spreadsheet.worksheet("Cadet_Master").get_all_records()
        for c in master:
            s_reg = str(c.get('Regimental_No', '')).strip()
            s_pass = str(c.get('Password', '')).strip()
            if s_reg == reg_no and s_pass == password:
                session['user'], session['rank'] = c.get('Cadet_Name'), c.get('Rank')
                return redirect('/dashboard')
    except: pass
    return "<h1>विवरण सही नहीं हैं! <a href='/'>Retry</a></h1>"

@app.route('/dashboard')
def dashboard():
    if 'user' not in session: return redirect('/')
    res = f'<body style="margin:0;">{get_header("स्वागत है, " + session["rank"] + " " + session["user"])}'
    res += '<div style="max-width:850px;margin:40px auto;display:grid;grid-template-columns: 1fr 1fr;gap:25px;padding:20px;">'
    res += '<a href="/subjects" style="text-decoration:none;"><div class="card" style="text-align:center; border-top:6px solid #ff9933;"><h2>📚 स्मार्ट नोट्स</h2></div></a>'
    res += '<a href="/practice_test" style="text-decoration:none;"><div class="card" style="text-align:center; border-top:6px solid #138808;"><h2>🎯 प्रैक्टिस टेस्ट</h2></div></a>'
    res += '</div><div id="chat-circle" onclick="document.getElementById(\'chat-box\').style.display=\'block\'" style="position:fixed;bottom:30px;right:30px;background:#1a5276;color:white;width:70px;height:70px;border-radius:50%;display:flex;align-items:center;justify-content:center;cursor:pointer;font-size:35px;box-shadow:0 10px 30px rgba(0,0,0,0.3);">🤖</div>'
    res += '<div id="chat-box" style="display:none;position:fixed;bottom:110px;right:30px;width:340px;height:480px;background:white;border-radius:20px;box-shadow:0 10px 40px rgba(0,0,0,0.2);overflow:hidden;z-index:1000;"><div style="background:#1a5276;color:white;padding:20px;font-weight:bold;">AI सूबेदार</div><div id="chat-content" style="padding:15px;height:330px;overflow-y:auto;background:#fafafa;"></div><div style="padding:10px;display:flex;gap:10px;border-top:1px solid #eee;"><input type="text" id="chat-input" placeholder="पूछें..." style="flex:1;padding:12px;border:1px solid #ddd;border-radius:10px;"><button onclick="askAI()" class="btn">Ask</button></div></div>'
    res += '<script>function askAI(){let i=document.getElementById("chat-input").value;let c=document.getElementById("chat-content");if(!i)return;c.innerHTML+="<p style=\'text-align:right;background:#dcf8c6;padding:12px;border-radius:15px;margin-left:20%;\'>"+i+"</p>";document.getElementById("chat-input").value="";fetch("/ask_smart",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({query:i})}).then(r=>r.json()).then(d=>{c.innerHTML+="<div onclick=\'speak(this.innerText)\' style=\'background:white;border:1px solid #eee;padding:12px;border-radius:15px;margin-bottom:10px;cursor:pointer;\'>🔊 "+d.response+"</div>";c.scrollTop=c.scrollHeight;});}</script></body>'
    return res

@app.route('/subjects')
def subjects():
    all_data = spreadsheet.worksheet("Content_Library").get_all_records()
    subs = sorted(list(set([r['Subject'] for r in all_data if r['Subject']])))
    html = get_header("विषय सूची") + '<div style="max-width:700px; margin:auto; padding:20px;"><a href="/dashboard" class="btn">⬅ वापस</a><br><br>'
    for s in subs: html += f'<a href="/topics/{s}" style="text-decoration:none;"><div class="card"><h3>{s} ⮕</h3></div></a>'
    return html + '</div>'

@app.route('/topics/<sub_name>')
def topics(sub_name):
    all_data = spreadsheet.worksheet("Content_Library").get_all_records()
    filtered = [r for r in all_data if r['Subject'] == sub_name]
    html = get_header(sub_name) + '<div style="padding:20px; max-width:800px; margin:auto;"><a href="/subjects" class="btn">⬅ वापस</a><br><br>'
    for t in filtered:
        img = f'<img src="{t.get("Photo_URL")}" style="width:100%;border-radius:15px;margin-bottom:15px;">' if t.get('Photo_URL') else ""
        html += f'<div class="card"><h2>{t["Topic"]}</h2>{img}<p style="white-space:pre-wrap; font-size:16px;">{str(t["Topic_Details"])}</p><button onclick="speak(`{str(t["Topic_Details"]).replace("`","")}`)" class="btn">🔊 सुनाओ</button><a href="{t["Video_Link"]}" target="_blank" class="btn" style="background:#d9534f;margin-left:10px;">▶ वीडियो</a></div>'
    return html + '</div>'

@app.route('/practice_test')
def practice_test():
    q_data = spreadsheet.worksheet("Quiz_Data").get_all_records()
    html = get_header("प्रैक्टिस टेस्ट") + '<div style="max-width:750px; margin:auto; padding:20px;"><a href="/dashboard" class="btn">⬅ वापस</a><br><br>'
    for i, q in enumerate(q_data):
        opts = q['Options'].split(',')
        opt_html = "".join([f'<div style="margin:10px 0;"><input type="radio" name="q{i}" value="{o.strip()}"> {o.strip()}</div>' for o in opts])
        html += f'<div class="card" style="border-left:8px solid #138808;"><b>Q{i+1}: {q["Question"]}</b><br><br>{opt_html}<br><button onclick="checkAns(\'q{i}\', \'{q["Correct_Answer"]}\')" class="btn">चेक करें</button><span id="res_q{i}" style="margin-left:15px; font-weight:bold;"></span></div>'
    html += '<script>function checkAns(n,c){let s=document.querySelector(`input[name="${n}"]:checked`);let r=document.getElementById("res_"+n);if(!s)return alert("Select!");if(s.value.trim()===c.trim()){r.innerHTML="✅ सही!";r.style.color="green";speak("सही जवाब");}else{r.innerHTML="❌ गलत!";r.style.color="red";speak("गलत जवाब");}}</script>'
    return html + '</div>'

@app.route('/ask_smart', methods=['POST'])
def ask_smart():
    q = request.json.get('query', '').lower()
    try:
        content = spreadsheet.worksheet("Content_Library").get_all_records()
        for row in content:
            if q in str(row['Topic']).lower(): return jsonify({"response": str(row.get('Topic_Details'))})
        res = model.generate_content("Answer in Hindi: " + q)
        return jsonify({"response": res.text})
    except: return jsonify({"response": "नेटवर्क धीमा है, कृपया दोबारा प्रयास करें।"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)