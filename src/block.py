import logging
from dataclasses import dataclass
from typing import Dict, List, Set
from collections import defaultdict, deque

from src.info import ValidatorInfo
from src.crypto import hasher, sign
from src.genesys import initialize_block_and_state
from src.ledger import Ledger

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# add formatter to ch
ch.setFormatter(formatter)
# add ch to logger
logger.addHandler(ch)

@dataclass
class VoteInfo:
    block_id: str
    round: int
    parent_block_id: str
    parent_round: int
    exec_state_id: str

    @staticmethod
    def to_tuple(obj):
        # logger.info("WARNING:")
        if not obj:
            return None
        return (obj.block_id, obj.round, obj.parent_block_id, obj.parent_round, 
        obj.exec_state_id)


@dataclass
class LedgerCommitInfo:
    commit_state_id: str
    vote_info_hash: str

    @staticmethod
    def to_tuple(obj):
        if not obj:
            return None
        return (obj.commit_state_id, obj.vote_info_hash)


@dataclass
class QC:
    vote_info: VoteInfo
    ledger_commit_info: LedgerCommitInfo
    signatures: Set[str]
    author: int
    author_signature: str

    def from_tuple(vote_info, ledger_commit_info, signatures, author, 
    author_signature):
        vote_info = VoteInfo(*vote_info)
        ledger_commit_info = LedgerCommitInfo(*ledger_commit_info)
        return QC(vote_info, ledger_commit_info, signatures, author, 
        author_signature)

    @staticmethod
    def to_tuple(obj):
        if not obj:
            return None
        return (VoteInfo.to_tuple(obj.vote_info), 
        LedgerCommitInfo.to_tuple(obj.ledger_commit_info), 
        obj.signatures, obj.author, obj.author_signature)


@dataclass
class VoteMsg:
    vote_info: VoteInfo
    ledger_commit_info: LedgerCommitInfo
    high_commit_qc: QC
    sender: str  # added automatically when constructed
    # TODO: signature types
    signature: str  # signed automatically when constructed

    @staticmethod
    def from_tuple(vote_info, ledger_commit_info, high_commit_qc, sender, signature):
        vote_info = VoteInfo.from_tuple(vote_info)
        ledger_commit_info = LedgerCommitInfo(*ledger_commit_info)
        qc = QC.from_tuple(high_commit_qc)
        return VoteMsg(vote_info, ledger_commit_info, qc, sender, signature)

    @staticmethod
    def to_tuple(obj):
        if not obj:
            return None
        return ('VoteMsg', VoteInfo.to_tuple(obj.vote_info), 
        LedgerCommitInfo.to_tuple(obj.ledger_commit_info), 
        QC.to_tuple(obj.high_commit_qc), obj.sender, obj.signature)


@dataclass
class Block:
    author: int
    round: int
    payload: str
    qc: QC
    block_id: str

    @staticmethod
    def from_tuple(author, round, payload, qc, block_id):
        return Block(author, round, payload, QC.from_tuple(*qc), block_id)

    @staticmethod
    def to_tuple(obj):
        if not obj:
            return None
        return (obj.author, obj.round, obj.payload, QC.to_tuple(obj.qc), 
        obj.block_id)


@dataclass
class PendingBlock:
    """
    Wrapper over Block. Contains additional references
    """
    block: Block
    # vote_info: VoteInfo
    parent: 'PendingBlock'
    children: List['PendingBlock'] = None


class PendingBlockTree:
    _root: PendingBlock
    _ids_to_block: Dict[str, PendingBlock]

    def __init__(self, root: PendingBlock = None) -> None:
        assert root.parent == None
        self._root: PendingBlock = root
        self._ids_to_block: Dict[str, PendingBlock] = {}
        self._ids_to_block = self.make_ids_to_block_from_root(root)

    def get_state_by_block_id(self, block_id) -> PendingBlock:
        return self._ids_to_block[block_id]

    def make_ids_to_block_from_root(self, root):
        # bfs on root
        logger.info("Make ids")
        dq = deque([root])
        hm = {}
        while len(dq):
            node = dq.popleft()
            hm[node.block.block_id] = node
            if node.children:
                dq.extend(node.children)
        return hm

    def prune(self, block_id):
        logger.info("Prune started")
        if not self._ids_to_block.get(block_id):
            return None
        node = self.get_state_by_block_id(block_id)
        nodes_pending_commit = []
        while node.parent != None:
            nodes_pending_commit.append(node)
            node = node.parent
        nodes_pending_commit = nodes_pending_commit[::-1]
        # TODO: Write nodes to file
        # self._ledger.writelines(list(map(str, nodes_pending_commit)))
        # with open(self._ledger_file_name, 'a+') as f:
        #     f.writelines(list(map(str, nodes_pending_commit)))
        # logger.info(self._ledger)
        # prune other branches
        if len(nodes_pending_commit) == 0:
            return None
        new_root = nodes_pending_commit[0]
        new_root.parent = None
        self._root = new_root
        self.make_ids_to_block_from_root(self._root)
        # return self._speculation_tree
        logger.info("Prune finished")

    def add(self, block: Block):
        parent_block_id = block.qc.vote_info.block_id
        assert self._ids_to_block[parent_block_id] != None
        parent_pending_block = self._ids_to_block[parent_block_id]
        if not parent_pending_block.children:
            parent_pending_block.children = []
        pending_block = PendingBlock(block, parent_pending_block, [])
        self._ids_to_block[pending_block.block.block_id] = pending_block
        parent_pending_block.children.append(pending_block)


