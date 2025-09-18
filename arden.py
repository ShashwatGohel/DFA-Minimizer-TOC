from typing import Dict, List, Tuple
from regex_utils import re_union, re_concat, re_star, EMPTY, EPS


def dfa_to_regex_arden(states: List[str],
                       start_state: str,
                       accept_states: List[str],
                       transitions: Dict[Tuple[str, str], str]):
    """
    Convert DFA/NFA to regex using Arden’s Theorem.
    - states: list of state names
    - start_state: the start state
    - accept_states: list of accepting states
    - transitions: dict mapping (state, symbol) -> target_state
    """

    # Sort states deterministically
    states = sorted(states)

    # Coefficients R(i,j) and constants C(i)
    R: Dict[Tuple[str, str], str] = {}
    C: Dict[str, str] = {}

    # Initialize constants: ε if accepting, else ∅
    for s in states:
        C[s] = EPS if s in accept_states else EMPTY

    # Build transition regexes
    symbols_to_targets: Dict[Tuple[str, str], List[str]] = {}
    for (s, a), t in transitions.items():
        key = (s, t)
        symbols_to_targets.setdefault(key, []).append(a)

    for (i_state, j_state), syms in symbols_to_targets.items():
        syms_sorted = sorted(set(str(x) for x in syms))
        coeff = "|".join(syms_sorted) if len(syms_sorted) > 1 else syms_sorted[0]
        R[(i_state, j_state)] = coeff

    # Elimination order: all except start
    order = [s for s in states if s != start_state]

    steps: List[Dict] = []

    # Eliminate states in reverse order
    for k in order[::-1]:
        Rkk = R.get((k, k), EMPTY)
        star = re_star(Rkk)
        Ck = C.get(k, EMPTY)

        step = {
            "eliminate": k,
            "Rkk": Rkk,
            "Rkk*": star,
            "equations_before": (dict(R), dict(C))
        }

        new_R: Dict[Tuple[str, str], str] = {}
        new_C: Dict[str, str] = {}

        for i in states:
            if i == k:
                continue
            Rik = R.get((i, k), EMPTY)
            # update constant part
            const_term = re_concat(re_concat(Rik, star), Ck)
            new_C[i] = re_union([C.get(i, EMPTY), const_term])
            for j in states:
                if j == k:
                    continue
                Rij = R.get((i, j), EMPTY)
                Rkj = R.get((k, j), EMPTY)
                through_k = re_concat(re_concat(Rik, star), Rkj)
                new_R[(i, j)] = re_union([Rij, through_k])

        # remove eliminated state entries
        for (i, j) in list(R.keys()):
            if i == k or j == k:
                del R[(i, j)]
        for i in list(C.keys()):
            if i == k:
                del C[i]

        R.update({(i, j): v for (i, j), v in new_R.items() if v != EMPTY})
        C.update(new_C)

        step["equations_after"] = (dict(R), dict(C))
        steps.append(step)

    # Final regex for start state
    s0 = start_state
    R00 = R.get((s0, s0), EMPTY)
    regex = re_concat(re_star(R00), C.get(s0, EMPTY))

    return {
        "regex": regex,
        "steps": steps,
        "start_state": s0,
    }
