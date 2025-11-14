# backend/bcrypt_selfcheck.py
"""
Bcrypt / passlib self-check script
Jalankan: (venv) $ python backend/bcrypt_selfcheck.py
Script ini:
 - Mengecek versi passlib & bcrypt
 - Mencoba hash menggunakan passlib (CryptContext bcrypt)
 - Mencoba hash langsung menggunakan modul bcrypt
 - Mencoba edge-cases: password >72 bytes, non-utf8 bytes
 - Memberi rekomendasi jika terjadi error
"""
import sys
import platform
import traceback

print("=== BCRYPT / PASSLIB SELF-CHECK ===\n")

# 1) Environment info
print("Python:", sys.version.replace("\n", " "))
print("Platform:", platform.platform())
print("Implementation:", platform.python_implementation())
print()

# 2) Import modules and print versions
try:
    import passlib
    from passlib.context import CryptContext
    print("passlib:", passlib.__version__)
except Exception as e:
    print("passlib import ERROR:", e)
    print(traceback.format_exc())
    sys.exit(1)

try:
    import bcrypt
    print("bcrypt:", getattr(bcrypt, "__version__", "unknown"))
except Exception as e:
    print("bcrypt import ERROR:", e)
    print(traceback.format_exc())
    sys.exit(1)
print()

# 3) Setup CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def try_passlib_hash(pw):
    print(f"-> passlib.hash for password (len={len(pw)}):", end=" ")
    try:
        h = pwd_context.hash(pw)
        print("OK")
        print("   hash sample:", h[:60], "...")
    except Exception as e:
        print("ERROR")
        print("   exception:", repr(e))
        print(traceback.format_exc())

def try_bcrypt_hash(pw_bytes):
    print(f"-> bcrypt.hashpw for bytes (len={len(pw_bytes)}):", end=" ")
    try:
        h = bcrypt.hashpw(pw_bytes, bcrypt.gensalt())
        print("OK")
        print("   hash sample:", h.decode('utf-8')[:60], "...")
    except Exception as e:
        print("ERROR")
        print("   exception:", repr(e))
        print(traceback.format_exc())

print("### Test normal password (ASCII) ###")
pw = "predator123"
try_passlib_hash(pw)
try_bcrypt_hash(pw.encode("utf-8"))
print()

print("### Test long password (>72 bytes) ###")
long_pw = "x" * 80
try_passlib_hash(long_pw)
try_bcrypt_hash(long_pw.encode("utf-8"))
print("Note: bcrypt has a 72-byte input limit; passlib will raise if input too long.")
print()

print("### Test password with non-UTF8 bytes ###")
# Example: invalid utf-8 sequence (random bytes)
bad_bytes = bytes([0xff, 0xfe, 0xfd, 0xfc])
try:
    # passlib expects str; simulate bad path if someone passes bytes converted weirdly
    # First try as decoded (will raise)
    try:
        bad_str = bad_bytes.decode("utf-8")
        try_passlib_hash(bad_str)
    except Exception as e:
        print("-> decoding bad_bytes to utf-8 failed (expected).")
    # Try hashing raw bytes with bcrypt directly
    try_bcrypt_hash(bad_bytes)
except Exception as e:
    print("Unexpected error handling non-utf8 test:", e)
    print(traceback.format_exc())
print()

print("### Extra checks: pip show versions (if available) ###")
import subprocess, shlex
def pip_show(pkg):
    try:
        out = subprocess.check_output(shlex.split(f"pip show {pkg}"), stderr=subprocess.STDOUT, text=True)
        print(f"pip show {pkg}:\n{out.splitlines()[0]}\n")
    except Exception:
        print(f"pip show {pkg}: (not available)")

pip_show("passlib")
pip_show("bcrypt")

print("\n=== End of check ===")
print("""
COMMON FIXES:
 - Jika hash error muncul (password cannot be longer than 72 bytes): ensure you're passing a normal str (utf-8) under 72 bytes to bcrypt via passlib.
 - If bcrypt import fails or behavior odd: reinstall with:
    pip uninstall bcrypt passlib -y
    pip install passlib[bcrypt]
 - If you use Windows and build issues appear: consider installing wheel or using WSL.
""")
