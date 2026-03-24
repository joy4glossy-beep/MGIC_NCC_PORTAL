import os
import json
import base64
import requests
import re
from flask import Flask, render_template, request, redirect, url_for, session
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

app = Flask(__name__)
app.secret_key = "MGIC_DALAN_CHHAPRA_FINAL_MASTER_V5"

# --- 1. गूगल शीट और इमेज इंजन ---
def get_sheet(sheet_name):
    json_key = os.environ.get('SERVICE_ACCOUNT_JSON')
    creds_dict = json.loads(json_key)
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client.open("NCC_Smart_Portal_Data").worksheet(sheet_name)

def get_b64_from_drive(drive_link):
    """ड्राइव लिंक से इमेज फेच करने का सबसे सटीक तरीका"""
    if not drive_link or "http" not in drive_link: return ""
    try:
        file_id = ""
        id_match = re.search(r'id=([a-zA-Z0-9_-]+)', drive_link)
        if id_match: file_id = id_match.group(1)
        else:
            d_match = re.search(r'/d/([a-zA-Z0-9_-]+)', drive_link)
            if d_match: file_id = d_match.group(1)
        
        if file_id:
            direct_url = f'https://drive.google.com/uc?export=download&id={file_id}'
            response = requests.get(direct_url, timeout=10)
            if response.status_code == 200:
                return base64.b64encode(response.content).decode('utf-8')
    except: pass
    return ""

def get_global_assets():
    """लोगो और बैकग्राउंड को एक साथ फेच करना"""
    try:
        data = get_sheet("App_Assets").get_all_records()
        logo_link = next((r['Asset_Link'] for r in data if r['Asset_Name'] == 'NCC_Logo'), "")
        bg_link = next((r['Asset_Link'] for r in data if r['Asset_Name'] == 'Portal_BG'), "")
        return get_b64_from_drive(logo_link), get_b64_from_drive(bg_link)
    except: return "", ""

# --- 2. मास्टर UI स्टाइल (Glassmorphism & Fixed BG) ---
def get_ui_style(bg_b64="", title="MGIC NCC"):
    bg_css = f"background-image: url('data:image/png;base64,{bg_b64}');" if bg_b64 else "background: #003366;"
    return f'''
    <head>
        <title>{title}</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    </head>
    <style>
        body {{ 
            font-family: 'Segoe UI', sans-serif; margin: 0; padding-bottom: 90px; text-align: center; color: #333;
            {bg_css} background-size: cover; background-attachment: fixed; background-position: center;
        }}
        .header {{ 
            background: rgba(0, 51, 102, 0.95); color: white; padding: 15px; display: flex; align-items: center; 
            position: sticky; top: 0; z-index: 1000; backdrop-filter: blur(10px); border-bottom: 2px solid #ffcc00;
        }}
        .header-text {{ text-align: left; margin-left: 10px; flex-grow: 1; }}
        .header-text b {{ font-size: 16px; display: block; color: #ffcc00; }}
        .header-text span {{ font-size: 13px; opacity: 0.9; }}
        
        .main-card {{ 
            background: rgba(255, 255, 255, 0.88); padding: 22px; margin: 15px auto; border-radius: 20px; 
            box-shadow: 0 8px 32px rgba(0,0,0,0.2); width: 88%; max-width: 420px; backdrop-filter: blur(8px);
            border: 1px solid rgba(255,255,255,0.4); text-align: left; cursor: pointer;
        }}
        .main-card h2 {{ margin: 0; font-size: 21px; color: #003366; }}
        .main-card p {{ margin: 5px 0 0; color: #555; font-size: 15px; }}
        
        .btn {{ background: #003366; color: white; padding: 12px 20px; border-radius: 10px; font-weight: bold; border: none; cursor: pointer; font-size: 16px; width: 100%; }}
        .notice-bar {{ background: rgba(255, 204, 0, 0.95); color: #000; padding: 10px; font-weight: bold; font-size: 14px; overflow: hidden; white-space: nowrap; }}
        .notice-text {{ display: inline-block; animation: marquee 15s linear infinite; }}
        @keyframes marquee {{ 0% {{ transform: translateX(100%); }} 100% {{ transform: translateX(-100%); }} }}
        .footer {{ position: fixed; bottom: 0; width: 100%; background: white; padding: 14px 0; font-size: 12px; color: #003366; font-weight: bold; border-top: 3px solid #003366; z-index: 1001; }}
        input, textarea {{ padding: 14px; border-radius: 12px; border: 1px solid #ddd; width: 100%; margin-bottom: 12px; font-size: 16px; box-sizing: border-box; }}
        .chat-box {{ background: rgba(255,255,255,0.92); padding: 15px; border-radius: 15px; margin-bottom: 12px; border-left: 6px solid #ffcc00; text-align: left; }}
        .meta {{ font-size: 12px; color: #777; margin-bottom: 5px; }}
    </style>
    '''

