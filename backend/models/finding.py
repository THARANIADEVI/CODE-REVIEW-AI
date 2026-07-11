from extensions import db


class ReviewFinding(db.Model):
    __tablename__ = "review_findings"

    id = db.Column(db.Integer, primary_key=True)
    review_id = db.Column(db.Integer, db.ForeignKey("reviews.id"), nullable=False)
    severity = db.Column(db.String(20), nullable=False)  # critical/high/medium/low/info
    category = db.Column(db.String(40), default="general")  # bug/security/smell/performance/style
    issue = db.Column(db.String(300), nullable=False)
    explanation = db.Column(db.Text, default="")
    suggestion = db.Column(db.Text, default="")
    file_name = db.Column(db.String(255), default="")
    line_number = db.Column(db.Integer, default=0)
    source = db.Column(db.String(20), default="ai")  # pylint/bandit/radon/ai

    def to_dict(self):
        return {
            "id": self.id,
            "review_id": self.review_id,
            "severity": self.severity,
            "category": self.category,
            "issue": self.issue,
            "explanation": self.explanation,
            "suggestion": self.suggestion,
            "file_name": self.file_name,
            "line_number": self.line_number,
            "source": self.source,
        }
