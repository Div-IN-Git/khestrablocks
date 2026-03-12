import hashlib
import json
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class Block:
    index: int
    property_id: str
    from_wallet: str
    to_wallet: str
    timestamp: str
    previous_hash: str
    sale_agreement: str

    def hash_block(self) -> str:
        payload = json.dumps(asdict(self), sort_keys=True)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class FakeBlockchain:
    @staticmethod
    def create_block(index: int, property_id: str, from_wallet: str, to_wallet: str, previous_hash: str, sale_agreement: str) -> dict:
        block = Block(
            index=index,
            property_id=property_id,
            from_wallet=from_wallet,
            to_wallet=to_wallet,
            timestamp=datetime.utcnow().isoformat(),
            previous_hash=previous_hash,
            sale_agreement=sale_agreement,
        )
        return {
            **asdict(block),
            "hash": block.hash_block(),
        }
