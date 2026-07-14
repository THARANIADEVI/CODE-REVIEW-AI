from datetime import datetime, timezone
from extensions import db


class Project(db.Model):
    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    project_name = db.Column(db.String(200), nullable=False)
    upload_type = db.Column(db.String(20), nullable=False)  # file | snippet
    workspace_id = db.Column(db.Integer, db.ForeignKey("workspaces.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    reviews = db.relationship(
        "Review", backref="project", lazy=True, cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "project_name": self.project_name,
            "upload_type": self.upload_type,
            "workspace_id": self.workspace_id,
            "created_at": self.created_at.isoformat(),
        }
