"""Reference semantic validator for the normative x-seis-invariants in schema.json."""

from collections import Counter
import re


class SeisSemanticError(ValueError):
    """Raised when a SEIS document violates a cross-object invariant."""


def _require_unique(values, label):
    duplicates = sorted(value for value, count in Counter(values).items() if count > 1)
    if duplicates:
        raise SeisSemanticError(f"duplicate {label}: {duplicates}")

_GENERATION_BATCH_RE = re.compile(
    r"^GEN_(CSAT|MS|UTE|GPA)_[A-Z0-9_]+_[0-9A-HJKMNP-TV-Z]{26}$"
)
_SOURCE_PASSAGE_RE = re.compile(r"^SRC_[A-Z0-9_]+_[0-9]{1,3}(?:-[0-9]{1,3})?$")
_UPPER_TOKEN_RE = re.compile(r"^[A-Z0-9_]+$")
_REQUESTED_TYPE_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")
_BATCH_FIELDS = {"batch_id", "blueprint_id", "generated_at"}
_LINEAGE_FIELDS = {
    "origin",
    "generation_batch_id",
    "blueprint_id",
    "source_exam_id",
    "source_passage_id",
    "parent_item_id",
    "requested_type",
    "transform",
}
_GENERATED_LINEAGE_FIELDS = {
    "generation_batch_id",
    "source_exam_id",
    "source_passage_id",
    "parent_item_id",
    "requested_type",
    "transform",
}
_SOURCE_FIELDS = {"id", "role", "sha256", "locator", "origin", "locator_root"}
_SOURCE_ROOTS = {"academy_data", "repository", "csat_sources"}
_SOURCE_LOCATOR_RE = re.compile(
    r"^(?:[A-Za-z0-9][A-Za-z0-9._-]*/)*[A-Za-z0-9][A-Za-z0-9._-]*"
    r"(?:#[A-Za-z0-9][A-Za-z0-9._:-]*)?$"
)


def _validate_source(source):
    unknown = set(source) - _SOURCE_FIELDS
    if unknown:
        raise SeisSemanticError(f"source {source['id']} has unknown fields: {sorted(unknown)}")
    origin = source.get("origin", "extracted")
    if origin not in {"extracted", "generated"}:
        raise SeisSemanticError(f"source {source['id']} has invalid origin")
    locator_root = source.get("locator_root", "academy_data")
    if locator_root not in _SOURCE_ROOTS:
        raise SeisSemanticError(f"source {source['id']} has invalid locator_root")
    if origin == "generated":
        locator = source.get("locator")
        if not isinstance(locator, str) or not _SOURCE_LOCATOR_RE.fullmatch(locator):
            raise SeisSemanticError(
                f"source {source['id']} generated origin requires a machine-readable locator"
            )
_AUXILIARY_FIELDS = {
    "points",
    "difficulty",
    "translation",
    "replacement_pairs",
    "choice_structure",
    "alternative_blocks",
}
_TYPE_SPECIFIC_AUXILIARY = {
    "replacement_pairs": "VOC_REPL",
    "choice_structure": "PAIR_MATCH",
    "alternative_blocks": "VOC_CTX",
}
_REPLACEMENT_PAIR_FIELDS = {"source", "replacement"}
_CHOICE_STRUCTURE_FIELDS = {"kind", "choices"}
_CHOICE_ENTRY_FIELDS = {"label", "concept", "expressions"}
_ALTERNATIVE_BLOCK_FIELDS = {"label", "alternatives"}
_CAPTURE_PROVENANCE_FIELDS = {
    "capture_segment",
    "source_file_id",
    "source_file_ref",
    "legacy_item_id",
}
_BOOK_CLASSIFICATION_FIELDS = {
    "actual_code",
    "exercise_role",
    "subsection_role",
    "semantic_type_review",
    "role_evidence",
    "source_category",
}
_SEMANTIC_REVIEW_FIELDS = {
    "previous_problem_type",
    "reviewed_problem_type",
    "decision",
    "decision_source",
    "confidence",
    "unresolved",
    "answer_unresolved",
}
_SEMANTIC_SOURCE_FIELDS = {"catalog", "evidence", "source_event_type"}
_BOOK_ROLES = {"concept_drill", "example", "hardcore", "practice", "representative_exam"}
_BOOK_SOURCE_CATEGORIES = {"book_authored_or_unspecified", "official_exam_source"}
_UPPER_TYPE_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")
_CAPTURE_SEGMENT_RE = re.compile(r"^P[0-9]{2}$")
_SOURCE_FILE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_SOURCE_FILE_REF_RE = re.compile(r"^P[0-9]{2}/item_[1-9][0-9]*\.json$")
_LEGACY_ITEM_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
_ACTUAL_CODE_RE = re.compile(r"^CODE [0-9]+-[0-9]+$")


