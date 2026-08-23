"""Encryption round-trip, tamper detection, and KDF parameters.

These are the claims README.md makes in the 'Encryption Stack' table:
AES-128-CBC via Fernet, PBKDF2-HMAC-SHA256 x 600,000, a 16-byte random salt,
and a fresh IV per message.  Each one is asserted here rather than described.
"""

import base64

import pytest
from cryptography.fernet import Fernet, InvalidToken

from password_manager import encryption


# ----------------------------------------------------------------------
# Round-trip
# ----------------------------------------------------------------------

def test_encrypt_decrypt_round_trip():
    salt = encryption.generate_salt()
    fernet = encryption.create_user_key("alice", "correct horse battery staple", salt)
    plaintext = b'{"github": {"user": "alice", "password": "hunter2"}}'
    token = fernet.encrypt(plaintext)
    assert token != plaintext
    assert fernet.decrypt(token) == plaintext


def test_decrypt_with_wrong_password_raises():
    salt = encryption.generate_salt()
    good = encryption.create_user_key("alice", "right-password", salt)
    bad = encryption.create_user_key("alice", "wrong-password", salt)
    token = good.encrypt(b"secret")
    with pytest.raises(InvalidToken):
        bad.decrypt(token)


def test_decrypt_with_wrong_username_raises():
    """The length-prefixed KDF input must make user+password unambiguous."""
    salt = encryption.generate_salt()
    good = encryption.create_user_key("alice", "pw", salt)
    other = encryption.create_user_key("alic", "epw", salt)  # naive concat collision
    token = good.encrypt(b"secret")
    with pytest.raises(InvalidToken):
        other.decrypt(token)


def test_tampered_ciphertext_raises():
    salt = encryption.generate_salt()
    fernet = encryption.create_user_key("alice", "pw", salt)
    token = bytearray(fernet.encrypt(b"secret payload"))
    token[-1] ^= 0x01  # flip one bit of the HMAC
    with pytest.raises(InvalidToken):
        fernet.decrypt(bytes(token))


def test_tampered_ciphertext_body_raises():
    salt = encryption.generate_salt()
    fernet = encryption.create_user_key("alice", "pw", salt)
    token = bytearray(fernet.encrypt(b"secret payload"))
    token[30] ^= 0xFF  # flip a bit inside the ciphertext block
    with pytest.raises(InvalidToken):
        fernet.decrypt(bytes(token))


# ----------------------------------------------------------------------
# KDF parameters
# ----------------------------------------------------------------------

def test_pbkdf2_iterations_is_owasp_2023_floor():
    assert encryption.PBKDF2_ITERATIONS == 600_000


def test_keystore_uses_the_same_iteration_count():
    from password_manager import keystore

    assert keystore._PBKDF2_ITERATIONS == encryption.PBKDF2_ITERATIONS


def test_salt_is_sixteen_random_bytes():
    a = encryption.generate_salt()
    b = encryption.generate_salt()
    assert isinstance(a, bytes)
    assert len(a) == 16
    assert len(b) == 16
    assert a != b, "two consecutive salts were identical — not random"


def test_password_hash_is_32_bytes_and_salt_dependent():
    digest = encryption.hash_password("pw", b"\x00" * 16)
    assert len(digest) == 32
    assert digest != encryption.hash_password("pw", b"\x01" * 16)
    assert digest == encryption.hash_password("pw", b"\x00" * 16)


def test_fresh_iv_per_message():
    """Fernet token layout: 0x80 | 8B timestamp | 16B IV | ct | 32B HMAC."""
    salt = encryption.generate_salt()
    fernet = encryption.create_user_key("alice", "pw", salt)
    ivs = set()
    for _ in range(8):
        raw = base64.urlsafe_b64decode(fernet.encrypt(b"same plaintext"))
        assert raw[0] == 0x80, "unexpected Fernet version byte"
        ivs.add(raw[9:25])
    assert len(ivs) == 8, "IV repeated across messages"


def test_fernet_key_is_128_bit_aes_plus_128_bit_hmac():
    """The README says AES-128-CBC. Fernet splits its 32-byte key in half."""
    key = Fernet.generate_key()
    raw = base64.urlsafe_b64decode(key)
    assert len(raw) == 32
    signing_key, aes_key = raw[:16], raw[16:]
    assert len(aes_key) * 8 == 128
    assert len(signing_key) * 8 == 128


def test_system_key_is_urlsafe_base64_fernet_key():
    salt = encryption.generate_salt()
    key = encryption.create_system_key(salt)
    assert isinstance(key, bytes)
    assert len(base64.urlsafe_b64decode(key)) == 32
    Fernet(key)  # must be accepted by Fernet


def test_system_key_is_deterministic_for_one_machine_and_salt():
    salt = encryption.generate_salt()
    assert encryption.create_system_key(salt) == encryption.create_system_key(salt)
    assert encryption.create_system_key(salt) != encryption.create_system_key(
        encryption.generate_salt()
    )
