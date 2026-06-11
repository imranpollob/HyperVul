#!/usr/bin/env python3
"""
HyperVul — FORGE-Curated Positive Hyperedge Feasibility Analysis
=================================================================

5-step pipeline:
  1. Filter to interaction-type vulnerabilities (CWE tree + keyword match)
  2. Extract function-level location references
  3. Check source code for external calls and state variable access
  4. Count constructable positive hyperedges
  5. Show concrete examples
"""

import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------

VFP_VULN_DIR = Path(__file__).resolve().parent.parent / "data" / "FORGE-Curated" / "flatten" / "vfp-vuln"

# CWE codes that define interaction-type vulnerabilities.
# We include the root CWEs and their children as they appear in the CWE tree.
INTERACTION_CWE_ROOTS = {
    "CWE-1265",  # Unintended Reentrant Invocation of Non-reentrant Code via Nested Calls
    "CWE-841",   # Improper Enforcement of Behavioral Workflow
    "CWE-691",   # Insufficient Control Flow Management  
    "CWE-362",   # Concurrent Execution Using Shared Resource with Improper Synchronization
    "CWE-435",   # Improper Interaction Between Multiple Correctly-Behaving Entities
}

# Known children / descendants of the above CWE roots (commonly found in smart contract audits)
INTERACTION_CWE_DESCENDANTS = {
    # CWE-691 descendants
    "CWE-670",   # Always-Incorrect Control Flow Implementation
    "CWE-696",   # Incorrect Behavior Order
    "CWE-835",   # Loop with Unreachable Exit Condition (Infinite Loop)
    "CWE-674",   # Uncontrolled Recursion
    "CWE-834",   # Excessive Iteration
    
    # CWE-362 descendants  
    "CWE-364",   # Signal Handler Race Condition
    "CWE-366",   # Race Condition within a Thread
    "CWE-367",   # Time-of-check Time-of-use (TOCTOU) Race Condition
    "CWE-421",   # Race Condition During Access to Alternate Channel
    
    # CWE-435 descendants
    "CWE-436",   # Interpretation Conflict
    "CWE-437",   # Incomplete Model of Endpoint Features
    "CWE-439",   # Behavioral Change in New Version or Environment
    
    # CWE-1265 is itself a child of CWE-691 and CWE-662
    "CWE-662",   # Improper Synchronization
    "CWE-663",   # Use of a Non-reentrant Function in a Concurrent Context
    "CWE-667",   # Improper Locking
    "CWE-764",   # Multiple Locks of a Critical Resource
    "CWE-765",   # Multiple Unlocks of a Critical Resource
    "CWE-820",   # Missing Synchronization
    "CWE-821",   # Incorrect Synchronization
    "CWE-1058",  # Invocation of Conflicting Primitives
    "CWE-1088",  # Synchronous Access of Remote Resource without Timeout
}

ALL_INTERACTION_CWES = INTERACTION_CWE_ROOTS | INTERACTION_CWE_DESCENDANTS

# Keywords that indicate interaction-type vulnerability (case-insensitive)
INTERACTION_KEYWORDS = [
    r"re-?entrancy",
    r"re-?entrant",
    r"flash[\s-]?loan",
    r"front[\s-]?run(?:ning)?",
    r"sandwich",
    r"cross[\s-]?contract",
    r"callback",
    r"read[\s-]?only[\s-]?re-?entrancy",
    r"reentrancy",  # explicit variant without hyphen
]

INTERACTION_KEYWORD_PATTERN = re.compile(
    "|".join(INTERACTION_KEYWORDS), re.IGNORECASE
)

# ---------------------------------------------------------------------------
# Solidity analysis patterns
# ---------------------------------------------------------------------------

