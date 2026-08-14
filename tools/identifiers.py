"""Canonical SEIS identifiers migrated from the V3 domain rules."""

from __future__ import annotations

import re
import secrets
import time

GPA_EXAM_RE = re.compile(
    r"^GPA_(TEST|BOOK)_[A-Z]+_[A-Z0-9]+_[0-9]{4}_SEM[12]_(MID|FIN)_G[1-3](?:_[A-Z][A-Z0-9_]*)?$"
)
CSAT_EXAM_RE = re.compile(
    r"^CSAT_(TEST|BOOK)_[A-Z]+(?:_[A-Z0-9]+)?_[0-9]{4}_[A-Z][A-Z0-9_]*_(G[1-3]|GRAD)$"
)
SOURCE_ITEM_RE = re.compile(
    r"^(?P<exam>(?:"
    r"GPA_(?:TEST|BOOK)_[A-Z]+_[A-Z0-9]+_[0-9]{4}_SEM[12]_(?:MID|FIN)_G[1-3](?:_[A-Z][A-Z0-9_]*)?"
    r"|CSAT_(?:TEST|BOOK)_[A-Z]+(?:_[A-Z0-9]+)?_[0-9]{4}_[A-Z][A-Z0-9_]*_(?:G[1-3]|GRAD)"
    r"))_(?P<number>[0-9]{1,3}(?:-[0-9]{1,3})?)$"
)
GENERATION_BATCH_RE = re.compile(
    r"^GEN_(CSAT|MS|UTE|GPA)_[A-Z0-9_]+_[0-9A-HJKMNP-TV-Z]{26}$"
)
GENERATED_ITEM_RE = re.compile(
    r"^(CSAT|MS|UTE|GPA)_GEN_[A-Z0-9_]+_[0-9A-HJKMNP-TV-Z]{26}_[0-9]{3}$"
)
SOURCE_PASSAGE_RE = re.compile(r"^SRC_(?P<item>.+_[0-9]{1,3}(?:-[0-9]{1,3})?)$")

_CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


def _token(value: str, field: str) -> str:
    normalized = value.strip().upper().replace("-", "_")
    if not normalized or not re.fullmatch(r"[A-Z0-9_]+", normalized):
        raise ValueError(f"invalid {field}: {value!r}")
    return normalized


def make_gpa_exam_id(
    *, school: str, year: int, semester: int, period: str, grade: int,
    medium: str = "TEST", publisher: str = "SCHOOL",
    subject: str | None = None,
) -> str:
    if not 1900 <= year <= 9999:
        raise ValueError(f"invalid year: {year}")
    if semester not in (1, 2):
        raise ValueError(f"invalid semester: {semester}")
    if grade not in (1, 2, 3):
        raise ValueError(f"invalid grade: {grade}")
    period = _token(period, "period")
    if period not in {"MID", "FIN"}:
        raise ValueError(f"invalid period: {period}")
    subject_token = f"_{_token(subject, 'subject')}" if subject else ""
    exam_id = (
        f"GPA_{_token(medium, 'medium')}_{_token(publisher, 'publisher')}_"
        f"{_token(school, 'school')}_{year}_SEM{semester}_{period}_G{grade}"
        f"{subject_token}"
    )
    validate_gpa_exam_id(exam_id)
    return exam_id
def make_csat_exam_id(
    *, year: int, series: str, grade: str | int,
    medium: str = "TEST", publisher: str = "OFFICIAL",
    provenance: str | None = None,
) -> str:
    if not 1900 <= year <= 9999:
        raise ValueError(f"invalid year: {year}")
    grade_token = f"G{grade}" if isinstance(grade, int) else _token(grade, "grade")
    if grade_token not in {"G1", "G2", "G3", "GRAD"}:
        raise ValueError(f"invalid grade: {grade}")
    provenance_token = f"_{_token(provenance, 'provenance')}" if provenance else ""
    exam_id = (
        f"CSAT_{_token(medium, 'medium')}_{_token(publisher, 'publisher')}"
        f"{provenance_token}_{year}_{_token(series, 'series')}_{grade_token}"
    )
    validate_csat_exam_id(exam_id)
    return exam_id


def validate_csat_exam_id(value: str) -> str:
    if not CSAT_EXAM_RE.fullmatch(value):
        raise ValueError(f"invalid CSAT exam ID: {value!r}")
    return value


def make_source_item_id(exam_id: str, number: str | int) -> str:
    if not (GPA_EXAM_RE.fullmatch(exam_id) or CSAT_EXAM_RE.fullmatch(exam_id)):
        raise ValueError(f"invalid source exam ID: {exam_id!r}")
    number = str(number)
    if not re.fullmatch(r"[0-9]{1,3}(?:-[0-9]{1,3})?", number):
        raise ValueError(f"invalid item number: {number!r}")
    return f"{exam_id}_{number}"


def validate_gpa_exam_id(value: str) -> str:
    if not GPA_EXAM_RE.fullmatch(value):
        raise ValueError(f"invalid GPA exam ID: {value!r}")
    return value


def validate_source_item_id(value: str, *, exam_id: str | None = None) -> str:
    match = SOURCE_ITEM_RE.fullmatch(value)
    if not match or (exam_id is not None and match.group("exam") != exam_id):
        raise ValueError(f"invalid GPA source item ID: {value!r}")
    return value
def make_source_passage_id(exam_id: str, number: str | int) -> str:
    return f"SRC_{make_source_item_id(exam_id, number)}"


def validate_source_passage_id(value: str) -> str:
    match = SOURCE_PASSAGE_RE.fullmatch(value)
    if not match:
        raise ValueError(f"invalid source passage ID: {value!r}")
    validate_source_item_id(match.group("item"))
    return value


def new_ulid() -> str:
    value = (int(time.time() * 1000) << 80) | secrets.randbits(80)
    chars = []
    for _ in range(26):
        chars.append(_CROCKFORD[value & 31])
        value >>= 5
    return "".join(reversed(chars))


def make_generation_batch_id(*, domain: str, blueprint_key: str, ulid: str | None = None) -> str:
    domain = _token(domain, "domain")
    if domain not in {"CSAT", "MS", "UTE", "GPA"}:
        raise ValueError(f"invalid domain: {domain}")
    ulid = ulid or new_ulid()
    value = f"GEN_{domain}_{_token(blueprint_key, 'blueprint_key')}_{ulid}"
    if not GENERATION_BATCH_RE.fullmatch(value):
        raise ValueError(f"invalid generation batch ID: {value!r}")
    return value


def make_generated_item_id(batch_id: str, sequence: int) -> str:
    match = GENERATION_BATCH_RE.fullmatch(batch_id)
    if not match:
        raise ValueError(f"invalid generation batch ID: {batch_id!r}")
    if not 1 <= sequence <= 999:
        raise ValueError(f"invalid sequence: {sequence}")
    _, domain, remainder = batch_id.split("_", 2)
    value = f"{domain}_GEN_{remainder}_{sequence:03d}"
    if not GENERATED_ITEM_RE.fullmatch(value):
        raise ValueError(f"invalid generated item ID: {value!r}")
    return value
