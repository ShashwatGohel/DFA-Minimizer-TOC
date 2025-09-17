from typing import Dict, Set, Tuple, List

from dfa import DFA

EPSILON_SYMBOLS = {"ε", "epsilon", "EPS", "e", ""}


class NFA:
    def __init__(
        self,
        states: Set[str],
        alphabet: Set[str],
        transitions: Dict[Tuple[str, str], Set[str]],
        start_state: str,
        accept_states: Set[str],
    ):
        self.states = set(states)
        self.alphabet = set(a for a in alphabet if a not in EPSILON_SYMBOLS)
        self.transitions = transitions  # (state, symbol) -> set(states)
        self.start_state = start_state
        self.accept_states = set(accept_states)
        self._validate()

    def _validate(self) -> None:
        if self.start_state not in self.states:
            raise ValueError(f"Start state {self.start_state} is not in the set of states.")
        if not self.accept_states.issubset(self.states):
            raise ValueError("Accept states must be a subset of states.")
        # Transitions may be partial in NFA; symbols can include epsilon-like
        for (state, symbol), targets in self.transitions.items():
            if state not in self.states:
                raise ValueError(f"Transition from non-existent state: {state}")
            for t in targets:
                if t not in self.states:
                    raise ValueError(f"Transition to non-existent state: {t}")
            if not isinstance(targets, (set, frozenset)):
                raise ValueError("NFA transitions must map to a set of target states")

    @classmethod
    def from_dict(cls, data: Dict) -> "NFA":
        states = set(data["states"]) if isinstance(data.get("states"), list) else set(data.get("states", []))
        alphabet = set(data["alphabet"]) if isinstance(data.get("alphabet"), list) else set(data.get("alphabet", []))
        start_state = data["start_state"]
        accept_states = set(data["accept_states"]) if isinstance(data.get("accept_states"), list) else set()

        transitions: Dict[Tuple[str, str], Set[str]] = {}
        raw = data.get("transitions", {})
        # raw expected: {state: {symbol: [targets...]}}
        for s, sym_map in raw.items():
            for sym, targets in sym_map.items():
                if isinstance(targets, str):
                    # support comma-separated string
                    targets_list = [t.strip() for t in targets.split(',') if t.strip()]
                else:
                    targets_list = list(targets)
                key = (s, sym)
                transitions[key] = set(targets_list)

        return cls(states, alphabet, transitions, start_state, accept_states)

    def epsilon_closure(self, states: Set[str]) -> Set[str]:
        stack = list(states)
        closure = set(states)
        while stack:
            s = stack.pop()
            for eps in EPSILON_SYMBOLS:
                nexts = self.transitions.get((s, eps), set())
                for n in nexts:
                    if n not in closure:
                        closure.add(n)
                        stack.append(n)
        return closure

    def move(self, states: Set[str], symbol: str) -> Set[str]:
        res: Set[str] = set()
        for s in states:
            res.update(self.transitions.get((s, symbol), set()))
        return res

    def to_dfa(self) -> DFA:
        # Subset construction with epsilon-closure
        symbols = sorted(self.alphabet)
        start_set = frozenset(self.epsilon_closure({self.start_state}))
        unmarked: List[frozenset] = [start_set]
        dfa_states: List[frozenset] = [start_set]
        trans: Dict[Tuple[str, str], str] = {}

        def label(subset: frozenset) -> str:
            if not subset:
                return '∅'
            return '{' + ','.join(sorted(subset)) + '}'

        # Collect DFA accept states
        dfa_accept: Set[str] = set()

        # We will add a sink state if needed at the end
        while unmarked:
            S = unmarked.pop(0)
            S_label = label(S)
            # mark accepting if any NFA accept in S
            if any(s in self.accept_states for s in S):
                dfa_accept.add(S_label)
            for a in symbols:
                U = self.epsilon_closure(self.move(set(S), a))
                U_f = frozenset(U)
                U_label = label(U_f)
                trans[(S_label, a)] = U_label
                if U_f not in dfa_states:
                    dfa_states.append(U_f)
                    unmarked.append(U_f)

        # Ensure total DFA by adding sink if any missing
        dfa_state_labels = {label(s) for s in dfa_states}
        sink_needed = False
        for q in list(dfa_state_labels):
            for a in symbols:
                if (q, a) not in trans:
                    sink_needed = True
                    trans[(q, a)] = '∅'
        if sink_needed:
            dfa_state_labels.add('∅')
            for a in symbols:
                trans[('∅', a)] = '∅'

        start_label = label(start_set)
        return DFA(dfa_state_labels, set(symbols), trans, start_label, dfa_accept)
