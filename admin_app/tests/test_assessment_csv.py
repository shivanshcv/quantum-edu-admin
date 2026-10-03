"""Unit tests for assessment CSV parsing (no DB)."""
from io import BytesIO

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from admin_app.assessment_csv import parse_assessment_csv, validate_grouped_rows


class AssessmentCsvParseTests(SimpleTestCase):
    def test_parse_and_validate_minimal(self):
        raw = (
            b"question_number,question_text,option_order,option_text,is_correct\r\n"
            b'1,"Stem?",1,"Wrong",false\r\n'
            b'1,"Stem?",2,"Right",true\r\n'
        )
        rows = parse_assessment_csv(BytesIO(raw))
        self.assertEqual(len(rows), 2)
        validate_grouped_rows(rows)

    def test_rejects_missing_correct(self):
        raw = (
            b"question_number,question_text,option_order,option_text,is_correct\n"
            b'1,"Q",1,"A",false\n'
            b'1,"Q",2,"B",false\n'
        )
        rows = parse_assessment_csv(BytesIO(raw))
        with self.assertRaises(ValidationError):
            validate_grouped_rows(rows)

    def test_header_case_insensitive(self):
        raw = (
            b"Question Number,Question Text,Option Order,Option Text,Is Correct\n"
            b'1,"Q",1,"A",false\n'
            b'1,"Q",2,"B",true\n'
        )
        rows = parse_assessment_csv(BytesIO(raw))
        validate_grouped_rows(rows)
