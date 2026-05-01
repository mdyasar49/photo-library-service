from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()


class Photo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(256), nullable=False)
    # server path or S3 key
    filepath = db.Column(db.String(512), nullable=False)
    # publicly accessible URL
    url = db.Column(db.String(512), nullable=False)
    directory = db.Column(db.String(256), default='')
    # store as comma-separated for simplicity
    tags = db.Column(db.String(512), default='')
    description = db.Column(db.Text, default='')
    uploaded_at = db.Column(db.DateTime, server_default=db.func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "filename": self.filename,
            "url": self.url,
            "directory": self.directory,
            "tags": [t.strip() for t in (self.tags or '').split(',') if t.strip()],
            "description": self.description,
            "uploaded_at": self.uploaded_at.isoformat()
        }
