from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for
from datetime import datetime
import uuid

app = Flask(__name__)
app.secret_key = "replace_this_with_a_better_secret_in_prod"  # change for production

# ----------------- In-memory data -----------------
users = []  # each: {"name","email","password"}
services = [
    {"id": 1, "name": "Haircut", "price": 300, "duration": "30 mins"},
    {"id": 2, "name": "Facial", "price": 800, "duration": "45 mins"},
    {"id": 3, "name": "Manicure", "price": 500, "duration": "40 mins"},
    {"id": 4, "name": "Pedicure", "price": 600, "duration": "45 mins"},
    {"id": 5, "name": "Hair Spa", "price": 1000, "duration": "60 mins"},
    {"id": 6, "name": "Waxing (Full Arms & Legs)", "price": 700, "duration": "50 mins"},
    {"id": 7, "name": "Threading & Eyebrow Shaping", "price": 150, "duration": "15 mins"},
    {"id": 8, "name": "Bridal Makeup Package", "price": 4000, "duration": "120 mins"},
    {"id": 9, "name": "Hair Coloring", "price": 1200, "duration": "90 mins"},
    {"id": 10, "name": "Detox Body Spa", "price": 2500, "duration": "90 mins"}
]
bookings = []  # each: {"id","user_email","user_name","service_id","service_name","created_at"}

