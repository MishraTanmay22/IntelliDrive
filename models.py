import os
from datetime import datetime
import uuid
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def format_size(size_bytes):
    if size_bytes == 0:
        return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}" if unit != 'B' else f"{int(size_bytes)} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    initials = db.Column(db.String(10), nullable=True)
    storage_quota_bytes = db.Column(db.BigInteger, default=2 * 1024 * 1024 * 1024) # 2 GB
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
    share_token = db.Column(db.String(64), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    children = db.relationship('FileItem', backref=db.backref('parent', remote_side=[id]), lazy=True)
    shares = db.relationship('ShareLink', backref='file_item', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "saved_name": self.saved_name,
            "type": self.file_type,
            "size_bytes": self.size_bytes or 0,
            "size_formatted": "Folder" if self.is_folder else format_size(self.size_bytes or 0),
            "created_at": self.created_at.isoformat() if self.created_at else "",
            "date_formatted": self.created_at.strftime("%b %d, %Y") if self.created_at else "",
            "starred": bool(self.starred),
            "trashed": bool(self.trashed),
            "shared": bool(self.shared),
            "share_token": self.share_token,
            "parent_id": self.parent_id,
            "is_folder": bool(self.is_folder),
            "download_url": f"/api/download/{self.id}" if not self.is_folder else None,
            "view_url": f"/api/view/{self.id}" if not self.is_folder else None
        }

class ShareLink(db.Model):
    __tablename__ = 'share_links'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    file_id = db.Column(db.String(36), db.ForeignKey('file_items.id'), nullable=False)
    token = db.Column(db.String(64), unique=True, nullable=False, index=True)
    permission = db.Column(db.String(20), default='view')  # 'view' | 'download'
    expires_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
