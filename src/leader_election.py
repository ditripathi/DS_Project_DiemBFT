import logging

class LeaderElection:
    """
    Leader election module
    """
    def __init__(self, n_validators):  #, window_size,exclude_size,reputation_leaders):
        self.n_validators = n_validators
        self.logger=logging.getLogger('DIEM')
        # self.window_size = window_size
        # self.excluded_size = exclude_size
        # self.reputation_leaders = reputation_leaders

    def elect_reputation_leaders(self, qc):
        pass

    def update_leaders(self, qc):
        """
        Update the leader
        """
        pass

    def get_leader(self, round):
        self.logger.info(f"Get the leader : {round % self.n_validators}")
        return round % self.n_validators
