from typing import Dict, Set, Tuple, List

from dfa import DFA
from regex_utils import re_union, re_concat, re_star, EMPTY, EPS


def dfa_to_regex_arden(dfa: DFA) -> Dict:
    # Order states deterministically
    states = sorted(list(dfa.states))
    index = {s: i for i, s in enumerate(states)}

    # Build coefficients R_{i,j} and constants C_i
    R: Dict[Tuple[str, str], str] = {}
    C: Dict[str, str] = {}

    # Initialize C_i (epsilon if accepting, else empty)
    for s in states:
        C[s] = EPS if s in dfa.accept_states else EMPTY

    # For each pair, collect union of symbols causing transition i -a-> j
    symbols_to_targets: Dict[Tuple[str, str], List[str]] = {}
    for (s, a), t in dfa.transitions.items():
        key = (s, t)
        symbols_to_targets.setdefault(key, []).append(a)

    for (i_state, j_state), syms in symbols_to_targets.items():
        syms_sorted = sorted(set(str(x) for x in syms))
        coeff = '|'.join(syms_sorted) if len(syms_sorted) > 1 else syms_sorted[0]
        R[(i_state, j_state)] = coeff

    # Elimination order: eliminate all except start_state, from the end
    order = [s for s in states if s != dfa.start_state]

    steps: List[Dict] = []

    for k in order[::-1]:
        Rkk = R.get((k, k), EMPTY)
        star = re_star(Rkk)
        Ck = C.get(k, EMPTY)
        # Prepare snapshot
        step = {
            'eliminate': k,
            'Rkk': Rkk,
            'Rkk_star': star,
        }
        # Update all equations i != k
        new_R: Dict[Tuple[str, str], str] = {}
        new_C: Dict[str, str] = {}
        for i in states:
            if i == k:
                continue
            Rik = R.get((i, k), EMPTY)
            if Rik == EMPTY and C.get(i, EMPTY) == EMPTY:
                # no dependency; still need to carry forward existing R(i, t) where t != k
                pass
            # constants
            const_term = re_concat(re_concat(Rik, star), Ck)
            new_C[i] = re_union([C.get(i, EMPTY), const_term])
            for j in states:
                if j == k:
                    continue
                Rij = R.get((i, j), EMPTY)
                Rkt = R.get((k, j), EMPTY)
                through_k = re_concat(re_concat(Rik, star), Rkt)
                new_R[(i, j)] = re_union([Rij, through_k])
        # Assign back R, C removing rows/cols for k
        for (i, j), val in list(R.items()):
            if i == k or j == k:
                del R[(i, j)]
        R.update({(i, j): v for (i, j), v in new_R.items() if v != EMPTY})
        for i in list(C.keys()):
            if i == k:
                del C[i]
        C.update(new_C)
        steps.append(step)

    s0 = dfa.start_state
    R00 = R.get((s0, s0), EMPTY)
    regex = re_concat(re_star(R00), C.get(s0, EMPTY))

    return {
        'regex': regex,
        'steps': steps,
        'start_state': s0,
    }
