#!/usr/bin/env python3
"""Expose saveStage + saveCheck to window so stage change and compliance toggles work. Run from ~/Command-Centre."""
import base64
f="recruitment.html"
s=open(f,encoding="utf-8").read()
P=[
  ("saveStage","ICByZW5kZXIoKTsgb3BlbkNhcmQoaWQpOwp9CmFzeW5jIGZ1bmN0aW9uIHNhdmVDaGVjayhpZCwga2V5LCB2YWwpew==","ICByZW5kZXIoKTsgb3BlbkNhcmQoaWQpOwp9CndpbmRvdy5zYXZlU3RhZ2UgPSBzYXZlU3RhZ2U7CmFzeW5jIGZ1bmN0aW9uIHNhdmVDaGVjayhpZCwga2V5LCB2YWwpew=="),
  ("saveCheck","ICByZW5kZXIoKTsgb3BlbkNhcmQoaWQpOwp9CmFzeW5jIGZ1bmN0aW9uIHNhdmVDYW5kKGlkLCBwYXRjaCl7","ICByZW5kZXIoKTsgb3BlbkNhcmQoaWQpOwp9CndpbmRvdy5zYXZlQ2hlY2sgPSBzYXZlQ2hlY2s7CmFzeW5jIGZ1bmN0aW9uIHNhdmVDYW5kKGlkLCBwYXRjaCl7"),
]
done=[];miss=[]
for n,ob,nb in P:
    o=base64.b64decode(ob).decode();w=base64.b64decode(nb).decode()
    if w in s: done.append(n+"(already)")
    elif o in s: s=s.replace(o,w,1);done.append(n)
    else: miss.append(n)
if miss: print("COULD NOT FIND:",miss)
else:
    open(f,"w",encoding="utf-8").write(s)
    print("patched OK:",done)
    print("window.saveStage:", s.count("window.saveStage ="), "| window.saveCheck:", s.count("window.saveCheck ="))
