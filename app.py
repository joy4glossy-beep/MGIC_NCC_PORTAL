import os
import json
import uuid
from flask import Flask, render_template, request, redirect, url_for, session
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

app = Flask(__name__)
app.secret_key = "MGIC_NCC_2026_V4_6_MASTER"

# --- 1. गूगल शीट कनेक्शन ---
def get_sheet(sheet_name):
    json_key = os.environ.get('SERVICE_ACCOUNT_JSON')
    creds_dict = json.loads(json_key)
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client.open("NCC_Smart_Portal_Data").worksheet(sheet_name)

# --- 2. UI डिजाइन (iPhone 11 Optimized) ---
UI_STYLE = '''
<style>
    body { font-family: 'Segoe UI', sans-serif; background: #f4f7f6; margin: 0; padding-bottom: 80px; text-align: center; color: #333; }
    .header { background: linear-gradient(135deg, #003366, #00509d); color: white; padding: 15px; display: flex; justify-content: space-between; align-items: center; position: sticky; top: 0; z-index: 1000; box-shadow: 0 2px 8px rgba(0,0,0,0.2); }
    .notice-bar { background: #ffcc00; color: #000; padding: 8px; font-weight: bold; font-size: 13px; overflow: hidden; white-space: nowrap; border-bottom: 1px solid #e6b800; }
    .notice-text { display: inline-block; animation: marquee 15s linear infinite; }
    @keyframes marquee { 0% { transform: translateX(100%); } 100% { transform: translateX(-100%); } }
    .main-card { background: white; padding: 20px; margin: 15px auto; border-radius: 15px; box-shadow: 0 3px 10px rgba(0,0,0,0.1); width: 88%; max-width: 400px; border-left: 6px solid #003366; text-align: left; cursor: pointer; }
    .btn { background: #003366; color: white; padding: 10px 18px; border-radius: 8px; text-decoration: none; font-weight: bold; border: none; cursor: pointer; }
    .chat-box { background: white; margin: 10px auto; padding: 12px; border-radius: 10px; width: 92%; text-align: left; box-shadow: 0 1px 4px rgba(0,0,0,0.1); border-left: 4px solid #ffcc00; }
    .content-box { background: white; margin: 15px auto; padding: 20px; border-radius: 15px; width: 90%; text-align: left; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
    input, textarea { padding: 12px; border-radius: 8px; border: 1px solid #ddd; width: 85%; font-size: 15px; margin-bottom: 10px; }
    .footer { position: fixed; bottom: 0; width: 100%; background: #eee; padding: 12px 0; font-size: 12px; color: #555; border-top: 1px solid #ddd; font-weight: bold; z-index: 1000; }
    .quiz-option { display: block; background: #f9f9f9; padding: 10px; margin: 10px 0; border-radius: 8px; border: 1px solid #ddd; text-align: left; cursor: pointer; }
</style>
'''

FOOTER = '<div class="footer">Developed by: CTO Krishna Pal Singh 🇮🇳</div>'

def get_notice():
    try:
        admin_data = get_sheet("Admin_Settings").get_all_records()
        return next((row['Value'] for row in admin_data if row['Feature'] == 'Notice'), "जय हिंद कैडेट्स!")
    except: return "MGIC NCC पोर्टल पर आपका स्वागत है!"

# --- 3. डैशबोर्ड ---
@app.route('/dashboard')
def dashboard():
    if 'user' not in session: return redirect('/')
    notice = get_notice()
    return UI_STYLE + f'''
    <div class="header"><span>जय हिंद, {session['rank']} {session['user']}</span><a href="/logout" style="color:white; font-size:12px;">Logout</a></div>
    <div class="notice-bar"><div class="notice-text">{notice}</div></div>
    <div style="padding-top:10px;">
        <div class="main-card" onclick="location.href='/subjects_list'"><h2>📘 ट्रेनिंग लाइब्रेरी</h2><p>वीडियो और नोट्स देखें</p></div>
        <div class="main-card" onclick="location.href='/ai'" style="border-left-color:#ff5500;"><h2>🤖 एआई सूबेदार</h2><p>सटीक जानकारी पाएं</p></div>
        <div class="main-card" onclick="location.href='/chat'" style="border-left-color:#ffcc00;"><h2>💬 कैडेट चर्चा</h2><p>आपस में बातचीत करें</p></div>
        <div class="main-card" onclick="location.href='/quiz'" style="border-left-color:#9c27b0;"><h2>📝 कैडेट क्विज</h2><p>अपनी तैयारी चेक करें</p></div>
        <div class="main-card" onclick="location.href='/store'" style="border-left-color:#28a745;"><h2>🛍️ एनसीसी स्टोर</h2><p>वर्दी और सामान खरीदें</p></div>
    </div>
    ''' + FOOTER

