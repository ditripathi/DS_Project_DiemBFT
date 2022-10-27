from src.crypto import hasher


def initialize_block_and_state(n_validators):
    """
    Generates starting blocks which all nodes agree on
    """
    from src.block import QC, Block, LedgerCommitInfo, VoteInfo
    from src.ledger import NoopTxnEngine

    # block 1
    author_1 = n_validators - 3
    round_1 = -3
    payload_1 = 'GENESYS'
    qc_1 = None
    qc_vote_info_1 = None
    qc_ledger_commit_info_1 = None
    block_1_id = hasher(author_1, round_1, payload_1, '', '')
    block_1 = Block(author_1, round_1, payload_1, qc_1, block_1_id)
    state_1 = NoopTxnEngine.execute_transactions(None, block_1_id, payload_1)
    # print("STATE 1", state_1)
    # block 2
    author_2 = n_validators - 2
    round_2 = -2
    payload_2 = 'GENESYS+1'
    qc_vote_info_2 = VoteInfo(block_1_id, round_1, None, None, state_1.state_id)
    qc_ledger_commit_info_2 = LedgerCommitInfo(state_1.state_id, None)
    qc_2 = QC(qc_vote_info_2, qc_ledger_commit_info_2, None, author_2, None)
    block_2_id = hasher(author_2, round_2, payload_2, '', '')
    block_2 = Block(author_2, round_2, payload_2, qc_2, block_2_id)
    state_2 = NoopTxnEngine.execute_transactions(state_1, block_2_id, payload_2)
    state_2.parent = state_1
    # print("STATE 2", state_2)
    state_1.children = [state_2]
    # block 3
    author_3 = n_validators - 1
    round_3 = -1
    payload_3 = 'GENESYS+2'
    qc_vote_info_3 = VoteInfo(block_2_id, round_2, block_1_id, round_1, 
    state_2.state_id)
    qc_ledger_commit_info_3 = LedgerCommitInfo(state_2.state_id, None)
    qc_3 = QC(qc_vote_info_3, qc_ledger_commit_info_3, None, author_2, None)
    block_3_id = hasher(author_3, round_3, payload_3, block_1_id, '')
    block_3 = Block(author_3, round_3, payload_3, qc_3, block_3_id)
    state_3 = NoopTxnEngine.execute_transactions(state_2, block_3_id, payload_3)
    state_3.parent = state_2
    state_2.children = [state_3]
    return (block_1, state_1), (block_2, state_2), (block_3, state_3)
