"""Read-only audit harness for Tasks 3 & 4. Imports the project's own AST helpers
and runs synthetic Solidity snippets through them. Does NOT touch model/labels/splits."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path("/home/pollmix/Coding/HyperVul/scripts")))
import negative_hyperedge_sampling as nhs


def analyze(source, contract, func):
    parsed = nhs.parse_contracts(source)
    funcs = nhs.resolve_all_functions(contract, parsed)
    if func not in funcs:
        return None
    fnode = funcs[func]
    svars = nhs.resolve_all_state_vars(contract, parsed)
    svtypes = nhs.resolve_all_state_var_types(contract, parsed)
    locals_ = nhs.extract_local_vars(fnode)
    accessed = nhs.find_state_var_accesses(fnode, svars, locals_)
    ext = nhs.find_external_calls_ast(fnode, svtypes, parsed, allow_fallback=False)
    return {
        "state_accessed": accessed,
        "ext_calls": [(e["method"], e["receiver"], e["reason"]) for e in ext],
        "constructable": len(accessed) > 0 and len(ext) > 0,
    }


def show(name, res):
    print(f"\n### {name}")
    if res is None:
        print("  FUNCTION NOT RESOLVED")
        return
    print(f"  state_accessed = {res['state_accessed']}")
    print(f"  ext_calls      = {res['ext_calls']}")
    print(f"  CONSTRUCTABLE  = {res['constructable']}")


# ---- TASK 3: what counts as 'state access' ----
print("=" * 70)
print("TASK 3 — STATE ACCESS DEFINITION")
print("=" * 70)

mapping_write = """
contract C {
    mapping(address => uint256) public balances;
    IERC20 token;
    function withdraw(uint256 amt) external {
        balances[msg.sender] -= amt;
        token.transfer(msg.sender, amt);
    }
}
"""
show("3a. mapping entry write (balances[msg.sender] -= amt)",
     analyze(mapping_write, "C", "withdraw"))

nested_struct = """
contract C {
    struct Info { uint256 amount; uint256 debt; }
    mapping(address => Info) public userInfo;
    IPool pool;
    function poke() external {
        userInfo[msg.sender].amount += 1;
        pool.deposit(1);
    }
}
"""
show("3b. nested struct field write (userInfo[x].amount += 1)",
     analyze(nested_struct, "C", "poke"))

array_elem = """
contract C {
    uint256[] public queue;
    IOracle oracle;
    function pushIt() external {
        queue[0] = oracle.latestAnswer();
    }
}
"""
show("3c. array element write (queue[0] = ...)",
     analyze(array_elem, "C", "pushIt"))

storage_alias = """
contract C {
    struct Info { uint256 amount; }
    mapping(address => Info) userInfo;
    IPool pool;
    function poke() external {
        Info storage s = userInfo[msg.sender];
        s.amount = pool.balanceOf(address(this));
    }
}
"""
show("3d. storage POINTER ALIAS mutation (s.amount=..., s aliases userInfo)",
     analyze(storage_alias, "C", "poke"))


# ---- TASK 4: pattern handling ----
print("\n" + "=" * 70)
print("TASK 4 — PATTERN HANDLING")
print("=" * 70)

modifier_state = """
contract C {
    bool private locked;
    IERC20 token;
    modifier nonReentrant() {
        require(!locked, "reentrant");
        locked = true;
        _;
        locked = false;
    }
    function pull() external nonReentrant {
        token.transfer(msg.sender, 1);
    }
}
"""
show("4a. modifier reads/writes 'locked' — is it in the function's state set?",
     analyze(modifier_state, "C", "pull"))

assembly_call = """
contract C {
    address target;
    uint256 result;
    function lowlevel() external {
        address t = target;
        uint256 r;
        assembly {
            r := call(gas(), t, 0, 0, 0, 0, 0)
        }
        result = r;
    }
}
"""
show("4b. external call inside assembly{} block (Yul call)",
     analyze(assembly_call, "C", "lowlevel"))

inheritance = """
contract Base {
    IVault vault;
    uint256 poolId;
}
contract Child is Base {
    function act() external {
        vault.unlock(abi.encode(poolId));
    }
}
"""
show("4c. inheritance — child uses parent's state var + parent-typed call",
     analyze(inheritance, "Child", "act"))

using_for_lib = """
library SafeMath {
    function add(uint256 a, uint256 b) internal pure returns (uint256) { return a + b; }
}
contract C {
    using SafeMath for uint256;
    uint256 total;
    IERC20 token;
    function go(uint256 x) external {
        total = total.add(x);
        token.transfer(msg.sender, x);
    }
}
"""
show("4d-i. using-for library call with NON-allowlist method (.add)",
     analyze(using_for_lib, "C", "go"))

using_for_lib_collision = """
library TokenLib {
    function deposit(uint256 a) internal pure returns (uint256) { return a + 1; }
}
contract C {
    using TokenLib for uint256;
    uint256 total;
    function go(uint256 x) external {
        total = x.deposit();
    }
}
"""
show("4d-ii. using-for library call whose method name IS in allowlist (.deposit)",
     analyze(using_for_lib_collision, "C", "go"))

multi_call = """
contract C {
    IERC20 token;
    IPool pool;
    function multi() external {
        uint256 b = token.balanceOf(address(this));
        pool.deposit(b);
        token.transfer(msg.sender, b);
    }
}
"""
r = analyze(multi_call, "C", "multi")
show("4e. multiple external calls in one function", r)
if r:
    print(f"  --> {len(r['ext_calls'])} external calls collapse into ONE function's edge")
