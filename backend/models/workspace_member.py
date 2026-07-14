from datetime import datetime, timezone
from extensions import db


class WorkspaceMember(db.Model):
    __tablename__ = "workspace_members"
    __table_args__ = (
        db.UniqueConstraint("workspace_id", "user_id", name="uq_workspace_member"),
    )

    id = db.Column(db.Integer, primary_key=True)
    workspace_id = db.Column(db.Integer, db.ForeignKey("workspaces.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="member")  # owner/admin/member
    joined_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship("User", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "user_id": self.user_id,
            "role": self.role,
            "joined_at": self.joined_at.isoformat(),
            "user": {
                "id": self.user.id,
                "name": self.user.name,
                "email": self.user.email,
            } if self.user else None,
        }
