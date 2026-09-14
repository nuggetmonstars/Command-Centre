#!/usr/bin/env python3
"""Card applied line -> actual date, bigger, blue. Run from ~/Command-Centre."""
import base64
f="recruitment.html"
s=open(f,encoding="utf-8").read()
o=base64.b64decode("ICAgICAgICAgICR7KGMuYXBwbGllZERhdGV8fGMuZGF0ZUFwcGxpZWQpP2A8ZGl2IGNsYXNzPSJwdCIgc3R5bGU9ImZvbnQtc2l6ZToxMXB4O2NvbG9yOiM5YWE4YjIiPmFwcGxpZWQgJHtNYXRoLm1heCgwLE1hdGgucm91bmQoKERhdGUubm93KCktbmV3IERhdGUoYy5hcHBsaWVkRGF0ZXx8Yy5kYXRlQXBwbGllZCkpLzg2NDAwMDAwKSl9ZCBhZ288L2Rpdj5gOicnfQ==").decode()
w=base64.b64decode("ICAgICAgICAgICR7KGMuYXBwbGllZERhdGV8fGMuZGF0ZUFwcGxpZWQpP2A8ZGl2IHN0eWxlPSJmb250LXNpemU6MTNweDtmb250LXdlaWdodDpib2xkO2NvbG9yOnZhcigtLWJsdWUpO21hcmdpbjoycHggMCI+QXBwbGllZCAke2RteShjLmFwcGxpZWREYXRlfHxjLmRhdGVBcHBsaWVkKX08L2Rpdj5gOicnfQ==").decode()
if w in s: print("already applied")
elif o in s:
    open(f,"w",encoding="utf-8").write(s.replace(o,w,1)); print("patched OK -> shows Applied DD-MM-YYYY, bigger, blue")
else: print("COULD NOT FIND the card line - tell Claude")