def _require_nonempty_string(value, label):
    if not isinstance(value, str) or not value:
        raise SeisSemanticError(f"{label} must be a non-empty string")


def _validate_auxiliary(item):
    if "auxiliary" not in item:
        return
    auxiliary = item["auxiliary"]
    if not isinstance(auxiliary, dict):
        raise SeisSemanticError(f"item {item['id']} auxiliary must be an object")
    unknown = set(auxiliary) - _AUXILIARY_FIELDS
    if unknown:
        raise SeisSemanticError(f"item {item['id']} auxiliary has unknown fields: {sorted(unknown)}")

    if "points" in auxiliary and (
        isinstance(auxiliary["points"], bool)
        or not isinstance(auxiliary["points"], (int, float))
        or auxiliary["points"] < 0
    ):
        raise SeisSemanticError(f"item {item['id']} auxiliary.points must be a non-negative number")
    for field in ("difficulty", "translation"):
        if field in auxiliary:
            _require_nonempty_string(auxiliary[field], f"item {item['id']} auxiliary.{field}")

    for field, required_type in _TYPE_SPECIFIC_AUXILIARY.items():
        if field in auxiliary and item["problem_type"] != required_type:
            raise SeisSemanticError(
                f"item {item['id']} auxiliary.{field} is only valid for {required_type}"
            )

    if "replacement_pairs" in auxiliary:
        pairs = auxiliary["replacement_pairs"]
        if not isinstance(pairs, list) or not pairs:
            raise SeisSemanticError(f"item {item['id']} replacement_pairs must be a non-empty list")
        seen_sources = set()
        for pair in pairs:
            if not isinstance(pair, dict):
                raise SeisSemanticError(f"item {item['id']} replacement_pairs entries must be objects")
            if set(pair) != _REPLACEMENT_PAIR_FIELDS:
                raise SeisSemanticError(f"item {item['id']} replacement_pairs entry has invalid fields")
            _require_nonempty_string(pair["source"], f"item {item['id']} replacement source")
            _require_nonempty_string(
                pair["replacement"], f"item {item['id']} replacement replacement"
            )
            if pair["source"] in seen_sources:
                raise SeisSemanticError(
                    f"item {item['id']} replacement_pairs has duplicate source {pair['source']!r}"
                )
            seen_sources.add(pair["source"])

    if "choice_structure" in auxiliary:
        structure = auxiliary["choice_structure"]
        if not isinstance(structure, dict) or set(structure) != _CHOICE_STRUCTURE_FIELDS:
            raise SeisSemanticError(f"item {item['id']} choice_structure has invalid fields")
        if structure["kind"] != "concept_expression_pairs":
            raise SeisSemanticError(f"item {item['id']} choice_structure has invalid kind")
        choices = structure["choices"]
        if not isinstance(choices, list) or not choices:
            raise SeisSemanticError(f"item {item['id']} choice_structure.choices must be non-empty")
        labels = set()
        for choice in choices:
            if not isinstance(choice, dict) or set(choice) != _CHOICE_ENTRY_FIELDS:
                raise SeisSemanticError(
                    f"item {item['id']} choice_structure choices have invalid fields"
                )
            for field in ("label", "concept"):
                _require_nonempty_string(
                    choice[field], f"item {item['id']} choice_structure.{field}"
                )
            expressions = choice["expressions"]
            if not isinstance(expressions, list) or not expressions:
                raise SeisSemanticError(
                    f"item {item['id']} choice_structure expressions must be non-empty"
                )
            if any(not isinstance(expression, str) or not expression for expression in expressions):
                raise SeisSemanticError(
                    f"item {item['id']} choice_structure expressions must be strings"
                )
            if len(expressions) != len(set(expressions)):
                raise SeisSemanticError(
                    f"item {item['id']} choice_structure expressions must be unique"
                )
            if choice["label"] in labels:
                raise SeisSemanticError(
                    f"item {item['id']} choice_structure has duplicate label {choice['label']!r}"
                )
            labels.add(choice["label"])

    if "alternative_blocks" in auxiliary:
        blocks = auxiliary["alternative_blocks"]
        if not isinstance(blocks, list) or not blocks:
            raise SeisSemanticError(f"item {item['id']} alternative_blocks must be non-empty")
        labels = set()
        for block in blocks:
            if not isinstance(block, dict) or set(block) != _ALTERNATIVE_BLOCK_FIELDS:
                raise SeisSemanticError(
                    f"item {item['id']} alternative_blocks entries have invalid fields"
                )
            if not isinstance(block["label"], str) or not re.fullmatch(r"\([A-Z]\)", block["label"]):
                raise SeisSemanticError(
                    f"item {item['id']} alternative block label is invalid"
                )
            alternatives = block["alternatives"]
            if not isinstance(alternatives, list) or len(alternatives) < 2:
                raise SeisSemanticError(
                    f"item {item['id']} alternative block alternatives need at least two values"
                )
            if any(not isinstance(value, str) or not value for value in alternatives):
                raise SeisSemanticError(
                    f"item {item['id']} alternative block values must be strings"
                )
            if len(alternatives) != len(set(alternatives)):
                raise SeisSemanticError(
                    f"item {item['id']} alternative block values must be unique"
                )
            if block["label"] in labels:
                raise SeisSemanticError(
                    f"item {item['id']} alternative_blocks has duplicate label {block['label']!r}"
                )
            labels.add(block["label"])


