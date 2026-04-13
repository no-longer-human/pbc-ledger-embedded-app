from pathlib import Path

from bip_utils import Bip39SeedGenerator
from ragger.bip import CurveChoice
from ragger.bip.seed import GET_CURVE_OBJ, SPECULOS_MNEMONIC

ROOT_SCREENSHOT_PATH = Path(__file__).parent.resolve()

KEY_PATH: str = "m/44'/3757'/0'/0/0"

CHAIN_IDS = [
    b'Partisia Blockchain Testnet',
    b'Partisia Blockchain',
]


def calculate_private_key(curve: CurveChoice,
                           path: str,
                           mnemonic: str = SPECULOS_MNEMONIC) -> str:
    """Derive the private key for the given BIP32 ``path`` and ``mnemonic``.

    Uses the same seed derivation as {@link calculate_public_key_and_chaincode},
    but returns the raw private key as a hex string instead of the public key.

    Args:
        curve: The elliptic curve to use for derivation.
        path: BIP32 derivation path (e.g. ``"m/44'/3757'/0'/0/0"``).
        mnemonic: BIP39 mnemonic word list. Defaults to {@link SPECULOS_MNEMONIC}.

    Returns:
        The 32-byte private key as a lowercase hex string.
    """
    seed = Bip39SeedGenerator(mnemonic).Generate()
    root_node = GET_CURVE_OBJ[curve].FromSeed(seed_bytes=seed)
    child_node = root_node.DerivePath(path=path)
    return child_node.PrivateKey().Raw().ToHex()