# External call patterns in Solidity
EXTERNAL_CALL_PATTERNS = [
    # Low-level calls
    r'\.call\s*[\({]',
    r'\.delegatecall\s*[\({]',
    r'\.staticcall\s*[\({]',
    r'\.transfer\s*\(',
    r'\.send\s*\(',
    # High-level calls: identifier.function(  — but NOT super.function or this.function on its own
    # We look for patterns like: someVar.someFunction(  where someVar is likely an external contract
    r'(?:IERC20|IERC721|IERC1155|ERC20|token|_token)\w*\.\w+\s*\(',
    # SafeERC20 patterns
    r'\.safeTransfer\s*\(',
    r'\.safeTransferFrom\s*\(',
    r'\.safeApprove\s*\(',
    r'\.safeIncreaseAllowance\s*\(',
    r'\.safeDecreaseAllowance\s*\(',
    # Interface calls (IContract pattern)
    r'I[A-Z]\w+\([^)]*\)\.\w+\s*\(',
    # Common DeFi patterns
    r'uniswap\w*\.\w+\s*\(',
    r'router\w*\.\w+\s*\(',
    r'pool\w*\.\w+\s*\(',
    r'vault\w*\.\w+\s*\(',
    r'oracle\w*\.\w+\s*\(',
    r'strategy\w*\.\w+\s*\(',
    # Generic contract-type variable calls: variable.function( where variable is a state var
    r'\w+\.\w+\s*\{[^}]*\}\s*\(',  # .function{value: X}(
]

EXTERNAL_CALL_RE = re.compile("|".join(EXTERNAL_CALL_PATTERNS), re.IGNORECASE)

# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def load_all_vfps(vfp_dir: Path) -> list[dict]:
    """Load all VFP JSON files."""
    vfps = []
    for f in sorted(vfp_dir.glob("vfp_*.json")):
        with open(f) as fh:
            vfps.append(json.load(fh))
    return vfps


def finding_has_interaction_cwe(finding: dict) -> bool:
    """Check if any CWE in the finding's category tree is an interaction-type CWE."""
    cat = finding.get("category", {})
    for level, cwes in cat.items():
        for cwe in cwes:
            if cwe in ALL_INTERACTION_CWES:
                return True
    return False


def finding_has_interaction_keyword(finding: dict) -> bool:
    """Check if title or description contains interaction-type keywords."""
    text = (finding.get("title", "") + " " + finding.get("description", "")).lower()
    return bool(INTERACTION_KEYWORD_PATTERN.search(text))


def is_interaction_finding(finding: dict) -> bool:
    return finding_has_interaction_cwe(finding) or finding_has_interaction_keyword(finding)


def extract_function_locations(finding: dict) -> list[dict]:
    """
    Extract function-level location references from a finding.
    Returns list of {file, function, line_info} dicts for locations containing '::'.
    """
    locs = []
    for loc_str in finding.get("location", []):
        if "::" in loc_str:
            # Parse: FileName.sol::functionName or FileName.sol::functionName#L123
            parts = loc_str.split("::")
            file_part = parts[0].strip()
            func_and_line = parts[1].strip() if len(parts) > 1 else ""
            
            # Split function name from line reference
            func_name = func_and_line.split("#")[0].strip()
            line_info = func_and_line.split("#")[1].strip() if "#" in func_and_line else None
            
            locs.append({
                "raw": loc_str,
                "file": file_part,
                "function": func_name,
                "line_info": line_info,
            })
    return locs


def extract_function_source(source_code: str, function_name: str) -> str | None:
    """
    Extract a function body from Solidity source code by name.
    Returns the full function text including signature and body, or None.
    """
    if not source_code or not function_name:
        return None
    
    # Try to find the function definition
    # Pattern: function functionName(...)  ... { ... }
    # We need to handle nested braces
    
    # Escape the function name for regex
    escaped_name = re.escape(function_name)
    
    # Find the function signature start
    pattern = rf'function\s+{escaped_name}\s*\('
    match = re.search(pattern, source_code)
    if not match:
        return None
    
    start_idx = match.start()
    
    # Now find the opening brace of the function body
    brace_idx = source_code.find('{', match.end())
    if brace_idx == -1:
        return None
    
    # Count braces to find the matching closing brace
    depth = 1
    i = brace_idx + 1
    while i < len(source_code) and depth > 0:
        if source_code[i] == '{':
            depth += 1
        elif source_code[i] == '}':
            depth -= 1
        i += 1
    
    if depth != 0:
        return None
    
    return source_code[start_idx:i]


