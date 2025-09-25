"""
Production Database Models for RetailXAI Dashboard
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

Base = declarative_base()

class DraftStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"

class PublishDestination(str, enum.Enum):
    SUBSTACK = "substack"
    LINKEDIN = "linkedin"
    TWITTER = "twitter"

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.VIEWER)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    drafts = relationship("Draft", back_populates="author")
    publish_records = relationship("PublishRecord", back_populates="user")

class Draft(Base):
    __tablename__ = "drafts"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    slug = Column(String(600), unique=True, index=True)
    summary = Column(Text)
    body_md = Column(Text, nullable=False)
    body_html = Column(Text)
    tags = Column(JSON, default=list)
    hero_image_url = Column(String(1000))
    source = Column(String(100))
    source_ref = Column(String(500))
    status = Column(Enum(DraftStatus), default=DraftStatus.DRAFT)
    scores = Column(JSON, default=dict)  # AI analysis scores
    meta = Column(JSON, default=dict)    # Additional metadata
    publish_destinations = Column(JSON, default=list)  # Where to publish
    author_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    author = relationship("User", back_populates="drafts")
    publish_records = relationship("PublishRecord", back_populates="draft")

class PublishRecord(Base):
    __tablename__ = "publish_records"
    
    id = Column(Integer, primary_key=True, index=True)
    draft_id = Column(Integer, ForeignKey("drafts.id"), nullable=False)
    destination = Column(Enum(PublishDestination), nullable=False)
    status = Column(String(50), nullable=False)  # success, failed, pending
    request_data = Column(JSON)
    response_data = Column(JSON)
    external_url = Column(String(1000))
    error_message = Column(Text)
    user_id = Column(Integer, ForeignKey("users.id"))
    attempt = Column(Integer, default=1)
    idempotency_key = Column(String(255), unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    draft = relationship("Draft", back_populates="publish_records")
    user = relationship("User", back_populates="publish_records")

class EndpointCredential(Base):
    __tablename__ = "endpoint_credentials"
    
    id = Column(Integer, primary_key=True, index=True)
    endpoint = Column(Enum(PublishDestination), unique=True, nullable=False)
    client_id = Column(String(500))
    client_secret = Column(String(1000))  # Encrypted
    access_token = Column(Text)  # Encrypted
    refresh_token = Column(Text)  # Encrypted
    expires_at = Column(DateTime(timezone=True))
    scopes = Column(JSON, default=list)
    is_encrypted = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    actor_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String(100), nullable=False)  # create, update, delete, publish
    entity_type = Column(String(50), nullable=False)  # draft, user, credential
    entity_id = Column(Integer)
    before_data = Column(JSON)
    after_data = Column(JSON)
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    actor = relationship("User")

class FeatureFlag(Base):
    __tablename__ = "feature_flags"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False)
    enabled = Column(Boolean, default=False)
    payload = Column(JSON, default=dict)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
