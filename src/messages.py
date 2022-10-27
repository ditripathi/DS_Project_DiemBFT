from typing import Set
from dataclasses import dataclass

from src.block import QC, Block


@dataclass
class TimeoutInfo:
    round: int
    high_qc: QC
    sender: str  # should be automatically added when created
    # TODO: might need to change it to bytes
    signature: str  # sign_u(round, high_qc.round) // automatically signed
    # when constructed


@dataclass
class TC:
    round: int  # All timeout messages that form TC have the same round
    tmo_high_qc_rounds: Set[int]  # A vector of 2f + 1 high qc round numbers
    # of timeout messages that form TC
    # TODO: signatures might change to bytes
    tmo_signatures: Set[str]  # A vector of 2f + 1 validator signatures on 
    # (round, respective high qc round)

    @staticmethod
    def to_tuple(obj):
        if not obj:
            return None
        return (obj.round, obj.tmo_high_qc_rounds, obj.tmo_signatures)


@dataclass
class TimeoutMsg:
    tmo_info: TimeoutInfo  # TimeoutInfo for some round with a high qc
    last_round_tc: TC  # TC for (tmo_info.round - 1) 
    # if tmo_info.high_qc.round != (tmo_info.round - 1), else None
    high_commit_qc: QC  # QC to synchronize on committed blocks


@dataclass
class ProposalMsg:
    block: 'Block'
    last_round_tc: TC  # TC for (block.round - 1) 
    # if block.qc.vote_info.round != (block.round - 1), else None
    high_commit_qc: QC  # QC to synchronise then committed blocks
    # TODO: might need to change to bytes
    signature: str
    sender : str

    @staticmethod
    def to_tuple(obj):
        if not obj:
            return None
        # output("last_round_tc", self.last_round_tc)
        return ('ProposalMsg', Block.to_tuple(obj.block), 
        TC.to_tuple(obj.last_round_tc), QC.to_tuple(obj.high_commit_qc), 
        obj.signature, obj.sender)
