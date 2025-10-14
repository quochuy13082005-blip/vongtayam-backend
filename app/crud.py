from sqlalchemy.orm import Session
from . import models, auth
from datetime import datetime
from sqlalchemy import func

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def create_user(db: Session, username: str, staff_code: str, password: str):
    u = models.User(
        username=username,
        staff_code=staff_code,
        hashed_password=auth.get_password_hash(password)
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u

def get_or_create_device(db: Session, product_code: str):
    dev = db.query(models.Device).filter(models.Device.product_code == product_code).first()
    if dev:
        return dev
    dev = models.Device(product_code=product_code, last_seen=datetime.utcnow())
    db.add(dev)
    db.commit()
    db.refresh(dev)
    return dev

def save_event(db: Session, product_c
