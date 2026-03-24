import os
import json
import base64
import requests
from flask import Flask, render_template, request, redirect, url_for, session
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

app = Flask(__name__)
app.secret_key = "MGIC_DALAN_CHHAPRA_FINAL_v5"

# --- 1. गूगल शीट और इमेज इंजन ---
def get_sheet(sheet_name):
    json_key = os.environ.get('SERVICE_ACCOUNT_JSON')
    creds_dict = json.loads(json_key)
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client.open("NCC_Smart_Portal_Data").worksheet(sheet_name)

def get_b64_from_drive(drive_link):
    """ड्राइव लिंक को सीधे Base64 इमेज में बदलने वाला जादुई फंक्शन"""
    if not drive_link or "id=" not in drive_link and "/" not in drive_link: return ""
    try:
        file_id = drive_link.split('id=')[-1] if 'id=' in drive_link else drive_link.split('/')[-2]
        direct_url = f'https://drive.google.com/uc?export=view&id={file_id}'
        response = requests.get(direct_url, timeout=5)
        return base64.b64encode(response.content).decode('utf-8')
    except: return ""

# --- 2. ग्लोबल एसेट्स (Logo & BG) ---
def get_assets():
    try:
        data = get_sheet("App_Assets").get_all_records()
        logo_link = next((r['Asset_Link'] for r in data if r['Asset_Name'] == 'NCC_Logo'), "")
        bg_link = next((r['Asset_Link'] for r in data if r['Asset_Name'] == 'Portal_BG'), "")
        return get_b64_from_drive(logo_link), get_b64_from_drive(bg_link)
    except: return "", ""

# --- 3. UI डिजाइन (Professional Glass Look) ---
def get_ui_style(bg_b64=""):
    bg_style = f"background-image: url('data:image/png;base64,{bg_b64}');" if bg_b64 else "background: #003366;"
    return f'''
    <head><meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no"></head>
    <style>
        body {{ 
            font-family: 'Segoe UI', sans-serif; margin: 0; padding-bottom: 90px; text-align: center; color: #333;
            {bg_style} background-size: cover; background-attachment: fixed; background-position: center;
        }}
        .header {{ 
            background: rgba(0, 51, 102, 0.9); color: white; padding: 15px; display: flex; align-items: center; 
            position: sticky; top: 0; z-index: 1000; backdrop-filter: blur(10px); border-bottom: 2px solid #ffcc00;
        }}
        .header-text {{ text-align: left; margin-left: 10px; flex-grow: 1; }}
        .header-text b {{ font-size: 18px; display: block; color: #ffcc00; }}
        .header-text span {{ font-size: 14px; opacity: 0.9; }}
        
        .main-card {{ 
            background: rgba(255, 255, 255, 0.85); padding: 22px; margin: 15px auto; border-radius: 20px; 
            box-shadow: 0 8px 32px rgba(0,0,0,0.1); width: 88%; max-width: 400px; backdrop-filter: blur(5px);
            border: 1px solid rgba(255,255,255,0.3); text-align: left; cursor: pointer;
        }}
        .main-card h2 {{ margin: 0; font-size: 20px; color: #003366; }}
        .btn {{ background: #003366; color: white; padding: 12px 20px; border-radius: 10px; font-weight: bold; border: none; cursor: pointer; font-size: 16px; width: 100%; }}
        .notice-bar {{ background: rgba(255, 204, 0, 0.9); color: #000; padding: 8px; font-weight: bold; overflow: hidden; white-space: nowrap; }}
        .notice-text {{ display: inline-block; animation: marquee 15s linear infinite; }}
        @keyframes marquee {{ 0% {{ transform: translateX(100%); }} 100% {{ transform: translateX(-100%); }} }}
        .footer {{ position: fixed; bottom: 0; width: 100%; background: white; padding: 12px 0; font-size: 12px; color: #003366; font-weight: bold; border-top: 3px solid #003366; }}
        input {{ padding: 15px; border-radius: 12px; border: 1px solid #ddd; width: 90%; margin-bottom: 15px; font-size: 16px; }}
    </style>
    '''

# --- 4. रूट्स (Routes) ---

