class DFA:
    """
    A class representing a Deterministic Finite Automaton (DFA).
    """
    
    def __init__(self, states, alphabet, transitions, start_state, accept_states):
        self.states = set(states)
        self.alphabet = set(alphabet)
        self.transitions = transitions
        self.start_state = start_state
        self.accept_states = set(accept_states)
        self.current_state = start_state
        
        # Validate the DFA components
        self._validate()
    
    def _validate(self):
        # Check that start_state is in states
        if self.start_state not in self.states:
            raise ValueError(f"Start state {self.start_state} is not in the set of states.")
        
        # Check that accept_states is a subset of states
        if not self.accept_states.issubset(self.states):
            raise ValueError("Accept states must be a subset of states.")
        
        # Check that transitions are defined for all state-symbol pairs
        for state in self.states:
            for symbol in self.alphabet:
                if (state, symbol) not in self.transitions:
                    raise ValueError(f"Transition not defined for state {state} and symbol {symbol}.")
                if self.transitions[(state, symbol)] not in self.states:
                    raise ValueError(f"Transition for state {state} and symbol {symbol} leads to non-existent state {self.transitions[(state, symbol)]}.")
    
    def reset(self):
        self.current_state = self.start_state
    
    def process_symbol(self, symbol):
        if symbol not in self.alphabet:
            raise ValueError(f"Symbol {symbol} is not in the alphabet.")
        
        self.current_state = self.transitions[(self.current_state, symbol)]
    
    def process_string(self, input_string):
        self.reset()
        
        for symbol in input_string:
            self.process_symbol(symbol)
        
        return self.current_state in self.accept_states
    
    def process_string_with_trace(self, input_string):
        """Process a string and return the sequence of states visited"""
        self.reset()
        
        # Initialize trace with the start state
        trace = [self.current_state]
        
        for symbol in input_string:
            if symbol not in self.alphabet:
                raise ValueError(f"Symbol {symbol} is not in the alphabet.")
            
            self.current_state = self.transitions[(self.current_state, symbol)]
            trace.append(self.current_state)
        
        # Return the trace and whether the string is accepted
        return {
            'trace': trace,
            'accepted': self.current_state in self.accept_states
        }
    
    def get_reachable_states(self):
        reachable = set()
        queue = [self.start_state]
        
        while queue:
            state = queue.pop(0)
            if state not in reachable:
                reachable.add(state)
                for symbol in self.alphabet:
                    next_state = self.transitions[(state, symbol)]
                    if next_state not in reachable:
                        queue.append(next_state)
        
        return reachable
    
    def remove_unreachable_states(self):
        reachable = self.get_reachable_states()
        
        # Filter states and accept_states
        new_states = reachable
        new_accept_states = self.accept_states.intersection(reachable)
        
        # Filter transitions
        new_transitions = {}
        for (state, symbol), next_state in self.transitions.items():
            if state in reachable and next_state in reachable:
                new_transitions[(state, symbol)] = next_state
        
        return DFA(new_states, self.alphabet, new_transitions, self.start_state, new_accept_states)
    
    def to_dict(self):
        # Convert transitions to a format suitable for JSON
        transitions_dict = {}
        for (state, symbol), next_state in self.transitions.items():
            if state not in transitions_dict:
                transitions_dict[state] = {}
            transitions_dict[state][symbol] = next_state
        
        return {
            "states": list(self.states),
            "alphabet": list(self.alphabet),
            "transitions": transitions_dict,
            "start_state": self.start_state,
            "accept_states": list(self.accept_states)
        }
    
    @classmethod
    def from_dict(cls, data):
        states = set(data["states"])
        alphabet = set(data["alphabet"])
        start_state = data["start_state"]
        accept_states = set(data["accept_states"])
        
        # Convert transitions from the JSON format
        transitions = {}
        for state, symbols in data["transitions"].items():
            for symbol, next_state in symbols.items():
                transitions[(state, symbol)] = next_state
        
        return cls(states, alphabet, transitions, start_state, accept_states)