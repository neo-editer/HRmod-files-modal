import pytest

from modal_routes import normalize_uploaded_file_names


def test_normalize_uploaded_file_names_removes_relative_paths_and_duplicates():
    uploaded = [
        "./downloads/model_a.safetensors",
        "model_a.safetensors",
        "C:/Users/test/Downloads/model_b.safetensors",
        "./downloads/model_c.safetensors",
    ]

    result = normalize_uploaded_file_names(uploaded)

    assert result == ["model_a.safetensors", "model_b.safetensors", "model_c.safetensors"]


def test_normalize_uploaded_file_names_ignores_non_safetensors_entries():
    uploaded = [
        "./downloads/model_a.safetensors",
        "notes.txt",
        "folder/another.safetensors",
    ]

    result = normalize_uploaded_file_names(uploaded)

    assert result == ["model_a.safetensors", "another.safetensors"]
