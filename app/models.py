import os
from datetime import datetime
import uuid

# SQLAlchemy Models for PostgreSQL
# Ready to connect to PostgreSQL by setting DATABASE_URL in environment or config
try:
    from flask_sqlalchemy import SQLAlchemy
    db = SQLAlchemy()
except ImportError:
    db = None

if db:
    class User(db.Model):
        __tablename__ = 'users'
        id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
        email = db.Column(db.String(255), unique=True, nullable=False, index=True)
        password_hash = db.Column(db.String(255), nullable=False)
        name = db.Column(db.String(255), nullable=False)
        initials = db.Column(db.String(10), nullable=True)
        storage_quota_bytes = db.Column(db.BigInteger, default=20 * 1024 * 1024 * 1024)
        created_at = db.Column(db.DateTime, default=datetime.utcnow)

        files = db.relationship('FileItem', backref='owner', lazy=True, cascade="all, delete-orphan")

    class FileItem(db.Model):
        __tablename__ = 'file_items'
        id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
        user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
        parent_id = db.Column(db.String(36), db.ForeignKey('file_items.id'), nullable=True, index=True)
        name = db.Column(db.String(255), nullable=False)
        saved_name = db.Column(db.String(255), nullable=True)
        file_type = db.Column(db.String(50), nullable=False, default='file')
        size_bytes = db.Column(db.BigInteger, default=0)
        is_folder = db.Column(db.Boolean, default=False)
        starred = db.Column(db.Boolean, default=False)
        trashed = db.Column(db.Boolean, default=False)
        shared = db.Column(db.Boolean, default=False)
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
        updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

        children = db.relationship('FileItem', backref=db.backref('parent', remote_side=[id]), lazy=True)
        shares = db.relationship('ShareLink', backref='file_item', lazy=True, cascade="all, delete-orphan")

    class ShareLink(db.Model):
        __tablename__ = 'share_links'
        id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
        file_id = db.Column(db.String(36), db.ForeignKey('file_items.id'), nullable=False)
        token = db.Column(db.String(64), unique=True, nullable=False, index=True)
        permission = db.Column(db.String(20), default='view')  # 'view' | 'download'
        expires_at = db.Column(db.DateTime, nullable=True)
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
