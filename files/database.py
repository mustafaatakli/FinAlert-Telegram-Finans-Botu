from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import config

Base = declarative_base()
engine = create_engine(config.DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)


class User(Base):
    """Kullanıcı tablosu"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    is_active = Column(Boolean, default=True)
    
    # İlişkiler
    portfolios = relationship("Portfolio", back_populates="user", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("TimeNotification", back_populates="user", cascade="all, delete-orphan")


class Portfolio(Base):
    """Portföy tablosu - Kullanıcının varlıkları"""
    __tablename__ = 'portfolios'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    asset_type = Column(String, nullable=False)  # doviz, altin, hisse
    asset_name = Column(String, nullable=False)  # USD, gram_altin, THYAO vb.
    amount = Column(Float, nullable=False)
    purchase_price = Column(Float, nullable=False)
    purchase_date = Column(DateTime, default=datetime.now)
    
    user = relationship("User", back_populates="portfolios")


class Alert(Base):
    """Seviye bazlı uyarılar tablosu"""
    __tablename__ = 'alerts'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    asset_type = Column(String, nullable=False)  # doviz, altin, hisse
    asset_name = Column(String, nullable=False)  # USD, gram_altin, THYAO vb.
    target_price = Column(Float, nullable=False)
    condition = Column(String, nullable=False)  # ustu (üstü), alti (altı)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    triggered_at = Column(DateTime, nullable=True)
    
    user = relationship("User", back_populates="alerts")


class TimeNotification(Base):
    """Zaman bazlı bildirimler tablosu"""
    __tablename__ = 'time_notifications'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    interval = Column(String, nullable=False)  # her_saat, her_4_saat, her_8_saat, gunluk
    asset_types = Column(String, nullable=False)  # virgülle ayrılmış: doviz,altin,hisse
    is_active = Column(Boolean, default=True)
    last_sent = Column(DateTime, nullable=True)
    
    user = relationship("User", back_populates="notifications")


def init_db():
    """Veritabanını başlat"""
    Base.metadata.create_all(engine)
    print("✅ Veritabanı başarıyla oluşturuldu!")


def get_db():
    """Veritabanı oturumu al"""
    db = SessionLocal()
    try:
        return db
    finally:
        pass


if __name__ == '__main__':
    init_db()