class BlockTree:
    pending_block_tree: PendingBlockTree
    ledger: 'Ledger'
    # TODO: Initialize
    high_commit_qc: QC
    high_qc: QC
    pending_votes: defaultdict
    validator_info: ValidatorInfo

    def __init__(self, ledger: 'Ledger', validator_info: 'ValidatorInfo') -> None:
        # TODO: Initialize better
        self.ledger = ledger
        self.validator_info = validator_info
        n_validators = len(validator_info.validator_pks)
        assert n_validators != None
        bs1, bs2, bs3 = initialize_block_and_state(n_validators)
        root = PendingBlock(bs1[0], None, [])
        self.pending_block_tree = PendingBlockTree(root)
        self.pending_block_tree.add(bs2[0])
        self.pending_block_tree.add(bs3[0])
        # construct QC for 3rd object
        vi = VoteInfo(bs3[0].block_id, bs3[0].round, bs2[0].block_id, 
        bs2[0].round, bs3[1].state_id)
        lci = LedgerCommitInfo(bs3[1].state_id, None)
        self.high_qc = QC(vi, lci, None, self.validator_info.author, None)
        self.high_commit_qc = self.high_qc
        self.pending_votes = defaultdict(set)

    def process_qc(self, qc: 'QC') -> 'State':
        """
        process_qc is used to commit a state to ledger. It is called when 
        a proposal or timeout message or a vote comes.
        """
        logger.info("Process QC started")
        committed_state = None
        if qc.ledger_commit_info.commit_state_id != None:
            committed_state = self.ledger.commit(qc.vote_info.parent_block_id)
            # logger.info("Commit done")
            self.pending_block_tree.prune(qc.vote_info.parent_block_id)
            # high_commit_qc = max_round(qc, high_commit_qc)
            if qc.vote_info.round > self.high_commit_qc.vote_info.round:
                self.high_commit_qc = qc
        # high_qc = max_round(qc, high_qc)
        if qc.vote_info.round > self.high_qc.vote_info.round:
            self.high_qc = qc
        logger.info("Process QC Done")
        return committed_state

    def execute_and_insert(self, block: Block):
        logger.info(f"Exec and insert in blocktree: {block.block_id}")
        self.ledger.speculate(block.qc.vote_info.block_id, block.block_id, 
        block.payload)
        self.pending_block_tree.add(block)
        logger.info(f"""Block in Tree {self.pending_block_tree.get_state_by_block_id(
            block.block_id)}""")

    def process_vote(self, vote_msg: VoteMsg):
        self.process_qc(vote_msg.high_commit_qc)
        # TODO: replace with cryptographic hash
        vote_idx = hasher(vote_msg.ledger_commit_info)
        self.pending_votes[vote_idx].add(vote_msg.signature)
        if len(self.pending_votes[vote_idx]) == 2 * self.validator_info.f + 1:
            signatures = self.pending_votes[vote_idx]
            qc = QC(vote_info=vote_msg.vote_info, 
                ledger_commit_info=vote_msg.ledger_commit_info, 
                signatures=self.pending_votes[vote_idx], 
                author=self.validator_info.author, 
                author_signature=sign(self.validator_info.private_key, signatures))
            logger.info("Created QC for vote")
            return qc
        return None

    def generate_block(self, txns, current_round):
        # TODO: check below statement
        # output("current_round", current_round)
        # output("high_qc", high_qc)
        h = hasher(self.validator_info.author, current_round, txns, 
        self.high_qc.vote_info.block_id, self.high_qc.signatures)
        return Block(author=self.validator_info.author, round=current_round, 
        payload=txns, qc=self.high_qc, block_id=h)


if __name__ == "__main__":
    validator_info = ValidatorInfo(
        0,
        ['1', '2', '3', '7'],
        '145',
        ['1', '2', '3', '7'],
        1
    )
    ledger = Ledger(ledger_file_name=f'ledgers/ledger-{validator_info.author}.log',
    n_validators=len(validator_info.validator_pks))
    block_tree = BlockTree(ledger, validator_info)
    block_tree.generate_block('HELLO', 0)
    pass
