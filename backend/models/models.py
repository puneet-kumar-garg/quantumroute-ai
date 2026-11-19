from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.db import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="user")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    optimizations = relationship("OptimizationRecord", back_populates="user")
    sessions = relationship("AuthSession", back_populates="user", cascade="all, delete-orphan")


class AuthSession(Base):
    __tablename__ = "auth_sessions"
    id = Column(String(36), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    user = relationship("User", back_populates="sessions")

class OptimizationRecord(Base):
    __tablename__ = "optimization_records"
    __table_args__ = (
        Index("ix_optimization_records_user_created", "user_id", "created_at"),
        Index("ix_optimization_records_route", "source", "destination"),
    )
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    source = Column(String, nullable=False)
    destination = Column(String, nullable=False)
    vehicle_type = Column(String, nullable=False)
    traffic_density = Column(String, nullable=False)
    weather = Column(String, nullable=False)
    road_condition = Column(String, nullable=False)
    optimization_priority = Column(String, nullable=False)
    quantum_result = Column(JSON)
    dijkstra_result = Column(JSON)
    astar_result = Column(JSON)
    bellman_ford_result = Column(JSON)
    traffic_prediction = Column(JSON)
    nodes = Column(JSON)
    edges = Column(JSON)
    optimization_score = Column(Float, default=0.0)
    objective_value = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    user = relationship("User", back_populates="optimizations")
