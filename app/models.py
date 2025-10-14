from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from sqlalchemy.sql import func
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    staff_code = Column(String, index=True)   # mã nhân viên
    hashed_password = Column(String)

class Device(Base):
    __tablename__ = "devices"
    id = Column(Integer, primary_key=True, index=True)
    product_code = Column(String, unique=True, index=True)  # Số lô-Phiên bản-ID
    location = Column(String, nullable=True)
    status = Column(String, default="online")  # online / offline / error
    battery = Column(Integer, default=100)
    last_seen = Column(DateTime, server_default=func.now())

class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer)
    child_id = Column(String, index=True)   # <Giới tính><Tuổi>-<ID>
    timestamp = Column(DateTime, server_default=func.now())
    message = Column(Text)
    emotion_score = Column(Float, default=0.0)
    risk_level = Column(String, default="Low")  # Low / Medium / High
    note = Column(String, nullable=True)