def _validate_capture_provenance(item):
    if "capture_provenance" not in item:
        return
    capture = item["capture_provenance"]
    if not isinstance(capture, dict):
        raise SeisSemanticError(f"item {item['id']} capture_provenance must be an object")
    unknown = set(capture) - _CAPTURE_PROVENANCE_FIELDS
    missing = _CAPTURE_PROVENANCE_FIELDS - set(capture)
    if unknown:
        raise SeisSemanticError(
            f"item {item['id']} capture_provenance has unknown fields: {sorted(unknown)}"
        )
    if missing:
        raise SeisSemanticError(
            f"item {item['id']} capture_provenance is missing fields: {sorted(missing)}"
        )
    for field in ("capture_segment", "source_file_id", "source_file_ref", "legacy_item_id"):
        _require_nonempty_string(capture[field], f"item {item['id']} capture_provenance.{field}")
    if not _CAPTURE_SEGMENT_RE.fullmatch(capture["capture_segment"]):
        raise SeisSemanticError(f"item {item['id']} capture_provenance has invalid capture_segment")
    if not _SOURCE_FILE_ID_RE.fullmatch(capture["source_file_id"]):
        raise SeisSemanticError(f"item {item['id']} capture_provenance has invalid source_file_id")
    if not _SOURCE_FILE_REF_RE.fullmatch(capture["source_file_ref"]):
        raise SeisSemanticError(f"item {item['id']} capture_provenance has invalid source_file_ref")
    if not _LEGACY_ITEM_ID_RE.fullmatch(capture["legacy_item_id"]):
        raise SeisSemanticError(f"item {item['id']} capture_provenance has invalid legacy_item_id")
    segment = capture["capture_segment"]
    if not capture["source_file_ref"].startswith(f"{segment}/"):
        raise SeisSemanticError(f"item {item['id']} capture_provenance segment does not match source_file_ref")
    if not capture["source_file_id"].endswith(f"_{segment}"):
        raise SeisSemanticError(f"item {item['id']} capture_provenance segment does not match source_file_id")


