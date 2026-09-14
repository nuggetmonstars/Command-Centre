#!/usr/bin/env python3
"""Sort pipeline cards newest-applied first within each column. Run from ~/Command-Centre."""
import base64
f="recruitment.html"
s=open(f,encoding="utf-8").read()
o=base64.b64decode("ICAgIGNvbnN0IGluQ29sID0gY29hY2hlcy5maWx0ZXIoYz0+Yy5zdGFnZT09PXN0KTs=").decode()
w=base64.b64decode("ICAgIGNvbnN0IGluQ29sID0gY29hY2hlcy5maWx0ZXIoYz0+Yy5zdGFnZT09PXN0KS5zb3J0KChhLGIpPT57CiAgICAgIGNvbnN0IGRhPShhLmFwcGxpZWREYXRlfHxhLmRhdGVBcHBsaWVkfHwnJyksIGRiPShiLmFwcGxpZWREYXRlfHxiLmRhdGVBcHBsaWVkfHwnJyk7CiAgICAgIGlmKGRhJiZkYikgcmV0dXJuIGRiLmxvY2FsZUNvbXBhcmUoZGEpOyAgIC8vIG5ld2VzdCBhcHBsaWVkIGZpcnN0CiAgICAgIGlmKGRhJiYhZGIpIHJldHVybiAtMTsgICAgICAgICAgICAgICAgICAgICAgLy8gZGF0ZWQgb25lcyBhYm92ZSB1bmRhdGVkCiAgICAgIGlmKCFkYSYmZGIpIHJldHVybiAxOwogICAgICByZXR1cm4gKGEubmFtZXx8JycpLmxvY2FsZUNvbXBhcmUoYi5uYW1lfHwnJyk7CiAgICB9KTs=").decode()
if w in s: print("already applied")
elif o in s:
    open(f,"w",encoding="utf-8").write(s.replace(o,w,1)); print("patched OK -> columns sorted newest applied first")
else: print("COULD NOT FIND the column filter line - tell Claude")
