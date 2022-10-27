import unittest
from unittest import TestCase

from nacl.signing import SigningKey
from src.block import VoteInfo, Block
from src.ledger import Ledger, SpeculationTree, State


class TestLedger(TestCase):
    # def setUp(self) -> None:
    #     self.priv_key = SigningKey.generate()
    #     self.pub_key = self.priv_key.verify_key

    def test_tree(self):
        blocks = []
        for i in range(10):
            blocks.append(Block(f'Client-{i+1}', i, f'ClientSent-{i+1}', None, 
            block_id=str(i)))
        root = State('GENESYS', 'GENESYS', None, 'GENESYS', [])
        ledger = Ledger(root=root, n_validators=1)
        ledger.speculate('GENESYS', blocks[0].block_id, blocks[0].payload)
        ledger.speculate('0', blocks[1].block_id, blocks[1].payload)
        ledger.speculate('GENESYS', blocks[2].block_id, blocks[1].payload)
        ledger.speculate('GENESYS', blocks[3].block_id, blocks[3].payload)
        ledger.speculate('0', blocks[4].block_id, blocks[1].payload)
        ledger.speculate('1', blocks[5].block_id, blocks[1].payload)
        ledger.commit('1')


if __name__ == "__main__":
    unittest.main()
