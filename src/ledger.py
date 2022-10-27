from typing import Dict, List
from collections import deque
from dataclasses import dataclass
# from tempfile import TemporaryFile

# from src.block import Block
from src.crypto import hasher
from src.genesys import initialize_block_and_state
import logging

class NoopTxnEngine:
    """
    Calculates new state as I(txns) where I is identity function and 
    state_id as Hash(prev_state + txns).
    """
    
    @staticmethod
    def execute_transactions(prev_state, block_id, txns: str):
        # state: identity
        # state = txns
        # TODO: Hash
        if not prev_state:
            state_id = hasher(txns)
        else:
            state_id = hasher(prev_state.state_id, txns)
        # don't modify tree here
        return State(state_id, txns, None, block_id)


@dataclass
class State:
    # parent
    # state
    state_id: str
    state_value: str
    parent: 'State'
    block_id: str
    children: List['State'] = None

    @staticmethod
    def pprint(s: 'State'):
        return f'{s.state_id}||{s.state_value}||{s.parent.state_id}\n'


class SpeculationTree:
    def __init__(self, root) -> None:
        # when starting out, put root as genesys
        assert root.parent == None
        self._root: State = root
        self._ids_to_state: Dict[str, State] = {}
        self._ids_to_state = self.make_ids_to_state_from_root(root)
        self.logger=logging.getLogger('DIEM')

    def add_node(self, prev_state, state):
        self.logger.info(f"Node with state {state} is getting added to parent with state {prev_state}")
        self._ids_to_state[state.block_id] = state
        if not prev_state.children:
            prev_state.children = []
        prev_state.children.append(state)
        state.parent = prev_state

    def get_state_by_block_id(self, block_id):
        self.logger.info(f"Get State by block id {block_id}")
        return self._ids_to_state[block_id]

    def make_ids_to_state_from_root(self, root):
        # bfs on root
        dq = deque([root])
        hm = {}
        while len(dq):
            node = dq.popleft()
            hm[node.block_id] = node
            print(f'Added {node.block_id} in _ids_to_state')
            if node.children:
                dq.extend(node.children)
        return hm


class Ledger:
    _speculation_tree: 'SpeculationTree'
    _ledger_file_name: str
    _committed_states: Dict['str', 'State'] = {}

    def __init__(self, root=None, ledger_file_name='ledgers/ledger.log', 
    n_validators=None, log=True) -> None:
        # TODO: if file exists read the last line
        # create genesys state
        self.log = log
        if not root:
            # genesys
            # root = State('42', '42', None, 'GENESYS', []) # Meaning of life, 
            # universe and everything
            assert n_validators != None
            bs1, bs2, bs3 = initialize_block_and_state(n_validators)
            root = bs1[1]
        self._ledger_file_name = ledger_file_name
        if not ledger_file_name:
            self._ledger_file_name = 'ledgers/ledger.log'
        # self._ledger = TemporaryFile('a+')
        # self._ledger = open('ledger.log', 'a+')
        self._speculation_tree = SpeculationTree(root)
        self._committed_states[root.block_id] = root
        self.logger=logging.getLogger('DIEM')

    def speculate(self, prev_block_id: int, block_id: int, txns: str):
        self.logger.info(f"Speculate the new transaction")
        prev_state = self._speculation_tree.get_state_by_block_id(prev_block_id)
        new_state = NoopTxnEngine.execute_transactions(prev_state, block_id, txns)
        self._speculation_tree.add_node(prev_state, new_state)
        self.logger.info(new_state.state_id)
        return new_state.state_id

    def commit(self, block_id) -> 'State':
        self.logger.info(f"Commit the block id: {block_id}")
        # keep looping until parent == null'
        state = self._speculation_tree.get_state_by_block_id(block_id)
        print("ledger.commit", state)
        if not state:
            return
        self._committed_states[block_id] = state
        # print("all nodes", self._speculation_tree._ids_to_state)
        nodes_pending_commit = []
        node = state
        while node.parent != None:
            nodes_pending_commit.append(node)
            node = node.parent
        nodes_pending_commit = nodes_pending_commit[::-1]
        if len(nodes_pending_commit) > 0:
            # TODO: Write nodes to file
            # self._ledger.writelines(list(map(str, nodes_pending_commit)))
            if self.log:
                with open(self._ledger_file_name, 'a+') as f:
                    f.writelines(list(map(State.pprint, nodes_pending_commit)))
            # prune other branches
            new_root = nodes_pending_commit[0]
            new_root.parent = None
            self._speculation_tree = SpeculationTree(nodes_pending_commit[0])
            print("Committed")
        self.logger.info(f"State is : {state}")
        return state

    def pending_state(self, block_id):
        return self._speculation_tree.get_state_by_block_id(block_id)

    def committed_block(self, block_id):
        self.logger.info(f"Committed blockid is {block_id}")
        return self._committed_states.get(block_id)


# if __name__ == "__main__":
    # ledger = Ledger()
    # blocks = []
    # for i in range(10):
        # blocks.append(Block(f'Client-{i+1}', i, f'ClientSent-{i+1}', None, 
        # block_id=str(i)))
    
    # ledger.speculate('GENESYS', blocks[0].block_id, blocks[0].payload)
    # ledger.speculate('0', blocks[1].block_id, blocks[1].payload)
    # ledger.speculate('GENESYS', blocks[2].block_id, blocks[1].payload)
    # ledger.speculate('GENESYS', blocks[3].block_id, blocks[3].payload)
    # ledger.speculate('0', blocks[4].block_id, blocks[1].payload)
    # ledger.speculate('1', blocks[5].block_id, blocks[1].payload)
    # ledger.commit('1')
