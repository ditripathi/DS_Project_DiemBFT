from typing import List
from dataclasses import dataclass

from nacl.signing import SigningKey, VerifyKey


@dataclass
class ValidatorInfo:
    author: int
    validator_pks: List[VerifyKey]
    private_key: SigningKey
    client_pks: List[VerifyKey]
    f: int  # f is upper bound on number of byzantine faults
