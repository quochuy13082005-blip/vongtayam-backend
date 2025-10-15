import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))  # đảm bảo import từ backend
import pydantic_patch_pro

from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from . import models, schemas, database, crud, auth
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import random
from .wsmanager import manager as ws_manager

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="VongTayAm Admin API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # đổi sang domain frontend khi production
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- helper tính score (dùng cho endpoint & seed demo)
def compute_emotion_and_risk(message: str, tone: float, hug_seconds: float):
    tone = tone or 0.5
    hug = min(hug_seconds or 0.0, 10) / 10.0
    base = 0.0
    txt = (message or "").lower()
    if any(w in txt for w in ["sad", "lonely", "tired", "scared", "don't", "don't have", "buồn", "cô đơn"]):
        base -= 0.6
    if any(w in txt for w in ["happy","love","fun","like", "vui", "thích"]):
        base += 0.6
    score = max(min(base*0.6 + (tone-0.5)*0.8 + hug*0.2, 1.0), -1.0)
    risk = "Low"
    if score <= -0.6: risk = "High"
    elif score <= -0.2: risk = "Medium"
    return score, risk

# --- Login
@app.post("/login", response_model=schemas.Token)
def login(data: schemas.LoginIn, db: Session = Depends(get_db)):
    user = crud.get_user_by_username(db, data.username)
    if not user:
        raise HTTPException(status_code=400, detail="Thông tin đăng nhập không chính xác")
    if user.staff_code != data.staff_code:
        raise HTTPException(status_code=400, detail="Thông tin đăng nhập không chính xác")
    if not auth.verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Thông tin đăng nhập không chính xác")
    token = auth.create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}

# --- receive events
@app.post("/api/events")
def receive_event(evt: schemas.EventIn, db: Session = Depends(get_db)):
    score, risk = compute_emotion_and_risk(evt.message, evt.tone_score, evt.hug_seconds)
    e = crud.save_event(db, evt.product_code, evt.child_id, evt.message, score, risk, note=None)
    # broadcast to websockets
    try:
        import asyncio
        import json
        # send basic payload
        msg = {"type":"new_event","device":evt.product_code,"child":evt.child_id,"risk":risk,"score":score, "message": evt.message}
        # best-effort: schedule broadcast
        loop = asyncio.get_event_loop()
        loop.create_task(ws_manager.broadcast(msg))
    except Exception:
        pass
    return {"status":"ok","emotion_score":score,"risk":risk}

# --- admin summary
@app.get("/api/admin/summary")
def get_summary(db: Session = Depends(get_db)):
    days = crud.summary_daily(db, days=14)
    devs = db.query(models.Device).all()
    devs_list = [{"id": d.id, "product_code": d.product_code, "status": d.status, "battery": d.battery, "last_seen": str(d.last_seen), "location": d.location} for d in devs]
    highs = db.query(models.Event).filter(models.Event.risk_level=="High").order_by(models.Event.timestamp.desc()).limit(20).all()
    high_list = [{"device_id": h.device_id, "product_code": (db.query(models.Device).filter(models.Device.id==h.device_id).first().product_code if db.query(models.Device).filter(models.Device.id==h.device_id).first() else None), "child": h.child_id, "risk": h.risk_level, "message": h.message} for h in highs]
    # also include medium risks (recent)
    mediums = db.query(models.Event).filter(models.Event.risk_level=="Medium").order_by(models.Event.timestamp.desc()).limit(20).all()
    med_list = [{"device_id": h.device_id, "product_code": (db.query(models.Device).filter(models.Device.id==h.device_id).first().product_code if db.query(models.Device).filter(models.Device.id==h.device_id).first() else None), "child": h.child_id, "risk": h.risk_level, "message": h.message} for h in mediums]
    riskList = high_list + med_list
    return {"eventsSummary": days, "devices": devs_list, "riskList": riskList}

# --- support endpoint
@app.post("/api/admin/support")
def support_action(payload: dict, db: Session = Depends(get_db)):
    product_code = payload.get("product_code")
    child_id = payload.get("child_id")
    if not product_code or not child_id:
        raise HTTPException(status_code=400, detail="Thiếu product_code hoặc child_id")
    evt = crud.mark_support_processing(db, product_code, child_id)
    # broadcast support action
    import asyncio
    loop = asyncio.get_event_loop()
    loop.create_task(ws_manager.broadcast({"type":"support","product_code":product_code,"child_id":child_id,"note":"Đang xử lý"}))
    return {"status":"processing", "product_code": product_code, "child_id": child_id}

# --- websocket
@app.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # simple pong
            await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)

# --- seed demo on startup (create demo user, devices, events)
@app.on_event("startup")
def seed_demo():
    db = database.SessionLocal()
    if not crud.get_user_by_username(db, "admin"):
        crud.create_user(db, "admin", "STAFF001", "password123")
    # devices
    for i in range(1, 11):
        product_code = f"LO01-V1-ID{i:03d}"
        crud.get_or_create_device(db, product_code)
    # sample messages (bilingual to trigger keywords)
    sample_msgs = ["I feel happy","Tôi vui","I feel sad","Tôi buồn","I am lonely","Tôi cô đơn","I miss family","I'm scared","Mình mệt"]
    devices = db.query(models.Device).all()
    for _ in range(50):
        dev = random.choice(devices)
        msg = random.choice(sample_msgs)
        tone = random.uniform(0.2, 0.9)
        hug = random.choice([0, random.uniform(0.2, 6.0)])
        score, risk = compute_emotion_and_risk(msg, tone, hug)
        crud.save_event(db, dev.product_code, random.choice(["M8-001","F7-002","M10-003","F9-004"]), msg, score, risk, note=None)
    db.close()
