from datetime import datetime

from app.extensions import db


class ChatThread(db.Model):
    __tablename__ = 'chat_threads'
    __table_args__ = (
        db.UniqueConstraint('mentor_id', 'student_id', name='uq_chat_thread_mentor_student'),
        db.Index('ix_chat_thread_mentor_student', 'mentor_id', 'student_id'),
    )

    id = db.Column(db.Integer, primary_key=True)
    mentor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'

    __table_args__ = (
        db.Index('ix_chat_message_read', 'thread_id', 'sender_id', 'read_at'),
    )

    id = db.Column(db.Integer, primary_key=True)
    thread_id = db.Column(db.Integer, db.ForeignKey('chat_threads.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    read_at = db.Column(db.DateTime, nullable=True)
