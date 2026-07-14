import json
from datetime import datetime, timezone
from extensions import db


class Review(db.Model):
    __tablename__ = "reviews"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    review_score = db.Column(db.Float, default=0)
    summary = db.Column(db.Text, default="")
    metrics_json = db.Column(db.Text, default="{}")  # complexity/maintainability/loc/etc
    documentation_json = db.Column(db.Text, default="{}")
    source_json = db.Column(db.Text, nullable=True)  # [{filename, content}, ...] original submitted source
    refactored_code = db.Column(db.Text, nullable=True)  # AI auto-refactor: full rewritten source
    refactor_summary = db.Column(db.Text, nullable=True)  # JSON-encoded list of change summaries
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    findings = db.relationship(
        "ReviewFinding", backref="review", lazy=True, cascade="all, delete-orphan"
    )

    @property
    def metrics(self):
        return json.loads(self.metrics_json or "{}")

    @metrics.setter
    def metrics(self, value):
        self.metrics_json = json.dumps(value)

    @property
    def documentation(self):
        return json.loads(self.documentation_json or "{}")

    @documentation.setter
    def documentation(self, value):
        self.documentation_json = json.dumps(value)

    @property
    def source_files(self):
        return json.loads(self.source_json or "[]")

    @source_files.setter
    def source_files(self, value):
        self.source_json = json.dumps(value)

    @property
    def refactor_changes(self):
        return json.loads(self.refactor_summary or "[]")

    @refactor_changes.setter
    def refactor_changes(self, value):
        self.refactor_summary = json.dumps(value)

    def to_dict(self, include_findings=False):
        data = {
            "id": self.id,
            "project_id": self.project_id,
            "project_name": self.project.project_name if self.project else None,
            "review_score": self.review_score,
            "summary": self.summary,
            "metrics": self.metrics,
            "documentation": self.documentation,
            "created_at": self.created_at.isoformat(),
        }
        if include_findings:
            data["findings"] = [f.to_dict() for f in self.findings]
        if self.refactored_code:
            data["refactored_code"] = self.refactored_code
            data["refactor_changes"] = self.refactor_changes
        return data
