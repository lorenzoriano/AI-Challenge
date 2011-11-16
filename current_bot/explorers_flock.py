import aggregator
import fsm

class ExplorerFlock(aggregator.Aggregator, fsm.FSM):
    """
    An Aggregator that tries first to cluster the belonging
    ants, then move them towards the closes enemy.
    """

    def __init__(self, leader, antlist):
        """
        Parameters:
    
        leader: the ants on which many computations might be based.
        antlist: a list of ants to add to this aggregator
    
        """
        aggregator.Aggregator(self, leader, antlist)
        fsm.FSM(self, "group")