@app.route('/')
def login_page():
    logo_b64, bg_b64 = get_assets()
    return get_ui_style(bg_b64) + f'''
    <div style="padding-top: 60px;">
        <img src="data:image/png;base64,{logo_b64}" style="width:100px; margin-bottom:10px;">
        <h2 style="color:white; text-shadow: 2px 2px 4px #000;">महात्मा गांधी इंटर कॉलेज</h2>
        <h4 style="color:#ffcc00; margin-top:-10px; text-shadow: 1px 1px 2px #000;">दलन छपरा, बलिया</h4>
        <div class="main-card" style="text-align:center; margin-top:30px;">
            <h3>🇮🇳 कैडेट लॉगिन</h3>
            <form action="/login" method="post">
                <input name="id" placeholder="Regiment No." required>
                <input name="pw" type="password" placeholder="Password" required>
                <button type="submit" class="btn">प्रवेश करें</button>
            </form>
        </div>
    </div>
    '''

@app.route('/dashboard')
def dashboard():
    if 'user' not in session: return redirect('/')
    logo_b64, bg_b64 = get_assets()
    notice = "MGIC NCC दलन छपरा पोर्टल पर आपका स्वागत है!"
    return get_ui_style(bg_b64) + f'''
    <div class="header">
        <img src="data:image/png;base64,{logo_b64}" style="width:45px;">
        <div class="header-text">
            <b>MGIC दलन छपरा, बलिया</b>
            <span>जय हिंद, {session['rank']} {session['user']}</span>
        </div>
        <a href="/logout" style="color:white; text-decoration:none; font-size:12px;">Logout</a>
    </div>
    <div class="notice-bar"><div class="notice-text">{notice}</div></div>
    <div style="padding-top:10px;">
        <div class="main-card" onclick="location.href='/subjects_list'" style="border-left: 8px solid #003366;"><h2>📘 ट्रेनिंग लाइब्रेरी</h2><p>वीडियो और नोट्स देखें</p></div>
        <div class="main-card" onclick="location.href='/ai'" style="border-left: 8px solid #ff5500;"><h2>🤖 एआई सूबेदार</h2><p>सटीक जानकारी पाएं</p></div>
        <div class="main-card" onclick="location.href='/chat'" style="border-left: 8px solid #ffcc00;"><h2>💬 कैडेट चर्चा</h2><p>आपस में बातचीत करें</p></div>
        <div class="main-card" onclick="location.href='/quiz'" style="border-left: 8px solid #9c27b0;"><h2>📝 कैडेट क्विज</h2><p>अपनी तैयारी चेक करें</p></div>
        <div class="main-card" onclick="location.href='/store'" style="border-left: 8px solid #28a745;"><h2>🛍️ एनसीसी स्टोर</h2><p>वर्दी और सामान खरीदें</p></div>
    </div>
    <div class="footer">Developed by: CTO Krishna Pal Singh 🇮🇳</div>
    '''

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

@app.route('/buy/<name>/<price>', methods=['GET', 'POST'])
def buy(name, price):
    if 'user' not in session: return redirect('/')
    logo_b64, bg_b64 = get_assets()
    qr_link = ""
    try:
        settings = get_sheet("Store_Settings").get_all_records()
        qr_link = next((s['Setting_Value'] for s in settings if s['Setting_Name'] == 'Payment_QR'), "")
    except: pass
    
    qr_b64 = get_b64_from_drive(qr_link)
    
    if request.method == 'POST':
        tid = request.form.get('tid')
        get_sheet("Store_Orders").append_row([datetime.now().strftime("%d/%m/%Y %H:%M"), session['reg_no'], f"{session['rank']} {session['user']}", name, price, tid])
        return "✅ ऑर्डर सबमिट! <a href='/dashboard'>Home</a>"

    return get_ui_style(bg_b64) + f'''
    <div class="header"><img src="data:image/png;base64,{logo_b64}" style="width:40px;"><div class="header-text"><b>पेमेंट गेटवे</b></div></div>
    <div class="main-card" style="text-align:center;">
        <h3>{name} - ₹{price}</h3>
        <img src="data:image/png;base64,{qr_b64}" style="width:250px; border-radius:15px; border:5px solid #003366;">
        <form method="post" style="margin-top:20px;">
            <input name="tid" placeholder="Enter Transaction ID" required>
            <button type="submit" class="btn" style="background:#28a745;">Confirm Payment</button>
        </form>
    </div>
    '''

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# --- रन करें ---
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
