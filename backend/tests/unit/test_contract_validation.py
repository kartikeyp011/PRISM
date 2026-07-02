"""Contract validation script tests."""

import subprocess
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
VALIDATE_SCRIPT = BACKEND_ROOT / "scripts" / "validate_contract.py"


def test_validate_contract_passes():
    result = subprocess.run(
        [sys.executable, str(VALIDATE_SCRIPT)],
        cwd=str(BACKEND_ROOT),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
