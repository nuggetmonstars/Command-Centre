#!/usr/bin/env python3
"""Expose saveNeed to window so Mark filled / Close / Reopen work. Run from ~/Command-Centre."""
import base64
f="recruitment.html"
s=open(f,encoding="utf-8").read()
o=base64.b64decode("ICByZW5kZXIoKTsKfQphc3luYyBmdW5jdGlvbiBjcmVhdGVOZWVkKG8pew==").decode()
w=base64.b64decode("ICByZW5kZXIoKTsKfQp3aW5kb3cuc2F2ZU5lZWQgPSBzYXZlTmVlZDsKYXN5bmMgZnVuY3Rpb24gY3JlYXRlTmVlZChvKXs=").decode()
if "window.saveNeed =" in s: print("already fixed")
elif o in s:
    open(f,"w",encoding="utf-8").write(s.replace(o,w,1)); print("patched OK -> Mark filled / Close / Reopen now work")
else: print("COULD NOT FIND anchor - tell Claude")
