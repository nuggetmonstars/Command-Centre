#!/usr/bin/env python3
"""Open Needs: click Raised header to sort newest<->oldest. Run from ~/Command-Centre."""
import base64
f="recruitment.html"
s=open(f,encoding="utf-8").read()
P=[
  ("state","bGV0IE5FRURTID0gW107IGxldCBmTmVlZFN0YXR1cyA9ICJvcGVuIjsgbGV0IGZOZWVkVXJnID0gIkFsbCI7","bGV0IE5FRURTID0gW107IGxldCBmTmVlZFN0YXR1cyA9ICJvcGVuIjsgbGV0IGZOZWVkVXJnID0gIkFsbCI7IGxldCBuZWVkUmFpc2VkU29ydCA9IG51bGw7"),
  ("sort","ICAgICAgICAgICAgICAgICAgICAgICAuc29ydCgoYSxiKT0+KFVSR1JBTktbKGIudXJnZW5jeXx8JycpLnRvTG93ZXJDYXNlKCldfHwwKS0oVVJHUkFOS1soYS51cmdlbmN5fHwnJykudG9Mb3dlckNhc2UoKV18fDApKTs=","ICAgICAgICAgICAgICAgICAgICAgICAuc29ydCgoYSxiKT0+ewogICAgICAgICAgICAgICAgICAgICAgICAgaWYobmVlZFJhaXNlZFNvcnQpewogICAgICAgICAgICAgICAgICAgICAgICAgICBjb25zdCBkYT1hLmRhdGVSYWlzZWR8fCcnLCBkYj1iLmRhdGVSYWlzZWR8fCcnOwogICAgICAgICAgICAgICAgICAgICAgICAgICBpZighZGEmJiFkYikgcmV0dXJuIDA7IGlmKCFkYSkgcmV0dXJuIDE7IGlmKCFkYikgcmV0dXJuIC0xOwogICAgICAgICAgICAgICAgICAgICAgICAgICByZXR1cm4gbmVlZFJhaXNlZFNvcnQ9PT0nZGVzYycgPyBkYi5sb2NhbGVDb21wYXJlKGRhKSA6IGRhLmxvY2FsZUNvbXBhcmUoZGIpOwogICAgICAgICAgICAgICAgICAgICAgICAgfQogICAgICAgICAgICAgICAgICAgICAgICAgcmV0dXJuIChVUkdSQU5LWyhiLnVyZ2VuY3l8fCcnKS50b0xvd2VyQ2FzZSgpXXx8MCktKFVSR1JBTktbKGEudXJnZW5jeXx8JycpLnRvTG93ZXJDYXNlKCldfHwwKTsKICAgICAgICAgICAgICAgICAgICAgICB9KTs="),
  ("header","PHRoPlVyZ2VuY3k8L3RoPjx0aD5SYWlzZWQ8L3RoPjx0aD5SZWFzb248L3RoPg==","PHRoPlVyZ2VuY3k8L3RoPjx0aCBvbmNsaWNrPSJ0b2dnbGVSYWlzZWRTb3J0KCkiIHN0eWxlPSJjdXJzb3I6cG9pbnRlcjt1c2VyLXNlbGVjdDpub25lIiB0aXRsZT0iQ2xpY2sgdG8gc29ydCBieSBkYXRlIHJhaXNlZCI+UmFpc2VkICR7bmVlZFJhaXNlZFNvcnQ9PT0nZGVzYyc/J1x1MjVCQyc6bmVlZFJhaXNlZFNvcnQ9PT0nYXNjJz8nXHUyNUIyJzonXHUyMUM1J308L3RoPjx0aD5SZWFzb248L3RoPg=="),
  ("fn","d2luZG93LnNldE5lZWRTdGF0dXMgPSBmdW5jdGlvbihzKXsgZk5lZWRTdGF0dXM9czsgcmVuZGVyKCk7IH07","d2luZG93LnNldE5lZWRTdGF0dXMgPSBmdW5jdGlvbihzKXsgZk5lZWRTdGF0dXM9czsgcmVuZGVyKCk7IH07CndpbmRvdy50b2dnbGVSYWlzZWRTb3J0ID0gZnVuY3Rpb24oKXsgbmVlZFJhaXNlZFNvcnQgPSAobmVlZFJhaXNlZFNvcnQ9PT0nZGVzYycpID8gJ2FzYycgOiAnZGVzYyc7IHJlbmRlcigpOyB9Ow=="),
]
done=[];miss=[]
for n,ob,nb in P:
    o=base64.b64decode(ob).decode();w=base64.b64decode(nb).decode()
    if w in s: done.append(n+"(already)")
    elif o in s: s=s.replace(o,w,1);done.append(n)
    else: miss.append(n)
if miss: print("COULD NOT FIND:",miss)
else:
    open(f,"w",encoding="utf-8").write(s); print("patched OK:",done)
    print("toggleRaisedSort:", s.count("window.toggleRaisedSort"))