FOOTER = '<div class="footer">Developed by: CTO Krishna Pal Singh 🇮🇳</div>'

# --- 3. कोर रूट्स (Login & Dashboard) ---

@app.route('/')
def login_page():
    if 'user' in session: return redirect('/dashboard')
    logo_b64, bg_b64 = get_global_assets()
    return get_ui_style(bg_b64, "Login") + f'''
    <div style="padding-top: 50px;">
        <img src="data:image/png;base64,{logo_b64}" style="width:95px; margin-bottom:12px;">
        <h2 style="color:white; text-shadow: 2px 2px 5px #000; margin:0; font-size:24px;">महात्मा गांधी इंटर कॉलेज</h2>
        <h4 style="color:#ffcc00; margin-top:5px; text-shadow: 1px 1px 3px #000; font-size:18px;">दलन छपरा, बलिया</h4>
        <div class="main-card" style="text-align:center; margin-top:35px;">
            <h3 style="margin-top:0; color:#003366;">🇮🇳 कैडेट लॉगिन</h3>
            <form action="/login" method="post">
                <input name="id" placeholder="Regiment No." required>
                <input name="pw" type="password" placeholder="Password" required>
                <button type="submit" class="btn">प्रवेश करें</button>
            </form>
        </div>
    </div>
    ''' + FOOTER

@app.route('/login', methods=['POST'])
def login():
    u_id, u_pw = request.form.get('id', '').strip(), request.form.get('pw', '').strip()
    try:
        records = get_sheet("Cadet_Master").get_all_records()
        for row in records:
            if str(row.get('Reg_No')) == u_id and str(row.get('Password')) == u_pw:
                session.update({'user': row.get('Name'), 'reg_no': u_id, 'rank': row.get('Rank', 'Cadet')})
                return redirect('/dashboard')
        return "गलत पासवर्ड! <a href='/'>Retry</a>"
    except: return "Login Error!"

@app.route('/dashboard')
def dashboard():
    if 'user' not in session: return redirect('/')
    logo_b64, bg_b64 = get_global_assets()
    return get_ui_style(bg_b64, "Dashboard") + f'''
    <div class="header">
        <img src="data:image/png;base64,{logo_b64}" style="width:42px;">
        <div class="header-text"><b>MGIC दलन छपरा, बलिया</b><span>जय हिंद, {session['rank']} {session['user']}</span></div>
        <a href="/logout" style="color:white; text-decoration:none; font-size:13px; font-weight:bold;">Logout</a>
    </div>
    <div class="notice-bar"><div class="notice-text">जय हिंद कैडेट्स! MGIC NCC दलन छपरा पोर्टल पर आपका स्वागत है। अनुशासन और एकता ही हमारी पहचान है।</div></div>
    <div style="padding: 10px 0;">
        <div class="main-card" onclick="location.href='/subjects_list'" style="border-left: 8px solid #003366;"><h2>📘 ट्रेनिंग लाइब्रेरी</h2><p>वीडियो और नोट्स देखें</p></div>
        <div class="main-card" onclick="location.href='/ai'" style="border-left: 8px solid #ff5500;"><h2>🤖 एआई सूबेदार</h2><p>सटीक जानकारी पाएं</p></div>
        <div class="main-card" onclick="location.href='/chat'" style="border-left: 8px solid #ffcc00;"><h2>💬 कैडेट चर्चा</h2><p>आपस में बातचीत करें</p></div>
        <div class="main-card" onclick="location.href='/quiz'" style="border-left: 8px solid #9c27b0;"><h2>📝 कैडेट क्विज</h2><p>अपनी तैयारी चेक करें</p></div>
        <div class="main-card" onclick="location.href='/store'" style="border-left: 8px solid #28a745;"><h2>🛍️ एनसीसी स्टोर</h2><p>वर्दी और सामान खरीदें</p></div>
    </div>
    ''' + FOOTER

