"""
Mixed Orthogonal Array (MOA) analyser.

A Mixed OA (also called an asymmetric or mixed-level OA) is an N×k array whose
columns are drawn from potentially *different* symbol alphabets.  It is written

    OA_λ(N; s_1^k_1 · s_2^k_2 · … · s_m^k_m, t)

where the first k_1 columns each have s_1 symbols, the next k_2 columns each
have s_2 symbols, etc.

Given:
  - N         : number of runs (rows)
  - groups    : list of (s_i, k_i) pairs   e.g. [(2,3), (3,2)]
  - t         : desired strength

The analyser:
  1. Validates basic structure (row count, column counts, symbol uniformity
     within each group).
  2. Checks every t-subset of columns: each t-tuple of the Cartesian product
     of the chosen columns' symbol sets must appear equally often (λ times).
  3. Reports the maximum verified strength, index λ, and the MOA notation.
"""

from dataclasses import dataclass, field
from itertools import combinations, product


@dataclass
class MOAResult:
    # ── Raw inputs ────────────────────────────────────────────────────────────
    array: list            # list[list[int]]
    N: int                 # number of rows
    k: int                 # total number of columns
    groups: list           # [(s_i, k_i), …]  as supplied by caller
    t_requested: int       # strength requested by caller

    # ── Per-column metadata ───────────────────────────────────────────────────
    col_symbols: list      # list[list[int]]  — sorted distinct symbols per col
    col_s: list            # list[int]        — symbol count per column

    # ── Result ────────────────────────────────────────────────────────────────
    strength: int          # maximum verified strength (0 if none)
    index: float | None    # λ at max verified strength (None if invalid)
    moa_notation: str      # e.g. "OA_1(8; 2^4 · 3^2, 2)"
    is_valid_moa: bool
    errors: list = field(default_factory=list)
    strength_checks: list = field(default_factory=list)
    # each entry: {t, valid, lambda, detail}


# ── Internal helpers ──────────────────────────────────────────────────────────

def _check_strength(array, k, col_symbols, t):
    """
    Check whether the array satisfies the MOA condition at strength t.

    For every t-subset of columns the multiset of t-tuples observed across all
    rows must be uniform (every element of the Cartesian product of those
    columns' symbol sets appears the same number of times).

    Returns (is_valid, lambda_value, detail_string).
    """
    issues = []
    first_lambda = None

    for cols in combinations(range(k), t):
        sym_sets = [col_symbols[c] for c in cols]
        expected = list(product(*sym_sets))

        # Count observed tuples
        counts: dict = {}
        for row in array:
            key = tuple(row[c] for c in cols)
            counts[key] = counts.get(key, 0) + 1

        observed_counts = [counts.get(tup, 0) for tup in expected]
        unique = set(observed_counts)

        # Any expected tuple never seen?
        for tup, cnt in zip(expected, observed_counts):
            if cnt == 0:
                issues.append(f"  tuple {tup} in columns {cols} never appears")

        if len(unique) > 1:
            issues.append(
                f"  columns {cols}: unequal coverage counts {sorted(unique)}"
            )
        else:
            lam = observed_counts[0] if observed_counts else None
            if first_lambda is None:
                first_lambda = lam
            elif lam != first_lambda:
                # λ differs across column-subsets — technically still a valid
                # MOA per-subset, but not a uniform index; flag it.
                issues.append(
                    f"  columns {cols}: λ={lam} differs from earlier λ={first_lambda}"
                )

    if issues:
        return False, None, "\n".join(issues)

    return True, first_lambda, f"λ = {first_lambda}"


def _build_notation(N, groups, t, lam):
    """Return the MOA notation string, e.g. OA_1(8; 2^4 · 3^2, 2)."""
    lam_str = "" if lam == 1 else f"_{lam}"
    group_str = " · ".join(f"{s}^{k}" for s, k in groups)
    return f"OA{lam_str}({N}; {group_str}, {t})"


# ── Public API ────────────────────────────────────────────────────────────────

def analyse_moa(array, groups, t_requested):
    """
    Analyse a user-supplied array for Mixed OA properties.

    Parameters
    ----------
    array      : list[list[int]]
        The test array (rows × columns).  Symbols should be integers ≥ 1.
    groups     : list of (s, k) pairs
        Each pair says "k columns with s symbols each".
        Total columns implied must equal len(array[0]).
    t_requested: int
        The strength to verify up to.

    Returns
    -------
    MOAResult
    """
    errors = []

    # ── Basic structural checks ───────────────────────────────────────────────
    if not array or not array[0]:
        return MOAResult(
            array=array, N=0, k=0, groups=groups, t_requested=t_requested,
            col_symbols=[], col_s=[],
            strength=0, index=None, moa_notation="N/A",
            is_valid_moa=False, errors=["Empty array."],
        )

    N = len(array)
    k_expected = sum(ki for _, ki in groups)
    k_actual   = len(array[0])

    if k_actual != k_expected:
        errors.append(
            f"Column count mismatch: groups imply {k_expected} columns but "
            f"array has {k_actual}."
        )

    # Validate row lengths
    for i, row in enumerate(array):
        if len(row) != k_actual:
            errors.append(f"Row {i} has {len(row)} columns, expected {k_actual}.")

    k = k_actual  # use actual width for the rest

    # ── Per-column symbol analysis ────────────────────────────────────────────
    col_symbols = [sorted(set(row[c] for row in array)) for c in range(k)]
    col_s       = [len(sym) for sym in col_symbols]

    # Build the expected s per column from groups
    expected_s_per_col = []
    for s_i, k_i in groups:
        expected_s_per_col.extend([s_i] * k_i)

    if len(expected_s_per_col) == k:
        for c, (exp_s, obs_s) in enumerate(zip(expected_s_per_col, col_s)):
            if obs_s != exp_s:
                errors.append(
                    f"Column {c}: expected {exp_s} distinct symbols "
                    f"(from group spec), found {obs_s}."
                )

    if t_requested < 1:
        errors.append("Strength t must be at least 1.")
    if t_requested > k:
        errors.append(f"Strength t={t_requested} exceeds number of columns k={k}.")

    if errors:
        return MOAResult(
            array=array, N=N, k=k, groups=groups, t_requested=t_requested,
            col_symbols=col_symbols, col_s=col_s,
            strength=0, index=None, moa_notation="N/A",
            is_valid_moa=False, errors=errors,
        )

    # ── Strength checks ───────────────────────────────────────────────────────
    strength_checks = []
    max_valid_t = 0
    final_lambda = None
    t_limit = min(t_requested, k)

    for t in range(1, t_limit + 1):
        valid, lam, detail = _check_strength(array, k, col_symbols, t)
        strength_checks.append({"t": t, "valid": valid, "lambda": lam, "detail": detail})
        if valid:
            max_valid_t = t
            final_lambda = lam
        else:
            break  # strength is maximal at max_valid_t

    is_valid_moa = max_valid_t >= 1

    if is_valid_moa:
        moa_notation = _build_notation(N, groups, max_valid_t, final_lambda)
    else:
        moa_notation = "Not a valid MOA"

    return MOAResult(
        array=array,
        N=N,
        k=k,
        groups=groups,
        t_requested=t_requested,
        col_symbols=col_symbols,
        col_s=col_s,
        strength=max_valid_t,
        index=final_lambda,
        moa_notation=moa_notation,
        is_valid_moa=is_valid_moa,
        errors=errors,
        strength_checks=strength_checks,
    )