def _validate_book_classification(item):
    if "book_classification" not in item:
        return
    classification = item["book_classification"]
    if not isinstance(classification, dict):
        raise SeisSemanticError(f"item {item['id']} book_classification must be an object")
    unknown = set(classification) - _BOOK_CLASSIFICATION_FIELDS
    missing = _BOOK_CLASSIFICATION_FIELDS - set(classification)
    if unknown:
        raise SeisSemanticError(
            f"item {item['id']} book_classification has unknown fields: {sorted(unknown)}"
        )
    if missing:
        raise SeisSemanticError(
            f"item {item['id']} book_classification is missing fields: {sorted(missing)}"
        )
    actual_code = classification["actual_code"]
    if not (
        actual_code == "INTRO"
        or isinstance(actual_code, str) and _ACTUAL_CODE_RE.fullmatch(actual_code)
    ):
        raise SeisSemanticError(f"item {item['id']} book_classification has invalid actual_code")
    for field in ("exercise_role", "subsection_role"):
        if classification[field] not in _BOOK_ROLES:
            raise SeisSemanticError(
                f"item {item['id']} book_classification has invalid {field}"
            )
    _require_nonempty_string(classification["role_evidence"], f"item {item['id']} role_evidence")
    if classification["source_category"] not in _BOOK_SOURCE_CATEGORIES:
        raise SeisSemanticError(f"item {item['id']} book_classification has invalid source_category")

    review = classification["semantic_type_review"]
    if not isinstance(review, dict) or set(review) != _SEMANTIC_REVIEW_FIELDS:
        raise SeisSemanticError(f"item {item['id']} semantic_type_review has invalid fields")
    for field in ("previous_problem_type", "reviewed_problem_type"):
        if not isinstance(review[field], str) or not _UPPER_TYPE_RE.fullmatch(review[field]):
            raise SeisSemanticError(f"item {item['id']} semantic_type_review has invalid {field}")
    if review["decision"] != "preserved_registered_type":
        raise SeisSemanticError(f"item {item['id']} semantic_type_review has invalid decision")
    if review["confidence"] not in {"high", "medium", "low"}:
        raise SeisSemanticError(f"item {item['id']} semantic_type_review has invalid confidence")
    for field in ("unresolved", "answer_unresolved"):
        if not isinstance(review[field], bool):
            raise SeisSemanticError(f"item {item['id']} semantic_type_review.{field} must be boolean")
    source = review["decision_source"]
    if not isinstance(source, dict) or set(source) != _SEMANTIC_SOURCE_FIELDS:
        raise SeisSemanticError(f"item {item['id']} decision_source has invalid fields")
    if source["catalog"] != "catalog/item-types/v1/registered-v3-snapshot.json":
        raise SeisSemanticError(f"item {item['id']} decision_source has invalid catalog")
    evidence = source["evidence"]
    if not isinstance(evidence, list) or not evidence or any(
        not isinstance(value, str) or not value for value in evidence
    ):
        raise SeisSemanticError(f"item {item['id']} decision_source evidence is invalid")
    if not isinstance(source["source_event_type"], str) or not _UPPER_TYPE_RE.fullmatch(
        source["source_event_type"]
    ):
        raise SeisSemanticError(f"item {item['id']} decision_source has invalid source_event_type")
def _validate_batch(exam):
    if "batch" not in exam:
        return
    batch = exam["batch"]
    if not isinstance(batch, dict):
        raise SeisSemanticError("exam.batch must be an object")
    unknown = set(batch) - _BATCH_FIELDS
    if unknown:
        raise SeisSemanticError(f"exam.batch has unknown fields: {sorted(unknown)}")
    missing = _BATCH_FIELDS - set(batch) - {"generated_at"}
    if missing:
        raise SeisSemanticError(f"exam.batch is missing fields: {sorted(missing)}")
    if not isinstance(batch.get("batch_id"), str) or not _GENERATION_BATCH_RE.fullmatch(batch["batch_id"]):
        raise SeisSemanticError("exam.batch.batch_id has invalid format")
    if not isinstance(batch.get("blueprint_id"), str) or not _UPPER_TOKEN_RE.fullmatch(batch["blueprint_id"]):
        raise SeisSemanticError("exam.batch.blueprint_id has invalid format")
    if "generated_at" in batch and not isinstance(batch["generated_at"], str):
        raise SeisSemanticError("exam.batch.generated_at must be a string")


def _validate_lineage(item):
    if "lineage" not in item:
        return
    lineage = item["lineage"]
    if not isinstance(lineage, dict):
        raise SeisSemanticError(f"item {item['id']} lineage must be an object")
    unknown = set(lineage) - _LINEAGE_FIELDS
    if unknown:
        raise SeisSemanticError(f"item {item['id']} lineage has unknown fields: {sorted(unknown)}")
    origin = lineage.get("origin")
    if origin not in {"extracted", "generated"}:
        raise SeisSemanticError(f"item {item['id']} lineage has invalid origin")
    if origin == "generated":
        missing = _GENERATED_LINEAGE_FIELDS - set(lineage)
        if missing:
            raise SeisSemanticError(f"item {item['id']} generated lineage is missing fields: {sorted(missing)}")

    if "generation_batch_id" in lineage and (
        not isinstance(lineage["generation_batch_id"], str)
        or not _GENERATION_BATCH_RE.fullmatch(lineage["generation_batch_id"])
    ):
        raise SeisSemanticError(f"item {item['id']} lineage has invalid generation_batch_id")
    for field in ("blueprint_id", "source_exam_id"):
        if field in lineage and (
            not isinstance(lineage[field], str) or not _UPPER_TOKEN_RE.fullmatch(lineage[field])
        ):
            raise SeisSemanticError(f"item {item['id']} lineage has invalid {field}")
    if "source_passage_id" in lineage and (
        not isinstance(lineage["source_passage_id"], str)
        or not _SOURCE_PASSAGE_RE.fullmatch(lineage["source_passage_id"])
    ):
        raise SeisSemanticError(f"item {item['id']} lineage has invalid source_passage_id")
    if "parent_item_id" in lineage and lineage["parent_item_id"] is not None and (
        not isinstance(lineage["parent_item_id"], str)
        or not _UPPER_TOKEN_RE.fullmatch(lineage["parent_item_id"])
    ):
        raise SeisSemanticError(f"item {item['id']} lineage has invalid parent_item_id")
    if "requested_type" in lineage and (
        not isinstance(lineage["requested_type"], str)
        or not _REQUESTED_TYPE_RE.fullmatch(lineage["requested_type"])
    ):
        raise SeisSemanticError(f"item {item['id']} lineage has invalid requested_type")
    if "transform" in lineage and lineage["transform"] not in {
        "passage_reuse",
        "type_swap",
        "difficulty_shift",
        "novel",
    }:
        raise SeisSemanticError(f"item {item['id']} lineage has invalid transform")

