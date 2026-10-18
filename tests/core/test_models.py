from pathlib import Path

import pytest
from pydantic import ValidationError

from synth_ai.core.sound_spec.io import load_json, save_json
from synth_ai.core.sound_spec.models import SoundSpec


def test_spec_is_immutable(lead_spec: SoundSpec) -> None:
    with pytest.raises(ValidationError):
        lead_spec.spec_id = "other"  # type: ignore[misc]
    assert isinstance(lead_spec.hypotheses, tuple)


def test_spec_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        SoundSpec.model_validate({"spec_id": "s", "reference_id": "r", "kronos_cutoff": 50})


def test_spec_rejects_other_schema_version() -> None:
    with pytest.raises(ValidationError):
        SoundSpec.model_validate({"schema_version": "9.9", "spec_id": "s", "reference_id": "r"})


def test_save_and_load(tmp_path: Path, lead_spec: SoundSpec) -> None:
    path = tmp_path / "nested" / "sound_spec.json"
    save_json(lead_spec, path)
    assert load_json(SoundSpec, path) == lead_spec
