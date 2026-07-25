#!/usr/bin/env python3
import asyncio, re, os, sys, time, threading, json
from datetime import datetime
from collections import deque
from http.server import HTTPServer, BaseHTTPRequestHandler

print(">>> Dang cai thu vien...")
for lib in ['telethon']:
    try: __import__(lib)
    except: os.system(f"{sys.executable} -m pip install {lib} -q")

from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError

# ==================== CONFIG ====================
PHONE = os.environ.get('PHONE', '+84346139930')
API_ID = int(os.environ.get('API_ID', '35742832'))
API_HASH = os.environ.get('API_HASH', '93ac3807fede03197c86170865e01571')
CHANNEL = os.environ.get('CHANNEL', '@laucuataixiuroom')
BOT = os.environ.get('BOT', '@laucua_tx_room_bot')
BET_SIDE = os.environ.get('BET_SIDE', 'T')
BET_AMOUNT = int(os.environ.get('BET_AMOUNT', '10000'))
WAIT = int(os.environ.get('WAIT_SECONDS', '8'))
AUTO = os.environ.get('AUTO_BET', 'true').lower() == 'true'
SESSION = os.environ.get('SESSION_STRING', '')

print(f">>> Config: Phone={PHONE}, Auto={AUTO}, Side={BET_SIDE}, Amount={BET_AMOUNT}")

# ==================== TOOL ====================
class Tool:
    def __init__(self):
        self.client = None
        self.active = False
        self.sess = 0
        self.wins = 0
        self.loss = 0
        self.logs = deque(maxlen=100)
        self.st = datetime.now()
    
    def log(self, msg):
        t = datetime.now().strftime('%H:%M:%S')
        self.logs.append(f"[{t}] {msg}")
        print(f"[{t}] {msg}")
    
    async def go(self):
        self.log(">>> Ket noi Telegram...")
        
        if SESSION:
            self.client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)
        else:
            self.client = TelegramClient('session_file', API_ID, API_HASH)
        
        await self.client.connect()
        
        if await self.client.is_user_authorized():
            me = await self.client.get_me()
            self.log(f">>> Da dang nhap: {me.first_name}")
        else:
            self.log(">>> CHUA DANG NHAP!")
            self.log(">>> Dang gui OTP den " + PHONE)
            await self.client.send_code_request(PHONE)
            self.log(">>> KIEM TRA DIEN THOAI -> Copy ma OTP")
            self.log(">>> Vao Render -> Environment -> Them OTP=ma-cua-ban -> Deploy lai")
            
            otp = os.environ.get('OTP', '')
            if otp:
                try:
                    await self.client.sign_in(PHONE, otp)
                    me = await self.client.get_me()
                    self.log(f">>> Dang nhap OK: {me.first_name}")
                    new_sess = self.client.session.save()
                    self.log(f">>> SESSION_STRING={new_sess}")
                    self.log(">>> COPY DONG TREN VA THEM VAO RENDER ENVIRONMENT")
                except Exception as e:
                    self.log(f">>> Loi OTP: {e}")
                    return
            else:
                return
        
        try:
            ch = await self.client.get_entity(CHANNEL)
            self.log(f">>> Kenh: {ch.title}")
        except:
            self.log(f">>> KHONG TIM THAY KENH: {CHANNEL}")
            return
        
        @self.client.on(events.NewMessage(chats=ch))
        async def on_ch(event):
            try:
                txt = event.message.text or ''
                t = txt.lower()
                
                if any(k in t for k in ['bắt đầu','mở cược','🎮','phiên mới']):
                    self.active = True
                    self.sess += 1
                    self.log(f"🔓 Phien #{self.sess}")
                    
                    if AUTO:
                        await asyncio.sleep(WAIT)
                        if self.active:
                            cmd = f"/{BET_SIDE} {BET_AMOUNT//1000}k" if BET_AMOUNT >= 1000 else f"/{BET_SIDE} {BET_AMOUNT}"
                            try:
                                await self.client.send_message(BOT, cmd)
                                self.log(f"💸 GUI: {cmd}")
                            except FloodWaitError as e:
                                self.log(f"⏳ Flood {e.seconds}s")
                                await asyncio.sleep(e.seconds)
                                try: await self.client.send_message(BOT, cmd)
                                except: pass
                            except Exception as e:
                                self.log(f"Loi: {e}")
                
                elif any(k in t for k in ['kết quả','📝']):
                    self.active = False
                    w = None
                    if re.search(r'tài.*thắng|thắng.*tài', txt, re.I): w = 'T'
                    elif re.search(r'xỉu.*thắng|thắng.*xỉu', txt, re.I): w = 'X'
                    if w:
                        won = w == BET_SIDE
                        if won: self.wins += 1
                        else: self.loss += 1
                        self.log(f"📊 KQ:{w} | {'🎉 THANG' if won else '💔 THUA'} | W:{self.wins} L:{self.loss}")
                
                elif any(k in t for k in ['hết thời gian','đóng cược','⌛']):
                    self.active = False
                    self.log("🔒 Dong phien")
            except: pass
        
        @self.client.on(events.NewMessage(chats=BOT))
        async def on_bot(event):
            try:
                txt = (event.message.text or '').lower()
                if 'cược thành công' in txt: self.log("✅ Cuoc OK")
                elif 'thắng' in txt: self.log("🎉 THANG!")
                elif 'thua' in txt: self.log("💔 THUA!")
            except: pass
        
        self.log(">>> 🚀 TOOL SAN SANG!")
        self.log(f">>> Auto:{AUTO} | Cua:{BET_SIDE} | Tien:{BET_AMOUNT:,}d | Doi:{WAIT}s")
        self.log(">>> CHO PHIEN MOI...")
        
        await self.client.run_until_disconnected()

# ==================== WEB SERVER ====================
def web(tool):
    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header('Content-type','text/html; charset=utf-8')
            self.end_headers()
            logs = '<br>'.join(list(tool.logs)[-30:])
            self.wfile.write(f"""
            <html><head><meta charset="utf-8"><title>Treo Cuoc</title>
            <style>body{{font-family:Arial;background:#0a0a1a;color:#fff;padding:15px}}
            .g{{color:#0f0}}.r{{color:#f44}}</style></head>
            <body><h1>🚀 Treo Cuoc Auto</h1>
            <p>⏱️ {str(datetime.now()-tool.st).split('.')[0]}</p>
            <p>Phien: {tool.sess} | <span class="g">W:{tool.wins}</span> <span class="r">L:{tool.loss}</span></p>
            <p>Auto: <span class="{'g' if AUTO else 'r'}">{'BAT' if AUTO else 'TAT'}</span></p>
            <hr><h3>Logs:</h3><p>{logs}</p></body></html>""".encode())
    port = int(os.environ.get('PORT', 8000))
    HTTPServer(('0.0.0.0', port), H).serve_forever()

if __name__ == '__main__':
    tool = Tool()
    threading.Thread(target=web, args=(tool,), daemon=True).start()
    try: asyncio.run(tool.go())
    except: time.sleep(60)