# --- 4. लाइब्रेरी और एआई ---

@app.route('/subjects_list')
def subjects_list():
    if 'user' not in session: return redirect('/')
    logo_b64, bg_b64 = get_global_assets()
    lib = get_sheet("Content_Library").get_all_records()
    topics = sorted(list(set([row.get('Topic_Name') for row in lib if row.get('Topic_Name')])))
    html = "".join([f'<div class="main-card" onclick="location.href=\'/view_subject/{t}\'"><h2>{t}</h2><p>पाठ्यक्रम देखें</p></div>' for t in topics])
    return get_ui_style(bg_b64) + f'<div class="header"><b>विषय सूची</b><a href="/dashboard" style="color:white; text-decoration:none; margin-left:auto;">Back</a></div><div style="padding:10px;">{html}</div>' + FOOTER

@app.route('/view_subject/<name>')
def view_subject(name):
    if 'user' not in session: return redirect('/')
    logo_b64, bg_b64 = get_global_assets()
    lib = get_sheet("Content_Library").get_all_records()
    cards = ""
    for v in lib:
        if v.get('Topic_Name') == name:
            v_id = v.get('Link','').split("v=")[-1] if "v=" in v.get('Link','') else v.get('Link','').split("/")[-1]
            cards += f'''<div class="main-card" style="cursor:default;">
                <h3>{v.get('Description', 'Video Lesson')}</h3>
                <iframe width="100%" height="210" src="https://www.youtube.com/embed/{v_id}" frameborder="0" allowfullscreen style="border-radius:15px; margin:12px 0;"></iframe>
                <a href="{v.get('Book_Link', '#')}" class="btn" style="background:#28a745; display:block; text-align:center; text-decoration:none;">📘 Read Handbook</a>
            </div>'''
    return get_ui_style(bg_b64) + f'<div class="header"><b>{name}</b><a href="/subjects_list" style="color:white; text-decoration:none; margin-left:auto;">Back</a></div><div style="padding:10px;">{cards}</div>' + FOOTER

@app.route('/ai', methods=['GET', 'POST'])
def ai():
    if 'user' not in session: return redirect('/')
    logo_b64, bg_b64 = get_global_assets()
    results, user_q = [], ""
    if request.method == 'POST':
        user_q = request.form.get('q', '').lower().strip()
        for row in get_sheet("Content_Library").get_all_records():
            if user_q in row.get('Topic_Name','').lower() or user_q in row.get('Description','').lower():
                results.append(row)
    res_html = "".join([f'<div class="main-card"><h3>{r.get("Topic_Name")}</h3><p>{r.get("Description")}</p></div>' for r in results])
    return get_ui_style(bg_b64) + f'''
    <div class="header"><b>🤖 एआई सूबेदार</b><a href="/dashboard" style="color:white; text-decoration:none; margin-left:auto;">Back</a></div>
    <div style="padding:20px;">
        <form method="post"><input name="q" placeholder="Weapon, Map आदि खोजें..." required><button type="submit" class="btn">खोजें</button></form>
        {res_html if res_html else "<p style='color:white; margin-top:20px;'>लाइब्रेरी में खोजें...</p>"}
    </div>
    ''' + FOOTER