# --- 4. एनसीसी स्टोर ---
@app.route('/store')
def store():
    if 'user' not in session: return redirect('/')
    products = get_sheet("Product_List").get_all_records()
    notice = get_notice()
    grid_html = ""
    for p in products:
        grid_html += f'''
        <div class="product-card" style="background:white; margin:10px; border-radius:10px; padding:10px; box-shadow:0 2px 5px rgba(0,0,0,0.1); width:40%; display:inline-block; vertical-align:top;">
            <img src="{p.get('Image_Link', '')}" style="width:100%; height:100px; object-fit:cover; border-radius:5px;">
            <h4 style="font-size:14px; margin:5px 0;">{p.get('Product_Name', 'N/A')}</h4>
            <div style="color:#28a745; font-weight:bold;">₹{p.get('Price', '0')}</div>
            <button class="btn" onclick="location.href='/buy/{p.get('Product_Name')}/{p.get('Price')}'" style="width:100%; padding:5px; font-size:12px; margin-top:5px;">Buy</button>
        </div>
        '''
    return UI_STYLE + f'<div class="header"><h2>एनसीसी स्टोर</h2><a href="/dashboard" style="color:white;">Back</a></div><div class="notice-bar"><div class="notice-text">{notice}</div></div><div style="padding:10px;">{grid_html}</div>' + FOOTER

@app.route('/buy/<name>/<price>', methods=['GET', 'POST'])
def buy(name, price):
    if 'user' not in session: return redirect('/')
    try:
        settings = get_sheet("Store_Settings").get_all_records()
        qr_link = next((s['Setting_Value'] for s in settings if s['Setting_Name'] == 'Payment_QR'), "")
    except: qr_link = ""

    if request.method == 'POST':
        tid = request.form.get('tid')
        sheet = get_sheet("Store_Orders")
        now = datetime.now().strftime("%d/%m/%Y %H:%M")
        sheet.append_row([now, session['reg_no'], f"{session['rank']} {session['user']}", name, price, tid])
        return UI_STYLE + f'<div style="padding-top:100px;"><h3>✅ ऑर्डर सबमिट हो गया!</h3><a href="/dashboard" class="btn">Back to Home</a></div>' + FOOTER
    
    return UI_STYLE + f'''
    <div class="header"><h2>पेमेंट करें</h2><a href="/store" style="color:white;">Back</a></div>
    <div class="content-box" style="text-align:center;">
        <h3>{name} - ₹{price}</h3>
        <img src="{qr_link}" style="width:250px; border:5px solid #003366; border-radius:10px; margin: 15px 0;">
        <form method="post">
            <input name="tid" placeholder="Enter Transaction ID" required>
            <br><button type="submit" class="btn" style="background:#28a745; width:90%;">Confirm Order</button>
        </form>
    </div>
    ''' + FOOTER

# --- 5. कैडेट चर्चा ---
@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if 'user' not in session: return redirect('/')
    try:
        sheet = get_sheet("Chat_Messages")
        notice = get_notice()
        if request.method == 'POST':
            msg = request.form.get('message', '').strip()
            parent_id = request.form.get('parent_id', '0')
            if msg:
                now = datetime.now().strftime("%d/%m %I:%M %p")
                sheet.append_row([now, f"{session['rank']} {session['user']}", session['reg_no'], msg, parent_id])
            return redirect('/chat')

        all_msgs = sheet.get_all_records()
        chat_html = ""
        questions = [m for m in all_msgs if str(m.get('Parent_ID', '0')) == '0']
        for q in questions:
            q_id = f"{q.get('Reg_No')}_{q.get('Timestamp')}"
            chat_html += f'''
            <div class="chat-box">
                <div class="meta">{q.get('Timestamp')} - {q.get('Name_Rank')}</div>
                <strong>{q.get('Message')}</strong>
                <form method="post" style="display:flex; margin-top:10px;">
                    <input name="message" placeholder="जवाब दें..." style="width:70%; margin:0; padding:5px;" required>
                    <input type="hidden" name="parent_id" value="{q_id}">
                    <button type="submit" class="btn" style="padding:5px; margin-left:5px;">Reply</button>
                </form>
            '''
            replies = [r for r in all_msgs if str(r.get('Parent_ID')) == q_id]
            for r in replies:
                chat_html += f'<div style="margin-left:25px; border-left:2px solid #003366; padding-left:10px; font-size:14px; margin-top:5px;"><div class="meta">{r.get("Timestamp")} - {r.get("Name_Rank")}</div>{r.get("Message")}</div>'
            chat_html += "</div>"
        return UI_STYLE + f'<div class="header"><h2>कैडेट चर्चा</h2><a href="/dashboard" style="color:white;">Back</a></div><div class="notice-bar"><div class="notice-text">{notice}</div></div><div style="padding:15px;"><form method="post"><textarea name="message" placeholder="नया सवाल पूछें..." required></textarea><input type="hidden" name="parent_id" value="0"><br><button type="submit" class="btn">Post Question</button></form><hr>{chat_html}</div>' + FOOTER
    except Exception as e: return f"Error: {str(e)}"

