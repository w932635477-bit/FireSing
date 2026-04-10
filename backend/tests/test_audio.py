"""Tests for audio services — chorus detection, mixing, TTS."""

import pytest
from pathlib import Path
from unittest.mock import patch, AsyncMock, MagicMock

from backend.models import Song, Segment, VoiceModel, Output
from backend.services.chorus_service import detect as detect_chorus


class TestChorusDetection:
    def test_detect_repeated_lyrics(self):
        """Segments with repeated text are identified as chorus."""
        segments = [
            MagicMock(id="s1", text="副歌歌词"),
            MagicMock(id="s2", text="主歌A"),
            MagicMock(id="s3", text="副歌歌词"),
            MagicMock(id="s4", text="主歌B"),
        ]
        chorus_ids = detect_chorus(segments)
        assert set(chorus_ids) == {"s1", "s3"}

    def test_detect_no_chorus_vad_fallback(self):
        """VAD segments (unique text) trigger fallback: last ~30% as chorus."""
        segments = [
            MagicMock(id="s1", text="第一句"),
            MagicMock(id="s2", text="第二句"),
            MagicMock(id="s3", text="第三句"),
        ]
        chorus_ids = detect_chorus(segments)
        # VAD fallback: last 1/3 of segments → ["s3"]
        assert chorus_ids == ["s3"]

    def test_detect_all_chorus(self):
        """All segments are chorus when all have same text."""
        segments = [
            MagicMock(id="s1", text="重复歌词"),
            MagicMock(id="s2", text="重复歌词"),
            MagicMock(id="s3", text="重复歌词"),
        ]
        chorus_ids = detect_chorus(segments)
        assert len(chorus_ids) == 3

    def test_detect_empty(self):
        """Empty segment list returns no chorus."""
        assert detect_chorus([]) == []


class TestAudioMixing:
    def test_mix_creates_output(self, db_session, sample_wav):
        """mix_all creates a final wav file and Output record."""
        from backend.services.audio_service import mix_all

        song = Song(
            id="mix_song",
            title="Test",
            original_audio_path=str(sample_wav),
            instrumental_path=str(sample_wav),
            status="mixing",
        )
        db_session.add(song)

        voice = VoiceModel(
            id="mix_voice",
            name="Test",
            model_path=str(sample_wav),
            is_preset=False,
        )
        db_session.add(voice)

        # Create segment with converted vocal
        seg = Segment(
            id="mix_seg",
            song_id="mix_song",
            line_number=1,
            text="Test",
            start_time=0.0,
            end_time=1.0,
            vocal_path=str(sample_wav),
            voice_model_id="mix_voice",
            converted_vocal_path=str(sample_wav),
        )
        db_session.add(seg)
        db_session.commit()

        output = mix_all("mix_song", [], "beginning", db_session)

        assert output.exists()
        assert output.name == "final.wav"

        # Check Output record created
        out_record = db_session.query(Output).filter(
            Output.song_id == "mix_song", Output.format == "audio"
        ).first()
        assert out_record is not None
        assert out_record.file_size > 0
        assert out_record.duration > 0

    def test_mix_with_chorus_boost(self, db_session, sample_wav):
        """Chorus segments get volume boost in the mix."""
        from backend.services.audio_service import mix_all

        song = Song(
            id="chorus_song",
            title="Test",
            original_audio_path=str(sample_wav),
            instrumental_path=str(sample_wav),
            status="mixing",
        )
        db_session.add(song)

        voice = VoiceModel(
            id="chorus_voice",
            name="Test",
            model_path=str(sample_wav),
            is_preset=False,
        )
        db_session.add(voice)

        for i in range(3):
            seg = Segment(
                id=f"chorus_seg_{i}",
                song_id="chorus_song",
                line_number=i + 1,
                text="合唱" if i == 1 else f"主歌{i}",
                start_time=float(i * 0.3),
                end_time=float((i + 1) * 0.3),
                vocal_path=str(sample_wav),
                voice_model_id="chorus_voice",
                converted_vocal_path=str(sample_wav),
            )
            db_session.add(seg)
        db_session.commit()

        # chorus_seg_1 is chorus
        output = mix_all("chorus_song", ["chorus_seg_1"], "beginning", db_session)
        assert output.exists()


class TestTTSGeneration:
    @pytest.mark.asyncio
    async def test_generate_monologue(self, db_session, sample_wav):
        """TTS generates monologue and updates song record."""
        from backend.services.tts_service import generate

        song = Song(
            id="tts_song",
            title="Test",
            original_audio_path=str(sample_wav),
            status="monologue",
        )
        db_session.add(song)
        db_session.commit()

        # Mock edge_tts at the service import level (edge_tts may not be installed)
        mock_communicate = AsyncMock()

        def fake_save(path):
            Path(path).write_bytes(b"fake mp3 data")
        mock_communicate.save = AsyncMock(side_effect=fake_save)

        mock_edge_tts = MagicMock()
        mock_edge_tts.Communicate = MagicMock(return_value=mock_communicate)

        with patch.dict("sys.modules", {"edge_tts": mock_edge_tts}):
            result = await generate("tts_song", "大家好", db_session)

        assert result.exists()
        assert song.monologue_text == "大家好"
        assert song.monologue_audio_path == str(result)