# --- 5. चैट, स्टोर और क्विज ---

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if 'user' not in session: return redirect('/')
    logo_b64, bg_b64 = get_global_assets()
    sheet = get_sheet("Chat_Messages")
    if request.method == 'POST':
        msg = request.form.get('message', '').strip()
        if msg: sheet.append_row([datetime.now().strftime("%d/%m %I:%M %p"), f"{session['rank']} {session['user']}", session['reg_no'], msg, "0"])
        return redirect('/chat')
    msgs = sheet.get_all_records()
    chat_html = "".join([f'<div class="chat-box"><div class="meta">{m["Timestamp"]} - {m["Name_Rank"]}</div><b>{m["Message"]}</b></div>' for m in msgs[-10:]])
    return get_ui_style(bg_b64) + f'''
    <div class="header"><b>💬 कैडेट चर्चा</b><a href="/dashboard" style="color:white; text-decoration:none; margin-left:auto;">Back</a></div>
    <div style="padding:15px;">
        <form method="post"><textarea name="message" placeholder="नया सवाल पूछें..." style="height:90px;" required></textarea><button type="submit" class="btn">Post Message</button></form>
        <hr style="border:0.5px solid rgba(255,255,255,0.3); margin:20px 0;">{chat_html}
    </div>
    ''' + FOOTER

@app.route('/store')
def store():
    if 'user' not in session: return redirect('/')
    logo_b64, bg_b64 = get_global_assets()
    products = get_sheet("Product_List").get_all_records()
    cards = "".join([f'''<div class="main-card" style="width:44%; display:inline-block; margin:5px; vertical-align:top; text-align:center; padding:10px;">
        <img src="{p.get('Image_Link')}" style="width:100%; height:110px; border-radius:12px; object-fit:cover;">
        <h4 style="font-size:15px; margin:10px 0 5px;">{p.get('Product_Name')}</h4>
        <div style="color:#28a745; font-weight:bold; margin-bottom:8px;">₹{p.get('Price')}</div>
        <button class="btn" onclick="location.href=\'/buy/{p.get('Product_Name')}/{p.get('Price')}\'" style="padding:7px; font-size:13px;">Buy</button>
    </div>''' for p in products])
    return get_ui_style(bg_b64) + f'<div class="header"><b>🛍️ एनसीसी स्टोर</b><a href="/dashboard" style="color:white; text-decoration:none; margin-left:auto;">Back</a></div><div style="padding:10px;">{cards}</div>' + FOOTER

@app.route('/buy/<name>/<price>', methods=['GET', 'POST'])
def buy(name, price):
    if 'user' not in session: return redirect('/')
    logo_b64, bg_b64 = get_global_assets()
    qr_link = next((s['Setting_Value'] for s in get_sheet("Store_Settings").get_all_records() if s['Setting_Name'] == 'Payment_QR'), "")
    qr_b64 = get_b64_from_drive(qr_link)
    if request.method == 'POST':
        tid = request.form.get('tid')
        get_sheet("Store_Orders").append_row([datetime.now().strftime("%d/%m/%Y %H:%M"), session['reg_no'], f"{session['rank']} {session['user']}", name, price, tid])
        return f"✅ ऑर्डर सफल! <a href='/dashboard'>Home</a>"
    return get_ui_style(bg_b64) + f'''
    <div class="header"><b>पेमेंट</b><a href="/store" style="color:white; text-decoration:none; margin-left:auto;">Back</a></div>
    <div class="main-card" style="text-align:center; margin-top:30px;">
        <h3 style="margin-top:0;">{name} - ₹{price}</h3>
        <img src="data:image/png;base64,{qr_b64 if qr_b64 else ''}" style="width:230px; border:6px solid #003366; border-radius:15px;">
        <form method="post" style="margin-top:20px;"><input name="tid" placeholder="Enter UTR / Transaction ID" required><button type="submit" class="btn" style="background:#28a745;">Confirm Order</button></form>
    </div>
    ''' + FOOTER

@app.route('/quiz')
def quiz():
    if 'user' not in session: return redirect('/')
    logo_b64, bg_b64 = get_global_assets()
    q_data = get_sheet("Quiz_Data").get_all_records()
    q_html = "".join([f'<div class="main-card"><h4>{q["Question"]}</h4><p style="font-size:15px;">A) {q["Opt1"]}<br>B) {q["Opt2"]}<br>C) {q["Opt3"]}</p></div>' for q in q_data[:5]])
    return get_ui_style(bg_b64) + f'<div class="header"><b>📝 कैडेट क्विज</b><a href="/dashboard" style="color:white; text-decoration:none; margin-left:auto;">Back</a></div><div style="padding:10px;">{q_html}<button class="btn" style="background:#9c27b0;">Submit Results</button></div>' + FOOTER

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