def validate_seis_v1(document):
    """Validate SEIS v1 graph, spans, ownership, answers, and provenance."""
    for source in document["sources"]:
        _validate_source(source)
    source_ids = [source["id"] for source in document["sources"]]
    passage_ids = [passage["id"] for passage in document["passages"]]
    item_ids = [item["id"] for item in document["items"]]
    sources = {source["id"]: source for source in document["sources"]}
    passages = {passage["id"]: passage for passage in document["passages"]}
    items = {item["id"]: item for item in document["items"]}
    _validate_batch(document["exam"])

    _require_unique(source_ids, "source id")
    _require_unique(passage_ids, "passage id")
    _require_unique(item_ids, "item id")
    _require_unique(
        (marker["id"] for passage in document["passages"] for marker in passage["markers"]),
        "marker id",
    )

    def validate_provenance(entries, subject):
        for entry in entries:
            if entry["source_id"] not in sources:
                raise SeisSemanticError(f"{subject} references missing source {entry['source_id']}")

    for passage in document["passages"]:
        validate_provenance(passage["provenance"], passage["id"])
        passage_evidence = {
            (entry["source_id"], entry.get("page")) for entry in passage["provenance"]
        }
        for marker in passage["markers"]:
            owner = items.get(marker["owner_item"])
            if owner is None:
                raise SeisSemanticError(f"marker {marker['id']} has missing owner")
            if passage["id"] not in owner["passage_ids"]:
                raise SeisSemanticError(f"marker {marker['id']} owner does not reference its passage")
            offset = marker["offset"]
            unit = offset["unit"]
            if unit == "unicode_code_point":
                start, end = offset["start"], offset["end"]
                if not 0 <= start < end <= len(passage["text"]):
                    raise SeisSemanticError(f"marker {marker['id']} has invalid text span")
                if passage["text"][start:end] != marker["label"]:
                    raise SeisSemanticError(f"marker {marker['id']} label does not match text span")
            elif unit == "unicode_code_point_anchor":
                if not 0 <= offset["position"] <= len(passage["text"]):
                    raise SeisSemanticError(f"marker {marker['id']} has invalid anchor")
            elif unit == "source_region":
                source_page = (offset["source_id"], offset["page"])
                if source_page not in passage_evidence:
                    raise SeisSemanticError(
                        f"marker {marker['id']} region is not backed by passage provenance"
                    )
                region = offset["region"]
                if region["x"] + region["width"] > 1 or region["y"] + region["height"] > 1:
                    raise SeisSemanticError(f"marker {marker['id']} region exceeds page bounds")

    for item in document["items"]:
        _validate_auxiliary(item)
        _validate_capture_provenance(item)
        _validate_book_classification(item)
        _validate_lineage(item)
        missing = set(item["passage_ids"]) - passages.keys()
        if missing:
            raise SeisSemanticError(f"item {item['id']} references missing passages {sorted(missing)}")
        validate_provenance(item["provenance"], item["id"])
        validate_provenance(item["answer_provenance"], f"{item['id']} answer")
        if any(sources[entry["source_id"]]["role"] != "answer" for entry in item["answer_provenance"]):
            raise SeisSemanticError(f"item {item['id']} answer provenance requires answer source")
        labels = [choice["label"] for choice in item["choices"]]
        _require_unique(labels, f"choice label in {item['id']}")
        answer = item["answer"]
        if answer["form"] == "single" and answer["value"] not in labels:
            raise SeisSemanticError(f"item {item['id']} answer is not a choice label")
        if answer["form"] == "multiple" and not set(answer["values"]) <= set(labels):
            raise SeisSemanticError(f"item {item['id']} answers are not choice labels")
        if answer["form"] == "free_text" and labels:
            raise SeisSemanticError(f"item {item['id']} free-text answer requires zero choices")

    return document