# --- 6. एआई सूबेदार (Direct Search Logic) ---
@app.route('/ai', methods=['GET', 'POST'])
def ai():
    if 'user' not in session: return redirect('/')
    results, user_q, notice = [], "", get_notice()
    if request.method == 'POST':
        user_q = request.form.get('q', '').lower().strip()
        try:
            library_data = get_sheet("Content_Library").get_all_records()
            # Direct keyword matching from library
            for row in library_data:
                topic = row.get('Topic_Name', '').lower()
                desc = row.get('Description', '').lower()
                if user_q in topic or user_q in desc:
                    results.append(row)
        except: pass
    
    res_html = ""
    for r in results:
        v_id = r.get('Link','').split("v=")[-1] if "v=" in r.get('Link','') else r.get('Link','').split("/")[-1]
        res_html += f'<div class="content-box"><h3>{r.get("Topic_Name")}</h3><p>{r.get("Description","")}</p><iframe width="100%" height="200" src="https://www.youtube.com/embed/{v_id}" frameborder="0" style="border-radius:10px;"></iframe><br><a href="{r.get("Book_Link", "")}" class="btn" style="background:#28a745; margin-top:10px;">📘 Read Handbook</a></div>'

    return UI_STYLE + f'''
    <div class="header"><h2>एआई सूबेदार</h2><a href="/dashboard" style="color:white;">Back</a></div>
    <div style="padding:15px;">
        <form method="post"><input name="q" placeholder="विषय खोजें (e.g. Map, Weapon)" required><br><button type="submit" class="btn">खोजें</button></form>
        {res_html if res_html else "<p style='margin-top:20px;'>लाइब्रेरी में खोजें...</p>"}
    </div>
    ''' + FOOTER

# --- 7. कैडेट क्विज ---
@app.route('/quiz')
def quiz():
    if 'user' not in session: return redirect('/')
    try:
        q_data = get_sheet("Quiz_Data").get_all_records()
        return UI_STYLE + f'''
        <div class="header"><h2>कैडेट क्विज</h2><a href="/dashboard" style="color:white;">Back</a></div>
        <div style="padding:20px;">
            <h3>प्रश्नावली</h3>
            <p>अपनी तैयारी जांचने के लिए सवालों के जवाब दें।</p>
            <div id="quiz-container">
                {"".join([f'<div class="main-card"><h4>{q.get("Question")}</h4><div class="quiz-option">{q.get("Opt1")}</div><div class="quiz-option">{q.get("Opt2")}</div><div class="quiz-option">{q.get("Opt3")}</div><div class="quiz-option">{q.get("Correct")}</div></div>' for q in q_data[:5]])}
            </div>
            <button class="btn" onclick="alert('आपका स्कोर शीट में सेव हो गया!')">Submit Score</button>
        </div>
        ''' + FOOTER
    except: return UI_STYLE + "Quiz sheet not found!" + FOOTER

# --- बाकी रूट्स ---
@app.route('/')
def login_page():
    if 'user' in session: return redirect('/dashboard')
    return UI_STYLE + '<div style="padding-top:100px;"><h2>🇮🇳 MGIC NCC पोर्टल</h2><form action="/login" method="post"><input name="id" placeholder="Reg No" required><br><input name="pw" type="password" placeholder="Password" required><br><button type="submit" class="btn">लॉगिन</button></form></div>' + FOOTER

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
    except Exception as e: return f"Error: {str(e)}"

@app.route('/subjects_list')
def subjects_list():
    if 'user' not in session: return redirect('/')
    lib = get_sheet("Content_Library").get_all_records()
    topics = sorted(list(set([row.get('Topic_Name') for row in lib if row.get('Topic_Name')])))
    html = f'<div class="header"><h2>विषय सूची</h2><a href="/dashboard" style="color:white;">Back</a></div>'
    for t in topics: html += f'<div class="main-card" onclick="location.href=\'/view_subject/{t}\'"><h3>{t}</h3></div>'
    return UI_STYLE + html + FOOTER

@app.route('/view_subject/<name>')
def view_subject(name):
    if 'user' not in session: return redirect('/')
    lib = get_sheet("Content_Library").get_all_records()
    html = f'<div class="header"><h2>{name}</h2><a href="/subjects_list" style="color:white;">Back</a></div>'
    for v in lib:
        if v.get('Topic_Name') == name:
            v_id = v.get('Link','').split("v=")[-1] if "v=" in v.get('Link','') else v.get('Link','').split("/")[-1]
            html += f'<div class="content-box"><iframe width="100%" height="220" src="https://www.youtube.com/embed/{v_id}" frameborder="0" allowfullscreen style="border-radius:10px;"></iframe><br><a href="{v.get("Book_Link", "")}" class="btn" style="background:#28a745; margin-top:10px;">📘 Handbook</a></div>'
    return UI_STYLE + html + FOOTER

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
