"""Tests for voice model upload validation."""

import io
import pytest


def _make_fake_pth(size_bytes: int = 20) -> bytes:
    """Create a fake .pth file of given size."""
    return b"fake pth model data" + b"\x00" * max(0, size_bytes - 19)


class TestVoiceUploadValidation:
    """Test that upload_voice rejects invalid model files."""

    def test_rejects_small_file(self, client):
        """Files under 10MB should be rejected with clear error."""
        fake_pth = _make_fake_pth(100)
        resp = client.post(
            "/api/voices",
            files={"pth_file": ("model.pth", fake_pth, "application/octet-stream")},
            data={"name": "Fake Voice"},
        )
        assert resp.status_code == 400
        assert "too small" in resp.json()["detail"].lower()

    def test_rejects_non_pth_extension(self, client):
        """Files without .pth extension should be rejected."""
        # Need a file large enough to pass size check but wrong extension
        resp = client.post(
            "/api/voices",
            files={"pth_file": ("model.bin", b"x" * 100, "application/octet-stream")},
            data={"name": "Wrong Ext"},
        )
        assert resp.status_code == 400
        assert ".pth" in resp.json()["detail"]

    def test_rejects_corrupted_large_file(self, client):
        """A large file that isn't a valid PyTorch checkpoint should be rejected."""
        # Create a 11MB file of random data (passes size check, fails torch.load)
        fake_large = b"\x00" * (11 * 1024 * 1024)
        resp = client.post(
            "/api/voices",
            files={"pth_file": ("model.pth", fake_large, "application/octet-stream")},
            data={"name": "Corrupted"},
        )
        assert resp.status_code == 400
        assert "not a valid" in resp.json()["detail"].lower()
