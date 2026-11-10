"""Small OS-backed secret store for Neo AI Terminal.

On Windows secrets are protected with the current user's DPAPI profile.
On macOS/Linux the optional `keyring` package is used when configured.
No API key is returned by the HTTP settings endpoints.
"""
from __future__ import annotations

import base64
import ctypes
import os
import sys
from ctypes import wintypes

SERVICE_NAME = "Neo AI Terminal"


class SecretStoreError(RuntimeError):
    pass


if sys.platform == "win32":
    class _DATA_BLOB(ctypes.Structure):
        _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_byte))]

    _crypt32 = ctypes.WinDLL("crypt32", use_last_error=True)
    _kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    _crypt32.CryptProtectData.argtypes = [
        ctypes.POINTER(_DATA_BLOB), wintypes.LPCWSTR,
        ctypes.POINTER(_DATA_BLOB), wintypes.LPVOID, wintypes.LPVOID,
        wintypes.DWORD, ctypes.POINTER(_DATA_BLOB),
    ]
    _crypt32.CryptProtectData.restype = wintypes.BOOL
    _crypt32.CryptUnprotectData.argtypes = [
        ctypes.POINTER(_DATA_BLOB), ctypes.POINTER(wintypes.LPWSTR),
        ctypes.POINTER(_DATA_BLOB), wintypes.LPVOID, wintypes.LPVOID,
        wintypes.DWORD, ctypes.POINTER(_DATA_BLOB),
    ]
    _crypt32.CryptUnprotectData.restype = wintypes.BOOL
    _kernel32.LocalFree.argtypes = [ctypes.c_void_p]
    _kernel32.LocalFree.restype = ctypes.c_void_p

    def _blob(raw: bytes):
        buffer = ctypes.create_string_buffer(raw, len(raw))
        return _DATA_BLOB(len(raw), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_byte))), buffer

    def _dpapi_protect(raw: bytes) -> bytes:
        source, keepalive = _blob(raw)
        output = _DATA_BLOB()
        ok = _crypt32.CryptProtectData(
            ctypes.byref(source), "Neo AI Terminal API credential", None, None, None,
            0x1, ctypes.byref(output),
        )
        if not ok:
            raise SecretStoreError(f"Windows DPAPI encryption failed: {ctypes.get_last_error()}")
        try:
            return ctypes.string_at(output.pbData, output.cbData)
        finally:
            _kernel32.LocalFree(output.pbData)

    def _dpapi_unprotect(raw: bytes) -> bytes:
        source, keepalive = _blob(raw)
        output = _DATA_BLOB()
        description = wintypes.LPWSTR()
        ok = _crypt32.CryptUnprotectData(
            ctypes.byref(source), ctypes.byref(description), None, None, None,
            0x1, ctypes.byref(output),
        )
        if not ok:
            raise SecretStoreError(
                "This API key cannot be decrypted under the current Windows account. "
                "Please enter it again."
            )
        try:
            return ctypes.string_at(output.pbData, output.cbData)
        finally:
            _kernel32.LocalFree(output.pbData)
            if description:
                _kernel32.LocalFree(description)


def save_secret(name: str, value: str) -> str:
    value = (value or "").strip()
    if not value:
        raise SecretStoreError("API key is empty")
    if sys.platform == "win32":
        return "dpapi:" + base64.b64encode(_dpapi_protect(value.encode("utf-8"))).decode("ascii")
    try:
        import keyring  # optional on non-Windows platforms
        keyring.set_password(SERVICE_NAME, name, value)
        return "keyring:"
    except Exception as exc:
        raise SecretStoreError(
            "Secure credential storage is unavailable on this platform. "
            "Install/configure Python keyring or run this app on Windows."
        ) from exc


def load_secret(name: str, stored_value: str | None) -> str:
    if not stored_value:
        return ""
    if stored_value.startswith("dpapi:"):
        if sys.platform != "win32":
            raise SecretStoreError("This credential is protected for its original Windows user account.")
        encrypted = base64.b64decode(stored_value[6:].encode("ascii"))
        return _dpapi_unprotect(encrypted).decode("utf-8")
    if stored_value == "keyring:":
        try:
            import keyring
            return keyring.get_password(SERVICE_NAME, name) or ""
        except Exception as exc:
            raise SecretStoreError("The operating-system keyring is not available.") from exc
    raise SecretStoreError("Unknown protected-secret format")


def delete_secret(name: str, stored_value: str | None) -> None:
    if stored_value == "keyring:":
        try:
            import keyring
            keyring.delete_password(SERVICE_NAME, name)
        except Exception:
            pass
