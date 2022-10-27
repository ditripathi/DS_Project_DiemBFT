import nacl.encoding
from nacl.signing import SigningKey
from nacl.hash import sha256


_encoder = nacl.encoding.Base64Encoder

def hasher(*items) -> str:
    """
    Return digest as string
    """
    items = list(map(str, items))
    msg = '|||'.join(items)
    if msg is str:
        msg = msg.encode('utf-8')
    else:
        msg = repr(msg).encode('utf8')
    return sha256(msg, encoder=_encoder).decode('utf-8')

def sign(private_key: SigningKey, *items):
    items = list(map(str, items))
    if len(items) == 0:
        raise Exception('No items provided') 
    msg = '|||'.join(items)
    # print('Msg', msg)
    if len(msg.strip()) == 0:
        raise Exception('Empty string provided to sign') 
    return private_key.sign(msg.encode('utf-8'), encoder=_encoder).decode('utf-8')

def valid_signatures(*items):
    # at leader, validate vote_msg.ledger_commit_info
    # at validators, validate signatures in QC
    # at validators, validate proposal message
    # raise NotImplementedError
    return True


if __name__ == "__main__":
    # signing_key = SigningKey.generate()
    from src.block import VoteInfo
    # sign(signing_key, '')
    msg = VoteInfo('abc', 5464, 'sadbjasdjb', 8574, 'asidnasiodn')
    hasher(msg)
    # 
