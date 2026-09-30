import os, sqlite3
from datetime import datetime
from flask import Flask, Response, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash

app=Flask(__name__)
app.secret_key=os.environ.get("SECRET_KEY","change-this-before-public-deploy")
DB="flowdm.db"

def con():
    c=sqlite3.connect(DB);c.row_factory=sqlite3.Row;return c

def init():
    c=con();c.execute("CREATE TABLE IF NOT EXISTS users (name TEXT PRIMARY KEY,password TEXT NOT NULL,role TEXT NOT NULL)");c.execute("CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT,role TEXT,text TEXT,created TEXT)");c.commit();c.close()
init()

def name(x):return ''.join(a for a in str(x) if a.isalnum() or a in '_-')[:24]

PAGE="""<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'><title>FlowDm</title><style>*{box-sizing:border-box}body{margin:0;background:#0c0c0e;color:#f5eeee;font:15px Arial}#auth{min-height:100vh;display:grid;place-items:center;background:radial-gradient(circle at 75% 0,#45171c,#090909 50%)}.card{width:390px;max-width:92%;background:#151515;border:1px solid #51252a;border-radius:12px;padding:28px}.logo{font-size:27px;font-weight:bold}.logo:before{content:'●';color:#e83e48;margin-right:8px}input{width:100%;padding:12px;background:#090909;border:1px solid #40262a;border-radius:7px;color:white;margin:6px 0;font:inherit}button{border:0;background:#e83e48;color:white;border-radius:7px;padding:11px 16px;cursor:pointer;font:inherit}.alt{background:#2c2022}.err{color:#ff858c;min-height:20px}#app{display:none;height:100vh;max-width:900px;margin:auto;grid-template-rows:58px 1fr 74px;background:#121214;border-left:1px solid #382326;border-right:1px solid #382326}header{padding:20px;border-bottom:1px solid #382326;font-weight:bold}#msgs{padding:18px;overflow:auto}.msg{padding:10px;border-radius:6px}.msg:hover{background:#1c1516}.admin{color:#ff5661}.moder{color:#ffb34f}.time{font-size:11px;color:#a89194;margin-left:8px}.text{display:block;margin-top:5px;white-space:pre-wrap}form{display:flex;gap:8px;padding:13px;border-top:1px solid #382326}form input{flex:1;margin:0;background:#211719}form button{margin:0}.top{float:right;background:#2c2022;padding:7px 10px}.hint{color:#a89194}</style><section id=auth><div class=card><div class=logo>FlowDm</div><p class=hint>Публичный чат</p><input id=n placeholder='Ник'><input id=p type=password placeholder='Пароль'><div id=e class=err></div><button onclick="go('/register')">Регистрация</button><button class=alt onclick="go('/login')">Войти</button></div></section><section id=app><header># общая <button class=top onclick=out()>Выйти</button><span id=who></span></header><div id=msgs></div><form onsubmit="send(event)"><input id=t maxlength=500 placeholder='Написать сообщение'><button>Отправить</button></form></section><script>let u,old='';async function api(a,o={}){let r=await fetch(a,o),d=await r.json();if(!r.ok)throw Error(d.error);return d}async function go(x){try{u=(await api(x,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({n:n.value,p:p.value})})).u;open()}catch(x){e.textContent=x.message}}function open(){auth.style.display='none';app.style.display='grid';who.textContent=' · '+u.name;load();setInterval(load,1500)}async function load(){let d=await api('/messages'),k=JSON.stringify(d);if(k===old)return;old=k;msgs.innerHTML='';d.forEach(x=>{let z=document.createElement('div');z.className='msg';let h=document.createElement('b');h.className=x.role;h.textContent='['+x.role.toUpperCase()+'] '+x.name;let q=document.createElement('span');q.className='text';q.textContent=x.text;z.append(h,q);msgs.append(z);msgs.scrollTop=msgs.scrollHeight})}async function send(x){x.preventDefault();try{await api('/send',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:t.value})});t.value='';old='';load()}catch(x){alert(x.message)}}async function out(){await api('/logout',{method:'POST'});location.reload()}fetch('/me').then(x=>x.json()).then(x=>{if(x.u){u=x.u;open()}})</script>"""
@app.route('/')
def home():return Response(PAGE,mimetype='text/html')
@app.route('/me')
def mer():return jsonify(u={'name':session['u']} if 'u' in session else None)
@app.route('/register',methods=['POST'])
def reg():
    d=request.json or {};n=name(d.get('n',''));p=str(d.get('p',''))
    if len(n)<3 or len(p)<6:return jsonify(error='Ник от 3, пароль от 6 символов'),400
    c=con()
    if c.execute('SELECT 1 FROM users WHERE name=?',(n,)).fetchone():c.close();return jsonify(error='Ник занят'),400
    role='admin' if not c.execute('SELECT 1 FROM users LIMIT 1').fetchone() else 'player';c.execute('INSERT INTO users VALUES(?,?,?)',(n,generate_password_hash(p),role));c.commit();c.close();session['u']=n;return jsonify(u={'name':n})
@app.route('/login',methods=['POST'])
def login():
    d=request.json or {};n=name(d.get('n',''));c=con();u=c.execute('SELECT * FROM users WHERE name=?',(n,)).fetchone();c.close()
    if not u or not check_password_hash(u['password'],str(d.get('p',''))):return jsonify(error='Неверный ник или пароль'),401
    session['u']=n;return jsonify(u={'name':n})
@app.route('/logout',methods=['POST'])
def logout():session.clear();return jsonify(ok=True)
@app.route('/messages')
def messages():
    if 'u' not in session:return jsonify(error='Войди'),401
    c=con();rows=c.execute('SELECT name,role,text,created FROM messages ORDER BY id DESC LIMIT 200').fetchall();c.close();return jsonify([dict(x) for x in reversed(rows)])
@app.route('/send',methods=['POST'])
def send():
    if 'u' not in session:return jsonify(error='Войди'),401
    text=str((request.json or {}).get('text','')).strip()[:500]
    if not text:return jsonify(error='Пустое сообщение'),400
    c=con();u=c.execute('SELECT role FROM users WHERE name=?',(session['u'],)).fetchone();c.execute('INSERT INTO messages(name,role,text,created) VALUES(?,?,?,?)',(session['u'],u['role'],text,datetime.now().isoformat()));c.commit();c.close();return jsonify(ok=True)
if __name__=='__main__':app.run(host='0.0.0.0',port=int(os.environ.get('PORT',5000)))