def find_external_calls(function_source: str) -> list[str]:
    """Find external call patterns in a function's source code."""
    if not function_source:
        return []
    
    calls = []
    for match in EXTERNAL_CALL_RE.finditer(function_source):
        # Get some context around the match
        start = max(0, match.start() - 40)
        end = min(len(function_source), match.end() + 20)
        context = function_source[start:end].strip()
        # Clean up the context
        context = re.sub(r'\s+', ' ', context)
        calls.append(context)
    
    return calls


def extract_contract_state_variables(source_code: str) -> set[str]:
    """
    Extract state variable names from Solidity source code.
    State variables are declared at contract level (not inside functions).
    """
    if not source_code:
        return set()
    
    state_vars = set()
    
    # We need to find variable declarations at contract level
    # Strategy: find all lines outside of function bodies
    
    # First, find the contract body
    contract_match = re.search(r'contract\s+\w+[^{]*\{', source_code)
    if not contract_match:
        return state_vars
    
    # Track brace depth to identify contract-level declarations
    code = source_code[contract_match.end():]
    depth = 1
    current_line = ""
    in_function = False
    func_depth = 0
    
    i = 0
    while i < len(code) and depth > 0:
        ch = code[i]
        
        if ch == '{':
            depth += 1
            if not in_function and depth == 2:
                # Check if this is a function/modifier/constructor body
                line_before = current_line.strip()
                if re.search(r'(function|modifier|constructor|receive|fallback)\s', line_before) or \
                   line_before.endswith(')') or line_before.endswith('override') or \
                   line_before.endswith('payable') or line_before.endswith('view') or \
                   line_before.endswith('pure') or line_before.endswith('external') or \
                   line_before.endswith('internal') or line_before.endswith('public') or \
                   line_before.endswith('private') or line_before.endswith('returns'):
                    in_function = True
                    func_depth = depth
            current_line = ""
        elif ch == '}':
            depth -= 1
            if in_function and depth < func_depth:
                in_function = False
            current_line = ""
        elif ch == '\n':
            if not in_function and depth == 1:
                # This is a contract-level line — parse for variable declaration
                line = current_line.strip()
                if line and not line.startswith('//') and not line.startswith('*') and not line.startswith('/*'):
                    # Match: type [visibility] [modifier] varName;
                    # or: mapping(...) [visibility] varName;
                    # or: type[] [visibility] varName;
                    
                    # Skip events, errors, modifiers, functions, using, import, struct, enum, constructor
                    skip_keywords = ['event ', 'error ', 'modifier ', 'function ', 'using ', 
                                   'import ', 'struct ', 'enum ', 'constructor', 'receive()',
                                   'fallback()', 'pragma ', 'interface ', 'library ', 'abstract ']
                    if not any(line.startswith(kw) for kw in skip_keywords):
                        # Try to extract variable name
                        # Pattern for simple declarations: type visibility name;
                        var_match = re.search(
                            r'(?:mapping|uint\d*|int\d*|address|bool|bytes\d*|string|'
                            r'I[A-Z]\w+|[A-Z]\w+)\b'  # type
                            r'(?:\s*\([^)]*\))?'  # optional mapping params
                            r'(?:\s*\[\])*'  # optional array brackets
                            r'(?:\s+(?:public|private|internal|external|constant|immutable|override|payable))*'  # modifiers
                            r'\s+(\w+)\s*[;=]',  # variable name followed by ; or =
                            line
                        )
                        if var_match:
                            var_name = var_match.group(1)
                            # Filter out known non-variable names
                            if var_name not in ('returns', 'return', 'if', 'else', 'for', 'while',
                                              'do', 'require', 'emit', 'new', 'delete', 'memory',
                                              'storage', 'calldata', 'override', 'virtual'):
                                state_vars.add(var_name)
            current_line = ""
        else:
            current_line += ch
        
        i += 1
    
    return state_vars


