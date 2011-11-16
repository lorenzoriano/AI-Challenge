class FSM(object):
    """
    A simple finite state machine. A state is the name of a class
    method. Transition are handled by the state using the two functions
    transition and transition_delayed. In transition the next method
    is called immediately, while in the delayed the next state will be executed
    at the next step() invocations. 
    step() executes the current state.

    A subclass should implement a log method.
    """
    def __init__(self, state):
        """
        state: the initial state
        """
        self.state = state

    def transition(self, state):
        """
        Transition to state and immediate execution    
        """
        self.state = state
        self.log.info("Next state (immediate) %s", self.state)
        action = getattr(self, state)
        return action()

    def transition_delayed(self, state):
        """
        Transition to state. Execution will be the next turn.    
        """
        self.state = state
        self.log.info("Next state (delayed) %s", self.state)
        return

    def step(self):
        """
        Execute the state the FSM is in.
        """
        action = getattr(self, self.state)
        action()

