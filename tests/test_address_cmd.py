import pytest

from application_client.command_sender import PbcCommandSender, Errors
from application_client.response_unpacker import unpack_get_address_response
from application_client.transaction import Address, from_hex
from ragger.bip import calculate_public_key_and_chaincode, CurveChoice
from ragger.bip.seed import SPECULOS_MNEMONIC
from ragger.error import ExceptionRAPDU
from ragger.navigator import NavInsID, NavIns
from utils import ROOT_SCREENSHOT_PATH, KEY_PATH


# In this test we check that the GET_ADDRESS works in non-confirmation mode
def test_get_address_no_confirm(backend):
    for path in [
            KEY_PATH, "m/44'/3757'/0'/0/0", "m/44'/3757'/910'/0/0",
            "m/44'/3757'/255/255/255", "m/44'/3757'/0/0/0/0/0/0/0"
    ]:
        client = PbcCommandSender(backend)
        response = client.get_address(path=path).data
        blockchain_address = unpack_get_address_response(response)

        ref_public_key, _ = calculate_public_key_and_chaincode(
            CurveChoice.Secp256k1, path=path)
        ref_address = Address.from_public_key(from_hex(ref_public_key))
        assert blockchain_address == ref_address


# In this test we check that the GET_ADDRESS works in confirmation mode
def test_get_address_confirm_accepted(firmware, backend, navigator, test_name):
    client = PbcCommandSender(backend)
    path = KEY_PATH
    with client.get_address_with_confirmation(path=path):
        if firmware.device.startswith("nano"):
            navigator.navigate_until_text_and_compare(NavInsID.RIGHT_CLICK,
                                                      [NavInsID.BOTH_CLICK],
                                                      "Approve",
                                                      ROOT_SCREENSHOT_PATH,
                                                      test_name)
        else:
            instructions = [
                NavInsID.USE_CASE_REVIEW_TAP,
                NavIns(NavInsID.TOUCH, (200, 335)),
                NavInsID.USE_CASE_ADDRESS_CONFIRMATION_EXIT_QR,
                NavInsID.USE_CASE_ADDRESS_CONFIRMATION_CONFIRM,
                NavInsID.USE_CASE_STATUS_DISMISS
            ]
            navigator.navigate_and_compare(ROOT_SCREENSHOT_PATH, test_name,
                                           instructions)
    response = client.get_async_response().data
    blockchain_address = unpack_get_address_response(response)

    ref_public_key, _ = calculate_public_key_and_chaincode(
        CurveChoice.Secp256k1, path=path)
    ref_address = Address.from_public_key(from_hex(ref_public_key))
    assert blockchain_address == ref_address


# In this test we check that the GET_ADDRESS in confirmation mode replies an error if the user refuses
def test_get_address_confirm_refused(firmware, backend, navigator, test_name):
    client = PbcCommandSender(backend)
    path = KEY_PATH

    if firmware.device.startswith("nano"):
        with pytest.raises(ExceptionRAPDU) as e:
            with client.get_address_with_confirmation(path=path):
                navigator.navigate_until_text_and_compare(
                    NavInsID.RIGHT_CLICK, [NavInsID.BOTH_CLICK], "Reject",
                    ROOT_SCREENSHOT_PATH, test_name)
        # Assert that we have received a refusal
        assert e.value.status == Errors.SW_DENY
        assert len(e.value.data) == 0
    else:
        instructions_set = [[
            NavInsID.USE_CASE_REVIEW_REJECT, NavInsID.USE_CASE_STATUS_DISMISS
        ],
                            [
                                NavInsID.USE_CASE_REVIEW_TAP,
                                NavInsID.USE_CASE_ADDRESS_CONFIRMATION_CANCEL,
                                NavInsID.USE_CASE_STATUS_DISMISS
                            ]]
        for i, instructions in enumerate(instructions_set):
            with pytest.raises(ExceptionRAPDU) as e:
                with client.get_address_with_confirmation(path=path):
                    navigator.navigate_and_compare(ROOT_SCREENSHOT_PATH,
                                                   test_name + f"/part{i}",
                                                   instructions)
            # Assert that we have received a refusal
            assert e.value.status == Errors.SW_DENY
            assert len(e.value.data) == 0


def test_get_address_for_seed(backend, cli_user_seed):
    """Derive the address for {@link KEY_PATH} using the seed phrase supplied via
    ``--seed`` and assert the device returns the matching address.

    When no ``--seed`` option is given, the test falls back to the default
    Speculos mnemonic so it can always run without extra arguments.

    Example invocation with a custom seed phrase::

        pytest tests/test_address_cmd.py::test_get_address_for_seed \\
            --device nanox \\
            --seed "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
    """
    mnemonic = cli_user_seed if cli_user_seed else SPECULOS_MNEMONIC

    client = PbcCommandSender(backend)
    response = client.get_address(path=KEY_PATH).data
    blockchain_address = unpack_get_address_response(response)

    ref_public_key, _ = calculate_public_key_and_chaincode(
        CurveChoice.Secp256k1, path=KEY_PATH, mnemonic=mnemonic)
    ref_address = Address.from_public_key(from_hex(ref_public_key))
    assert blockchain_address == ref_address


if __name__ == '__main__':
    from ragger.backend.ledgerwallet import LedgerWalletBackend
    from ragger.firmware import Firmware

    with LedgerWalletBackend(Firmware.NANOS) as backend:
        test_get_address_no_confirm(backend)