def function_accesses_state_vars(function_source: str, state_vars: set[str]) -> list[str]:
    """
    Check if a function references any of the contract's state variables.
    Returns list of state variables accessed.
    """
    if not function_source or not state_vars:
        return []
    
    accessed = []
    for var in state_vars:
        # Look for the variable name as a whole word in the function body
        # Exclude the function signature parameters
        pattern = rf'\b{re.escape(var)}\b'
        if re.search(pattern, function_source):
            accessed.append(var)
    
    return accessed


# ---------------------------------------------------------------------------
# MAIN ANALYSIS
# ---------------------------------------------------------------------------

def run_analysis():
    print("=" * 80)
    print("HyperVul — FORGE-Curated Positive Hyperedge Feasibility Analysis")
    print("=" * 80)
    
    # Load all VFPs
    vfps = load_all_vfps(VFP_VULN_DIR)
    total_findings = sum(len(v.get("findings", [])) for v in vfps)
    print(f"\nLoaded {len(vfps)} VFPs with {total_findings} total findings.")
    
    # -----------------------------------------------------------------------
    # STEP 1: Filter to interaction-type vulnerabilities
    # -----------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("STEP 1 — Filter to Interaction-Type Vulnerabilities")
    print("=" * 80)
    
    interaction_findings = []  # list of (vfp, finding)
    cwe_match_count = 0
    keyword_match_count = 0
    both_match_count = 0
    severity_counter = Counter()
    vfp_counter = Counter()
    matched_cwes = Counter()
    matched_keywords = Counter()
    
    for vfp in vfps:
        for finding in vfp.get("findings", []):
            has_cwe = finding_has_interaction_cwe(finding)
            has_kw = finding_has_interaction_keyword(finding)
            
            if has_cwe or has_kw:
                interaction_findings.append((vfp, finding))
                severity_counter[finding.get("severity", "Unknown")] += 1
                vfp_counter[vfp["vfp_id"]] += 1
                
                if has_cwe and has_kw:
                    both_match_count += 1
                elif has_cwe:
                    cwe_match_count += 1
                else:
                    keyword_match_count += 1
                
                # Track which CWEs matched
                if has_cwe:
                    cat = finding.get("category", {})
                    for level, cwes in cat.items():
                        for cwe in cwes:
                            if cwe in ALL_INTERACTION_CWES:
                                matched_cwes[cwe] += 1
                
                # Track which keywords matched
                if has_kw:
                    text = (finding.get("title", "") + " " + finding.get("description", ""))
                    for kw_pat in INTERACTION_KEYWORDS:
                        if re.search(kw_pat, text, re.IGNORECASE):
                            matched_keywords[kw_pat] += 1
    
    print(f"\nTotal interaction-type findings: {len(interaction_findings)} / {total_findings}")
    print(f"  Matched by CWE only:    {cwe_match_count}")
    print(f"  Matched by keyword only: {keyword_match_count}")
    print(f"  Matched by both:         {both_match_count}")
    
    print(f"\nDistinct VFPs with interaction findings: {len(vfp_counter)}")
    print("\nTop 20 VFPs by finding count:")
    for vfp_id, count in vfp_counter.most_common(20):
        print(f"  {vfp_id}: {count} findings")
    
    print(f"\nSeverity distribution:")
    for sev, count in severity_counter.most_common():
        print(f"  {sev}: {count}")
    
    print(f"\nMatched CWEs:")
    for cwe, count in matched_cwes.most_common():
        print(f"  {cwe}: {count}")
    
    print(f"\nMatched keywords:")
    for kw, count in matched_keywords.most_common():
        print(f"  {kw}: {count}")
    
    # -----------------------------------------------------------------------
    # STEP 2: Extract function-level locations
    # -----------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("STEP 2 — Extract Function-Level Locations")
    print("=" * 80)
    
    findings_with_func_loc = []
    findings_without_func_loc = []
    
    for vfp, finding in interaction_findings:
        func_locs = extract_function_locations(finding)
        if func_locs:
            findings_with_func_loc.append((vfp, finding, func_locs))
        else:
            findings_without_func_loc.append((vfp, finding))
    
    total_func_locs = sum(len(fl) for _, _, fl in findings_with_func_loc)
    
    print(f"\nFindings with ≥1 function-level location: {len(findings_with_func_loc)}")
    print(f"Findings with zero function-level locations: {len(findings_without_func_loc)}")
    print(f"Total function-level location references: {total_func_locs}")
    
    if findings_without_func_loc:
        print(f"\nSample findings without function-level locations:")
        for vfp, finding in findings_without_func_loc[:5]:
            print(f"  [{vfp['vfp_id']}] {finding.get('title', 'N/A')[:80]}")
            print(f"    Locations: {finding.get('location', [])}")
    
    # -----------------------------------------------------------------------
    # STEP 3: Source code analysis
    # -----------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("STEP 3 — Source Code Analysis (External Calls & State Variables)")
    print("=" * 80)
    
    analysis_results = []
    source_found_count = 0
    source_not_found_count = 0
    has_external_call_count = 0
    has_state_var_count = 0
    has_both_count = 0
    
    for vfp, finding, func_locs in findings_with_func_loc:
        affected_files = vfp.get("affected_files", {})
        
        for loc in func_locs:
            file_key = loc["file"]
            func_name = loc["function"]
            
            # Find the source code for this file
            source_code = affected_files.get(file_key)
            
            if source_code is None:
                # Try matching by basename
                for af_key, af_source in affected_files.items():
                    if af_key.endswith(file_key) or file_key.endswith(af_key):
                        source_code = af_source
                        break
            
            if source_code is None:
                source_not_found_count += 1
                analysis_results.append({
                    "vfp_id": vfp["vfp_id"],
                    "finding_id": finding["id"],
                    "finding_title": finding.get("title", ""),
                    "severity": finding.get("severity", "Unknown"),
                    "file": file_key,
                    "function": func_name,
                    "source_found": False,
                    "function_source": None,
                    "external_calls": [],
                    "state_vars_accessed": [],
                    "has_external_call": False,
                    "has_state_var_access": False,
                    "constructable": False,
                })
                continue
            
            source_found_count += 1
            
            # Extract the function source
            func_source = extract_function_source(source_code, func_name)
            
            # Find external calls
            ext_calls = find_external_calls(func_source) if func_source else []
            
            # Extract state variables from the contract
            state_vars = extract_contract_state_variables(source_code)
            
            # Check if function accesses state variables
            accessed_vars = function_accesses_state_vars(func_source, state_vars) if func_source else []
            
            has_ext = len(ext_calls) > 0
            has_sv = len(accessed_vars) > 0
            
            if has_ext:
                has_external_call_count += 1
            if has_sv:
                has_state_var_count += 1
            if has_ext and has_sv:
                has_both_count += 1
            
            analysis_results.append({
                "vfp_id": vfp["vfp_id"],
                "finding_id": finding["id"],
                "finding_title": finding.get("title", ""),
                "severity": finding.get("severity", "Unknown"),
                "file": file_key,
                "function": func_name,
                "source_found": True,
                "function_source": func_source,
                "function_source_preview": (func_source[:500] + "...") if func_source and len(func_source) > 500 else func_source,
                "external_calls": ext_calls[:10],  # limit for reporting
                "state_vars_accessed": accessed_vars[:20],
                "all_state_vars": sorted(state_vars)[:30],
                "has_external_call": has_ext,
                "has_state_var_access": has_sv,
                "constructable": has_ext and has_sv,
            })
    
    total_locs_analyzed = len(analysis_results)
    print(f"\nTotal function locations analyzed: {total_locs_analyzed}")
    print(f"  Source code found: {source_found_count}")
    print(f"  Source code NOT found: {source_not_found_count}")
    print(f"\nOf those with source code found:")
    print(f"  Has external call pattern: {has_external_call_count}")
    print(f"  Has state variable access: {has_state_var_count}")
    print(f"  Has BOTH (constructable):  {has_both_count}")
    
    # -----------------------------------------------------------------------
    # STEP 4: Count constructable positive hyperedges
    # -----------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("STEP 4 — Constructable Positive Hyperedges")
    print("=" * 80)
    
    constructable = [r for r in analysis_results if r["constructable"]]
    
    # Deduplicate by (vfp_id, finding_id, function) to avoid double-counting
    seen = set()
    unique_constructable = []
    for r in constructable:
        key = (r["vfp_id"], r["finding_id"], r["function"])
        if key not in seen:
            seen.add(key)
            unique_constructable.append(r)
    
    # Also count unique findings that have at least one constructable location
    constructable_finding_keys = set()
    for r in unique_constructable:
        constructable_finding_keys.add((r["vfp_id"], r["finding_id"]))
    
    constructable_vfps = set(r["vfp_id"] for r in unique_constructable)
    
    print(f"\n{'='*60}")
    print(f"  DECISION GATE NUMBER")
    print(f"  Constructable positive hyperedges: {len(unique_constructable)}")
    print(f"{'='*60}")
    print(f"\n  From {len(constructable_finding_keys)} unique findings")
    print(f"  Across {len(constructable_vfps)} unique VFPs")
    
    # Severity distribution of constructable hyperedges
    constr_severity = Counter(r["severity"] for r in unique_constructable)
    print(f"\n  Severity distribution of constructable hyperedges:")
    for sev, count in constr_severity.most_common():
        print(f"    {sev}: {count}")
    
    # -----------------------------------------------------------------------
    # STEP 5: Concrete examples
    # -----------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("STEP 5 — Concrete Examples of Constructable Positive Hyperedges")
    print("=" * 80)
    
    # Pick up to 3 examples with the most detail
    examples = []
    for r in unique_constructable:
        if r["function_source"] and len(r["external_calls"]) > 0 and len(r["state_vars_accessed"]) > 0:
            examples.append(r)
        if len(examples) >= 3:
            break
    
    # If we don't have 3 good ones, pad with whatever we have
    if len(examples) < 3:
        for r in unique_constructable:
            if r not in examples:
                examples.append(r)
            if len(examples) >= 3:
                break
    
    for i, ex in enumerate(examples, 1):
        print(f"\n{'─'*60}")
        print(f"Example {i}")
        print(f"{'─'*60}")
        print(f"VFP ID:        {ex['vfp_id']}")
        print(f"Finding ID:    {ex['finding_id']}")
        print(f"Finding Title: {ex['finding_title']}")
        print(f"Severity:      {ex['severity']}")
        print(f"File:          {ex['file']}")
        print(f"Function:      {ex['function']}")
        print(f"\nFunction Source Code:")
        if ex.get("function_source"):
            # Print first 80 lines
            lines = ex["function_source"].split('\n')
            for line in lines[:80]:
                print(f"  | {line}")
            if len(lines) > 80:
                print(f"  | ... ({len(lines) - 80} more lines)")
        else:
            print("  (not available)")
        
        print(f"\nExternal Call Sites Identified:")
        for call in ex.get("external_calls", []):
            print(f"  → {call}")
        
        print(f"\nState Variables Accessed:")
        for var in ex.get("state_vars_accessed", []):
            print(f"  → {var}")
        
        print(f"\nWhy Constructable:")
        print(f"  ✓ Finding is interaction-type vulnerability")
        print(f"  ✓ Function-level location available: {ex['file']}::{ex['function']}")
        print(f"  ✓ External call detected: {len(ex.get('external_calls', []))} call site(s)")
        print(f"  ✓ State variable access detected: {len(ex.get('state_vars_accessed', []))} variable(s)")
        print(f"  → Positive hyperedge: ({ex['function']}, "
              f"{{{', '.join(ex.get('state_vars_accessed', [])[:3])}}}, "
              f"{ex.get('external_calls', ['?'])[0][:60]})")
    
    # -----------------------------------------------------------------------
    # Summary
    # -----------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("PIPELINE SUMMARY")
    print("=" * 80)
    summary = {
        "step1_total_vfps": len(vfps),
        "step1_total_findings": total_findings,
        "step1_interaction_findings": len(interaction_findings),
        "step1_cwe_only_matches": cwe_match_count,
        "step1_keyword_only_matches": keyword_match_count,
        "step1_both_matches": both_match_count,
        "step1_distinct_vfps_with_interaction": len(vfp_counter),
        "step1_severity_distribution": dict(severity_counter),
        "step2_findings_with_func_loc": len(findings_with_func_loc),
        "step2_findings_without_func_loc": len(findings_without_func_loc),
        "step2_total_func_locations": total_func_locs,
        "step3_source_found": source_found_count,
        "step3_source_not_found": source_not_found_count,
        "step3_has_external_call": has_external_call_count,
        "step3_has_state_var_access": has_state_var_count,
        "step3_has_both": has_both_count,
        "step4_constructable_hyperedges": len(unique_constructable),
        "step4_from_unique_findings": len(constructable_finding_keys),
        "step4_from_unique_vfps": len(constructable_vfps),
        "step4_severity_distribution": dict(constr_severity),
    }
    
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    # Save results
    output_dir = Path(__file__).resolve().parent.parent / "experiments" / "results"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save summary
    with open(output_dir / "forge_hyperedge_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    
    # Save detailed results (without full source code to keep it manageable)
    detailed_output = []
    for r in analysis_results:
        d = dict(r)
        # Remove full source to keep file small
        d.pop("function_source", None)
        detailed_output.append(d)
    
    with open(output_dir / "forge_hyperedge_detailed.json", "w") as f:
        json.dump(detailed_output, f, indent=2)
    
    # Save constructable hyperedges
    constructable_output = []
    for r in unique_constructable:
        constructable_output.append({
            "vfp_id": r["vfp_id"],
            "finding_id": r["finding_id"],
            "finding_title": r["finding_title"],
            "severity": r["severity"],
            "file": r["file"],
            "function": r["function"],
            "external_calls": r.get("external_calls", []),
            "state_vars_accessed": r.get("state_vars_accessed", []),
        })
    
    with open(output_dir / "forge_constructable_hyperedges.json", "w") as f:
        json.dump(constructable_output, f, indent=2)
    
    # Save examples
    examples_output = []
    for ex in examples:
        examples_output.append({
            "vfp_id": ex["vfp_id"],
            "finding_id": ex["finding_id"],
            "finding_title": ex["finding_title"],
            "severity": ex["severity"],
            "file": ex["file"],
            "function": ex["function"],
            "function_source": ex.get("function_source", ""),
            "external_calls": ex.get("external_calls", []),
            "state_vars_accessed": ex.get("state_vars_accessed", []),
        })
    
    with open(output_dir / "forge_hyperedge_examples.json", "w") as f:
        json.dump(examples_output, f, indent=2)
    
    print(f"\n  Results saved to: {output_dir}/")
    print(f"    forge_hyperedge_summary.json")
    print(f"    forge_hyperedge_detailed.json")
    print(f"    forge_constructable_hyperedges.json")
    print(f"    forge_hyperedge_examples.json")
    
    return summary, unique_constructable, examples


if __name__ == "__main__":
    summary, constructable, examples = run_analysis()
