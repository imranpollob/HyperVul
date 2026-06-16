import json
import re
from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = Path("/home/pollmix/Coding/HyperVul")
OZ_DIR = PROJECT_ROOT / "data" / "external" / "openzeppelin-contracts" / "contracts"

all_sol_files = list(OZ_DIR.glob("**/*.sol"))

# Let's read a few files to see import patterns
sample_files = [
    "mocks/account/AccountMock.sol",
    "mocks/VotesMock.sol",
    "token/ERC20/extensions/ERC20Votes.sol",
    "governance/extensions/GovernorTimelockControl.sol"
]

import_regex = re.compile(r'import\s+(?:(?:\{[^\}]*\}|\*)\s+from\s+)?["\']([^"\']+)["\'];')

for sf_rel in sample_files:
    sf = OZ_DIR / sf_rel
    if not sf.exists():
        print(f"File {sf_rel} does not exist at {sf}")
        continue
    with open(sf, "r", encoding="utf-8", errors="ignore") as fh:
        content = fh.read()
    imports = import_regex.findall(content)
    print(f"\nFile: {sf_rel}")
    print(f"Raw imports found by regex:")
    for imp in imports:
        print(f"  - {imp}")

