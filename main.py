import os
import threading
from flask import Flask, render_template_string, request, jsonify

# --- BAGIAN 1: KODE SERVER (FLASK) ---
app = Flask(__name__)
rooms = {}

def check_winner(board):
    win_patterns = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8], [0, 3, 6], 
        [1, 4, 7], [2, 5, 8], [0, 4, 8], [2, 4, 6]
    ]
    for p in win_patterns:
        if board[p[0]] == board[p[1]] == board[p[2]] != "":
            return f"{board[p[0]]} MENANG!"
    if "" not in board: return "SERI!"
    return None

HTML_CODE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&display=swap');
        body { margin: 0; background: #0f172a; color: white; font-family: 'Orbitron', sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh; overflow: hidden; }
        .container { text-align: center; width: 90%; max-width: 400px; display: flex; flex-direction: column; height: 90vh; }
        #room-menu { display: flex; flex-direction: column; gap: 10px; margin-top: 20px; }
        input { padding: 12px; border-radius: 8px; border: none; text-align: center; font-family: 'Orbitron'; }
        .btn { padding: 12px; background: #38bdf8; border: none; border-radius: 8px; color: white; font-weight: bold; cursor: pointer; font-family: 'Orbitron'; }
        .board { display: grid; grid-template-columns: repeat(3, 1fr); gap: 5px; margin: 10px 0; }
        .cell { aspect-ratio: 1/1; background: #1e293b; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 24px; border: 2px solid #334155; }
        #chat-history { flex: 1; background: #1e293b; overflow-y: auto; padding: 10px; font-size: 11px; display: flex; flex-direction: column; gap: 5px; border-radius: 8px; margin-bottom: 5px; }
        .msg { padding: 5px 10px; border-radius: 5px; background: #334155; max-width: 80%; }
    </style>
</head>
<body>
    <div class="container">
        <div id="room-menu">
            <h2 style="color:#38bdf8">SLAYER APK</h2>
            <input type="text" id="room-id" placeholder="Kode Kamar">
            <button class="btn" onclick="join('X')">P1 (X)</button>
            <button class="btn" style="background:#10b981" onclick="join('O')">P2 (O)</button>
        </div>
        <div id="game-area" style="display:none; flex-direction: column; height: 100%;">
            <div id="status">Giliran: X</div>
            <div class="board" id="board"></div>
            <div id="chat-history"></div>
            <div style="display:flex; gap:5px">
                <input type="text" id="msg" style="flex:1" placeholder="Pesan...">
                <button class="btn" onclick="sendChat()">></button>
            </div>
        </div>
    </div>
    <script>
        let room = "", symbol = "", lastMsg = 0;
        function join(s) {
            room = document.getElementById('room-id').value;
            if(!room) return;
            symbol = s;
            document.getElementById('room-menu').style.display = 'none';
            document.getElementById('game-area').style.display = 'flex';
            const b = document.getElementById('board');
            for(let i=0; i<9; i++) b.innerHTML += `<div class="cell" id="c${i}" onclick="move(${i})"></div>`;
            setInterval(sync, 1000);
        }
        async function sync() {
            const res = await fetch(`/get?r=${room}`);
            const data = await res.json();
            data.board.forEach((v,i) => document.getElementById('c'+i).innerText = v);
            document.getElementById('status').innerText = data.winner || "Giliran: " + data.turn;
            if(data.messages.length > lastMsg) {
                const h = document.getElementById('chat-history');
                h.innerHTML = data.messages.map(m => `<div class="msg">${m}</div>`).join('');
                h.scrollTop = h.scrollHeight;
                lastMsg = data.messages.length;
            }
        }
        async function move(i) {
            await fetch('/move', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({r:room, s:symbol, i:i})});
        }
        async function sendChat() {
            const m = document.getElementById('msg');
            await fetch('/chat', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({r:room, s:symbol, m:m.value})});
            m.value = "";
        }
    </script>
</body>
</html>
'''

@app.route('/')
def home(): return render_template_string(HTML_CODE)

@app.route('/get')
def get():
    r = request.args.get('r')
    if r not in rooms: rooms[r] = {'board':[""]*9, 'turn':'X', 'winner':None, 'messages':[]}
    return jsonify(rooms[r])

@app.route('/move', methods=['POST'])
def move():
    d = request.json
    r = rooms[d['r']]
    if r['turn'] == d['s'] and r['board'][d['i']] == "" and not r['winner']:
        r['board'][d['i']] = d['s']
        r['turn'] = 'O' if d['s'] == 'X' else 'X'
        r['winner'] = check_winner(r['board'])
    return jsonify({'ok':True})

@app.route('/chat', methods=['POST'])
def chat():
    d = request.json
    rooms[d['r']]['messages'].append(f"{d['s']}: {d['m']}")
    return jsonify({'ok':True})

# --- BAGIAN 2: KODE APK (KIVY) ---
try:
    from kivy.app import App
    from kivy.uix.modalview import ModalView
    from kvdroid.tools.webview import WebView # Library WebView untuk Android

    class SlayerApp(App):
        def build(self):
            # Jalankan Flask di Thread berbeda agar APK tidak macet
            threading.Thread(target=lambda: app.run(host='127.0.0.1', port=5000), daemon=True).start()
            # Tampilkan Webview yang membuka alamat Flask
            wv = WebView("http://127.0.0.1:5000", enable_javascript=True)
            return wv

    if __name__ == "__main__":
        SlayerApp().run()
except ImportError:
    # Jika dijalankan di Laptop (Tanpa Kivy)
    if __name__ == "__main__":
        app.run(debug=True, port=5000)
                    