# ----------------- HTML Template (single-page) -----------------
page = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Beauty Parlor </title>
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <style>
    :root{
      --pink:#ff4d88; --light:#fff4f8; --muted:#666;
      --card-bg: #ffffff; --shadow: rgba(0,0,0,0.08);
      font-family: Inter, "Poppins", Arial, sans-serif;
    }
    body{ margin:0; background: linear-gradient(135deg,#fff0f5,#fffaf0); min-height:100vh; }
    .app { display:flex; min-height:100vh; }
    .sidebar {
      width:240px; background:var(--pink); color:#fff; padding:22px 16px; box-shadow:2px 0 12px rgba(0,0,0,0.06);
      position:fixed; height:100vh;
    }
    .brand { font-size:20px; font-weight:700; margin-bottom:18px; text-align:center; }
    .userbox { background: rgba(255,255,255,0.08); padding:10px; border-radius:8px; margin-bottom:18px; text-align:center;}
    .navbtn { display:block; width:100%; text-align:left; background:transparent; color:#fff; border:none; padding:10px 12px; margin:6px 0; border-radius:8px; cursor:pointer; font-weight:600; }
    .navbtn:hover { background: rgba(255,255,255,0.08); }
    .main { margin-left:260px; padding:30px; flex:1; }
    .card { background:var(--card-bg); border-radius:12px; padding:18px; box-shadow: 0 6px 18px var(--shadow); }
    h1{ color:var(--pink); margin:0 0 8px 0; }
    .grid { display:grid; gap:14px; grid-template-columns: repeat(auto-fit, minmax(240px,1fr)); margin-top:16px; }
    .service { padding:12px; border-radius:10px; border:1px solid #f1f1f1; }
    .service h3{ margin:0 0 6px 0; color:#333; }
    .muted{ color:var(--muted); font-size:14px; }
    input, select { width:100%; padding:10px; border-radius:8px; border:1px solid #ddd; margin-top:8px; }
    button.primary { background:var(--pink); color:#fff; border:none; padding:10px 14px; border-radius:8px; cursor:pointer; font-weight:700; margin-top:10px; }
    .center { text-align:center; }
    .small { font-size:13px; color:#888; margin-top:8px; }
    .success { background:#e6ffef; color:#0a7a3e; padding:10px; border-radius:8px; }
    .error { background:#ffe6ea; color:#9b1522; padding:10px; border-radius:8px; }
    .topbar { display:flex; justify-content:space-between; align-items:center; margin-bottom:18px; }
    .logout { background:transparent; color:var(--pink); border:1px solid var(--pink); padding:8px 12px; border-radius:8px; cursor:pointer; }
    .hidden{ display:none; }
    footer{ margin-top:20px; color:#999; font-size:13px; }
  </style>
</head>
<body>
  <div class="app">
    <aside class="sidebar">
      <div class="brand">💅 Beauty Parlor</div>

      <div id="userBox" class="userbox">
        <div id="userName" style="font-weight:700">Guest</div>
        <div id="userEmail" class="small">Please login / signup</div>
      </div>

      <button class="navbtn" onclick="showSection('home')">🏠 Home</button>
      <button class="navbtn" onclick="showSection('services')">✂️ Services</button>
      <button class="navbtn" onclick="showSection('book')">📅 Book Appointment</button>
      <button class="navbtn" onclick="showSection('mybookings')">📖 My Bookings</button>

      <div style="margin-top:18px;">
        <button id="toSignup" class="navbtn" onclick="showSection('signup')">📝 Signup</button>
        <button id="toLogin" class="navbtn" onclick="showSection('login')">🔐 Login</button>
        <button id="btnLogout" class="navbtn hidden" onclick="logout()">🚪 Logout</button>
      </div>

      <div style="position:absolute; bottom:18px; left:16px; right:16px;">
        <div class="small center">Built for demo • in-memory data</div>
      </div>
    </aside>

    <main class="main">
      <div class="topbar">
        <div><h1>Beauty Parlor</h1><div class="small">Manage bookings & services</div></div>
        <div id="topRight"></div>
      </div>

      <!-- HOME -->
      <section id="sec-home" class="card">
        <h2>Welcome 👋</h2>
        <p class="muted">This is glowify app. Login to create bookings.</p>
      </section>

      <!-- SERVICES -->
      <section id="sec-services" class="card hidden">
        <h2>Available Services</h2>
        <div id="servicesGrid" class="grid"></div>
      </section>

      <!-- BOOK -->
      <section id="sec-book" class="card hidden">
        <h2>Book an Appointment</h2>
        <div id="bookMessages"></div>
        <label>Select Service</label>
        <select id="book_service_id"></select>
        <label>Your Name</label>
        <input id="book_customer" placeholder="Your full name">
        <button class="primary" onclick="bookNow()">Book Now</button>
        <div class="small">You must be logged in to book. If not logged in, use Signup / Login from the sidebar.</div>
      </section>

      <!-- MY BOOKINGS -->
      <section id="sec-mybookings" class="card hidden">
        <h2>My Bookings</h2>
        <div id="myBookingsList"></div>
      </section>

      <!-- SIGNUP -->
      <section id="sec-signup" class="card hidden">
        <h2>Create Account</h2>
        <div id="signupMsg"></div>
        <label>Full name</label>
        <input id="su_name" placeholder="e.g. Riya Sharma">
        <label>Email</label>
        <input id="su_email" placeholder="your@email.com">
        <label>Password</label>
        <input id="su_password" type="password" placeholder="choose a password">
        <button class="primary" onclick="signup()">Signup</button>
      </section>

      <!-- LOGIN -->
      <section id="sec-login" class="card hidden">
        <h2>Login</h2>
        <div id="loginMsg"></div>
        <label>Email</label>
        <input id="li_email" placeholder="your@email.com">
        <label>Password</label>
        <input id="li_password" type="password" placeholder="your password">
        <button class="primary" onclick="login()">Login</button>
      </section>

      <footer>© {{ year }} Beauty Parlor</footer>
    </main>
  </div>

<script>
  // --- navigation ---
  function showSection(name){
    const secs = ['home','services','book','mybookings','signup','login'];
    secs.forEach(s => {
      const el = document.getElementById('sec-' + s);
      if(el) el.classList.add('hidden');
    });
    const target = document.getElementById('sec-' + name);
    if(target) target.classList.remove('hidden');
    // load data as needed
    if(name === 'services') loadServices();
    if(name === 'book') loadBookForm();
    if(name === 'mybookings') loadMyBookings();
  }

  // --- session check ---
  async function checkSession(){
    const res = await fetch('/session');
    const data = await res.json();
    if(data.logged_in){
      document.getElementById('userName').textContent = data.name;
      document.getElementById('userEmail').textContent = data.email;
      document.getElementById('btnLogout').classList.remove('hidden');
      document.getElementById('toLogin').classList.add('hidden');
      document.getElementById('toSignup').classList.add('hidden');
      // show top right
      document.getElementById('topRight').innerHTML = '<div style="color:#666">Logged in as <b style="color:var(--pink)">'+data.name+'</b></div>';
    } else {
      document.getElementById('userName').textContent = 'Guest';
      document.getElementById('userEmail').textContent = 'Please login / signup';
      document.getElementById('btnLogout').classList.add('hidden');
      document.getElementById('toLogin').classList.remove('hidden');
      document.getElementById('toSignup').classList.remove('hidden');
      document.getElementById('topRight').innerHTML = '';
    }
  }

  // --- services ---
  async function loadServices(){
    const res = await fetch('/services');
    const list = await res.json();
    const grid = document.getElementById('servicesGrid');
    grid.innerHTML = '';
    list.forEach(s => {
      const div = document.createElement('div');
      div.className = 'service';
      div.innerHTML = `<h3>${s.name}</h3>
                       <div class="muted">₹${s.price} • ${s.duration}</div>
                       <div style="margin-top:8px"><button onclick="prefillBook(${s.id})" class="primary">Book ${s.name}</button></div>`;
      grid.appendChild(div);
    });
  }

  function prefillBook(service_id){
    showSection('book');
    document.getElementById('book_service_id').value = service_id;
  }

  // populate service dropdown when booking
  async function loadBookForm(){
    const res = await fetch('/services');
    const list = await res.json();
    const sel = document.getElementById('book_service_id');
    sel.innerHTML = '';
    list.forEach(s => {
      const opt = document.createElement('option');
      opt.value = s.id;
      opt.text = `${s.name} — ₹${s.price}`;
      sel.appendChild(opt);
    });
  }

  // --- signup/login/logout ---
  async function signup(){
    const name = document.getElementById('su_name').value.trim();
    const email = document.getElementById('su_email').value.trim();
    const password = document.getElementById('su_password').value;
    const msg = document.getElementById('signupMsg');
    msg.innerHTML = '';
    if(!name || !email || !password){ msg.innerHTML = '<div class="error">Please fill all fields.</div>'; return; }
    const res = await fetch('/signup', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({name,email,password})
    });
    const data = await res.json();
    if(data.success){
      msg.innerHTML = '<div class="success">'+data.message+'</div>';
      document.getElementById('su_name').value=''; document.getElementById('su_email').value=''; document.getElementById('su_password').value='';
      // auto-login or prompt to login
      await checkSession();
    } else {
      msg.innerHTML = '<div class="error">'+data.message+'</div>';
    }
  }

  async function login(){
    const email = document.getElementById('li_email').value.trim();
    const password = document.getElementById('li_password').value;
    const msg = document.getElementById('loginMsg');
    msg.innerHTML = '';
    if(!email || !password){ msg.innerHTML = '<div class="error">Please fill all fields.</div>'; return; }
    const res = await fetch('/login', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({email,password})
    });
    const data = await res.json();
    if(data.success){
      msg.innerHTML = '<div class="success">'+data.message+'</div>';
      document.getElementById('li_email').value=''; document.getElementById('li_password').value='';
      await checkSession();
      showSection('home');
    } else {
      msg.innerHTML = '<div class="error">'+data.message+'</div>';
    }
  }

  async function logout(){
    await fetch('/logout');
    await checkSession();
    showSection('home');
  }

  // --- booking ---
  async function bookNow(){
    const sel = document.getElementById('book_service_id');
    const service_id = sel.value;
    const customer = document.getElementById('book_customer').value.trim();
    const msgbox = document.getElementById('bookMessages');
    msgbox.innerHTML = '';
    if(!customer){ msgbox.innerHTML = '<div class="error">Please enter your name.</div>'; return; }
    const res = await fetch('/book', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({service_id, customer})
    });
    const data = await res.json();
    if(data.success){
      msgbox.innerHTML = '<div class="success">'+data.message+'</div>';
      document.getElementById('book_customer').value = '';
      loadMyBookings();
    } else {
      msgbox.innerHTML = '<div class="error">'+data.message+'</div>';
    }
  }

  // --- my bookings ---
  async function loadMyBookings(){
    const res = await fetch('/bookings');
    const data = await res.json();
    const el = document.getElementById('myBookingsList');
    el.innerHTML = '';
    if(!data.logged_in){ el.innerHTML = '<div class="muted">Please login to see your bookings.</div>'; return; }
    if(data.bookings.length === 0){ el.innerHTML = '<div class="muted">You have no bookings yet.</div>'; return; }
    data.bookings.forEach(b => {
      const d = document.createElement('div');
      d.className = 'service';
      d.innerHTML = `<strong>${b.service_name}</strong><div class="muted">Booked for: ${b.user_name} • ${b.created_at}</div>`;
      el.appendChild(d);
    });
  }

  // initial
  (async function(){
    await checkSession();
    showSection('home');
  })();

</script>
</body>
</html>
"""

# ----------------- Helper utilities -----------------
def find_user_by_email(email):
    return next((u for u in users if u['email'].lower() == email.lower()), None)

# ----------------- Routes -----------------
@app.route('/')
def index():
    return render_template_string(page, year=datetime.now().year)

@app.route('/session', methods=['GET'])
def get_session():
    if 'user_email' in session:
        return jsonify({"logged_in": True, "email": session['user_email'], "name": session.get('user_name', '')})
    else:
        return jsonify({"logged_in": False})

@app.route('/signup', methods=['POST'])
def signup():
    data = request.json or {}
    name = data.get('name', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    if not name or not email or not password:
        return jsonify({"success": False, "message": "Please provide name, email and password."})
    if find_user_by_email(email):
        return jsonify({"success": False, "message": "User already exists. Please login."})
    users.append({"name": name, "email": email, "password": password})
    # auto-login after signup
    session['user_email'] = email
    session['user_name'] = name
    return jsonify({"success": True, "message": "Signup successful — you are now logged in."})

@app.route('/login', methods=['POST'])
def login():
    data = request.json or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    user = find_user_by_email(email)
    if user and user['password'] == password:
        session['user_email'] = user['email']
        session['user_name'] = user['name']
        return jsonify({"success": True, "message": f"Welcome back, {user['name']}!"})
    return jsonify({"success": False, "message": "Invalid email or password."})

@app.route('/logout', methods=['GET'])
def logout():
    session.pop('user_email', None)
    session.pop('user_name', None)
    return redirect(url_for('index'))

@app.route('/services', methods=['GET'])
def get_services():
    return jsonify(services)

@app.route('/book', methods=['POST'])
def book():
    if 'user_email' not in session:
        return jsonify({"success": False, "message": "You must be logged in to book."})
    data = request.json or {}
    service_id = data.get('service_id')
    customer = data.get('customer', '').strip()
    try:
        service_id = int(service_id)
    except Exception:
        return jsonify({"success": False, "message": "Invalid service selected."})
    service = next((s for s in services if s['id'] == service_id), None)
    if not service:
        return jsonify({"success": False, "message": "Service not found."})
    if not customer:
        return jsonify({"success": False, "message": "Please enter your name."})
    booking = {
        "id": str(uuid.uuid4()),
        "user_email": session['user_email'],
        "user_name": customer,
        "service_id": service['id'],
        "service_name": service['name'],
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    bookings.append(booking)
    return jsonify({"success": True, "message": f"Appointment confirmed for {customer} — {service['name']} (₹{service['price']})"})

@app.route('/bookings', methods=['GET'])
def my_bookings():
    if 'user_email' not in session:
        return jsonify({"logged_in": False, "bookings": []})
    user_email = session['user_email']
    user_bs = [b for b in bookings if b['user_email'] == user_email]
    return jsonify({"logged_in": True, "bookings": user_bs})

# ----------------- Run -----------------
import os

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5009))  # Render gives its own PORT
    app.run(host='0.0.0.0', port=port, debug=True)
