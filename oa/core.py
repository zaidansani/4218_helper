"""
Orthogonal Array (OA) analyser.

Given an array (list of rows / list of lists of ints), determines:
  - N  : number of runs (rows)
  - k  : number of factors (columns)
  - s  : number of symbols (levels) — must be uniform across columns
  - t  : strength (max t such that every t-way combination appears equally often)
  - λ  : index  (λ = N / s^t)
  - OA notation  : OA(N, k, s, t)
  - L notation   : L_N(s^k)
  - validity errors if the array is not a valid OA
"""

from dataclasses import dataclass, field
from itertools import combinations, product
from math import gcd
from functools import reduce


@dataclass
class OAResult:
    # Raw inputs
    array: list          # list[list[int]]
    N: int               # number of rows
    k: int               # number of columns
    symbols: list        # sorted list of distinct symbols found per column
    s: int               # number of levels (None if mixed)
    mixed: bool          # True if columns have different numbers of symbols

    # OA properties (None if array is not a valid OA at any strength)
    strength: int        # maximum verified strength t
    index: float         # λ = N / s^t  (exact if valid)
    oa_notation: str     # OA(N, k, s, t)
    l_notation: str      # L_N(s^k)

    # Validation
    is_valid_oa: bool
    errors: list = field(default_factory=list)
    strength_checks: list = field(default_factory=list)  # list of {t, valid, lambda, detail}


def _symbol_counts(array, k):
    """Return list of sorted unique-symbol sets per column."""
    cols = [sorted(set(row[c] for row in array)) for c in range(k)]
    return cols


def _check_strength(array, N, k, col_symbols, t):
    """
    Check whether the array is OA(N, k, s, t) at strength t.
    Returns (is_valid, lambda_value, detail_string).
    """
    # For each t-subset of columns, count occurrences of each t-tuple
    issues = []
    lambdas = []
    for cols in combinations(range(k), t):
        sym_sets = [col_symbols[c] for c in cols]
        # Only check tuples that are in the Cartesian product of the actual symbols
        counts = {}
        for row in array:
            key = tuple(row[c] for c in cols)
            counts[key] = counts.get(key, 0) + 1

        expected_tuples = list(product(*sym_sets))
        for tup in expected_tuples:
            cnt = counts.get(tup, 0)
            lambdas.append(cnt)
            if cnt == 0:
                issues.append(f"  tuple {tup} in columns {cols} never appears")

        # Check all counts are equal
        unique_counts = set(counts.get(tup, 0) for tup in expected_tuples)
        if len(unique_counts) > 1:
            issues.append(
                f"  columns {cols}: unequal coverage counts {sorted(unique_counts)}"
            )

    if issues:
        return False, None, "\n".join(issues)

    lam = lambdas[0] if lambdas else None
    return True, lam, f"λ = {lam}"


def analyse_oa(array):
    """
    Analyse a user-supplied array for OA properties.

    Parameters
    ----------
    array : list[list[int]]
        The test array, rows x columns.

    Returns
    -------
    OAResult
    """
    if not array or not array[0]:
        return OAResult(
            array=array, N=0, k=0, symbols=[], s=None, mixed=False,
            strength=0, index=None, oa_notation="N/A", l_notation="N/A",
            is_valid_oa=False, errors=["Empty array."],
        )

    N = len(array)
    k = len(array[0])

    # Validate all rows same length
    errors = []
    for i, row in enumerate(array):
        if len(row) != k:
            errors.append(f"Row {i} has {len(row)} columns, expected {k}.")

    col_symbols = _symbol_counts(array, k)
    col_sizes = [len(s) for s in col_symbols]
    mixed = len(set(col_sizes)) > 1
    s = col_sizes[0] if not mixed else None

    if mixed:
        errors.append(
            f"Columns have different numbers of symbols: {col_sizes}. "
            "Mixed-level OAs are not supported by this analyser."
        )

    if errors:
        return OAResult(
            array=array, N=N, k=k, symbols=col_symbols, s=s, mixed=mixed,
            strength=0, index=None, oa_notation="N/A", l_notation="N/A",
            is_valid_oa=False, errors=errors,
        )

    # Check strengths 1 .. k
    strength_checks = []
    max_valid_t = 0
    final_lambda = None

    for t in range(1, k + 1):
        valid, lam, detail = _check_strength(array, N, k, col_symbols, t)
        strength_checks.append({
            "t": t,
            "valid": valid,
            "lambda": lam,
            "detail": detail,
        })
        if valid:
            max_valid_t = t
            final_lambda = lam
        else:
            break  # strength is maximal at max_valid_t

    is_valid_oa = max_valid_t >= 1

    if is_valid_oa:
        oa_notation = f"OA({N}, {k}, {s}, {max_valid_t})"
        l_notation = f"L_{N}({s}^{k})"
    else:
        oa_notation = "Not a valid OA"
        l_notation = "N/A"

    # Sanity-check λ = N / s^t
    if is_valid_oa:
        expected_lam = N / (s ** max_valid_t)
        if abs(expected_lam - final_lambda) > 1e-9:
            errors.append(
                f"Index mismatch: computed λ={final_lambda} but N/s^t = {expected_lam}"
            )

    return OAResult(
        array=array,
        N=N,
        k=k,
        symbols=col_symbols,
        s=s,
        mixed=mixed,
        strength=max_valid_t,
        index=final_lambda,
        oa_notation=oa_notation,
        l_notation=l_notation,
        is_valid_oa=is_valid_oa,
        errors=errors,
        strength_checks=strength_checks,
    )
