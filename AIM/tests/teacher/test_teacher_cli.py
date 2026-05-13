# AIM/tests/teacher/test_teacher_cli.py
import pytest
from pathlib import Path
from scripts.teacher_cli import main
import sys


def test_cli_audit_command(monkeypatch, capsys):
    """Test CLI audit command."""
    # Mock sys.argv
    monkeypatch.setattr(sys, "argv", ["teacher_cli.py", "audit", "test_agent"])

    # Should not crash
    try:
        main()
    except SystemExit:
        pass  # Expected for CLI

    captured = capsys.readouterr()
    # Should print something
    assert len(captured.out) > 0 or len(captured.err) > 0


def test_cli_audit_all_command(monkeypatch, capsys):
    """Test CLI audit-all command."""
    monkeypatch.setattr(sys, "argv", ["teacher_cli.py", "audit-all"])

    try:
        main()
    except SystemExit:
        pass

    captured = capsys.readouterr()
    assert len(captured.out) > 0 or len(captured.err) > 0
