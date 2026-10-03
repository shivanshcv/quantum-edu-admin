"""
Parse assessment bulk-import CSV and replace questions/options for an Assessment.

Expected columns: question_number, question_text, option_order, option_text, is_correct
(see quantum-edu-be/docs/assessments/assessment_import_template.csv).
"""
from __future__ import annotations

import csv
import io
from collections import defaultdict
from typing import BinaryIO

from django.core.exceptions import ValidationError
from django.db import transaction

from .models import Assessment, AssessmentOption, AssessmentQuestion

COL_QUESTION_NUMBER = "question_number"
COL_QUESTION_TEXT = "question_text"
COL_OPTION_ORDER = "option_order"
COL_OPTION_TEXT = "option_text"
COL_IS_CORRECT = "is_correct"

REQUIRED_COLUMNS = (
    COL_QUESTION_NUMBER,
    COL_QUESTION_TEXT,
    COL_OPTION_ORDER,
    COL_OPTION_TEXT,
    COL_IS_CORRECT,
)


def _parse_bool(raw: str) -> bool:
    s = (raw or "").strip().lower()
    if s in ("true", "1", "yes", "y"):
        return True
    if s in ("false", "0", "no", "n"):
        return False
    raise ValidationError(f"Invalid is_correct value: {raw!r} (use true/false or yes/no)")


def _normalize_header(key: str) -> str:
    return (key or "").strip().lower().replace(" ", "_")


def parse_assessment_csv(file_obj: BinaryIO) -> list[dict]:
    """
    Read CSV and return list of row dicts with normalized keys.
    """
    raw = file_obj.read()
    if isinstance(raw, bytes):
        text = raw.decode("utf-8-sig")
    else:
        text = raw
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise ValidationError("CSV has no header row.")

    normalized_map = {_normalize_header(h): h for h in reader.fieldnames if h}
    missing = [c for c in REQUIRED_COLUMNS if c not in normalized_map]
    if missing:
        raise ValidationError(
            "CSV missing required columns: "
            + ", ".join(missing)
            + ". Required: "
            + ", ".join(REQUIRED_COLUMNS)
        )

    rows: list[dict] = []
    for i, row in enumerate(reader, start=2):
        if not row or not any((v or "").strip() for v in row.values()):
            continue
        try:
            qn = int(str(row[normalized_map[COL_QUESTION_NUMBER]]).strip())
            oo = int(str(row[normalized_map[COL_OPTION_ORDER]]).strip())
        except ValueError as e:
            raise ValidationError(f"Row {i}: question_number and option_order must be integers") from e
        qtext = (row[normalized_map[COL_QUESTION_TEXT]] or "").strip()
        otext = (row[normalized_map[COL_OPTION_TEXT]] or "").strip()
        if not qtext or not otext:
            raise ValidationError(f"Row {i}: question_text and option_text must be non-empty")
        is_cor = _parse_bool(row[normalized_map[COL_IS_CORRECT]])
        rows.append(
            {
                COL_QUESTION_NUMBER: qn,
                COL_QUESTION_TEXT: qtext,
                COL_OPTION_ORDER: oo,
                COL_OPTION_TEXT: otext,
                COL_IS_CORRECT: is_cor,
            }
        )
    if not rows:
        raise ValidationError("CSV contains no data rows.")
    return rows


def validate_grouped_rows(rows: list[dict]) -> dict[int, list[dict]]:
    """Group by question_number; ensure exactly one correct option and at least 2 options per question."""
    by_q: dict[int, list[dict]] = defaultdict(list)
    for r in rows:
        by_q[r[COL_QUESTION_NUMBER]].append(r)

    for qn, opts in sorted(by_q.items()):
        if len(opts) < 2:
            raise ValidationError(f"Question {qn}: need at least 2 options, found {len(opts)}")
        orders = [o[COL_OPTION_ORDER] for o in opts]
        if len(orders) != len(set(orders)):
            raise ValidationError(f"Question {qn}: duplicate option_order values")
        correct = [o for o in opts if o[COL_IS_CORRECT]]
        if len(correct) != 1:
            raise ValidationError(
                f"Question {qn}: must have exactly one is_correct=true, found {len(correct)}"
            )
        texts = {o[COL_QUESTION_TEXT] for o in opts}
        if len(texts) != 1:
            raise ValidationError(
                f"Question {qn}: question_text must match on all rows for that question (found {len(texts)} variants)"
            )
    return by_q


@transaction.atomic
def replace_assessment_questions_from_rows(assessment: Assessment, rows: list[dict]) -> tuple[int, int]:
    """
    Delete existing questions (cascade options) and create from validated rows.
    Returns (questions_created, options_created).
    """
    by_q = validate_grouped_rows(rows)
    AssessmentQuestion.objects.filter(assessment=assessment).delete()

    q_created = 0
    o_created = 0
    for qn in sorted(by_q.keys()):
        opts = sorted(by_q[qn], key=lambda x: x[COL_OPTION_ORDER])
        stem = opts[0][COL_QUESTION_TEXT]
        q = AssessmentQuestion.objects.create(assessment=assessment, question_text=stem)
        q_created += 1
        for o in opts:
            AssessmentOption.objects.create(
                question=q,
                option_text=o[COL_OPTION_TEXT],
                is_correct=o[COL_IS_CORRECT],
            )
            o_created += 1
    return q_created, o_created


def replace_assessment_questions_from_csv_file(assessment: Assessment, file_obj: BinaryIO) -> tuple[int, int]:
    rows = parse_assessment_csv(file_obj)
    return replace_assessment_questions_from_rows(assessment, rows)
