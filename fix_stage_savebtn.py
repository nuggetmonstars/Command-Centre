#!/usr/bin/env python3
"""Stage change shows a Save button that commits the move. Run from ~/Command-Centre."""
import base64
f="recruitment.html"
s=open(f,encoding="utf-8").read()
P=[
  ("stageBtn","ICAgICAgPHNlbGVjdCBjbGFzcz0iZnNlbCIgc3R5bGU9Im1heC13aWR0aDoxMDAlO3dpZHRoOjEwMCUiIG9uY2hhbmdlPSJzYXZlU3RhZ2UoJyR7aWR9Jyx0aGlzLnZhbHVlKSI+JHtzdGFnZU9wdHN9PC9zZWxlY3Q+","ICAgICAgPHNlbGVjdCBjbGFzcz0iZnNlbCIgaWQ9InN0YWdlU2VsXyR7aWR9IiBzdHlsZT0ibWF4LXdpZHRoOjEwMCU7d2lkdGg6MTAwJSIgb25jaGFuZ2U9Im9uU3RhZ2VDaGFuZ2UoJyR7aWR9JykiPiR7c3RhZ2VPcHRzfTwvc2VsZWN0PgogICAgICA8YnV0dG9uIGlkPSJzdGFnZVNhdmVfJHtpZH0iIHN0eWxlPSJkaXNwbGF5Om5vbmU7bWFyZ2luLXRvcDo2cHg7YmFja2dyb3VuZDp2YXIoLS1ncmVlbik7Y29sb3I6I2ZmZjtib3JkZXI6bm9uZTtib3JkZXItcmFkaXVzOjhweDtwYWRkaW5nOjhweCAxNHB4O2ZvbnQtZmFtaWx5OidNYXJrZXJGZWx0JyxjdXJzaXZlO2N1cnNvcjpwb2ludGVyIiBvbmNsaWNrPSJjb21taXRTdGFnZSgnJHtpZH0nKSI+U2F2ZSBtb3ZlPC9idXR0b24+"),
  ("handlers","d2luZG93LnNhdmVTdGFnZSA9IHNhdmVTdGFnZTs=","d2luZG93LnNhdmVTdGFnZSA9IHNhdmVTdGFnZTsKd2luZG93Lm9uU3RhZ2VDaGFuZ2UgPSBmdW5jdGlvbihpZCl7CiAgY29uc3QgYyA9IENBTkRTLmZpbmQoeD0+eC5pZD09PWlkKTsgaWYoIWMpIHJldHVybjsKICBjb25zdCBzZWwgPSBkb2N1bWVudC5nZXRFbGVtZW50QnlJZCgnc3RhZ2VTZWxfJytpZCk7CiAgY29uc3QgYnRuID0gZG9jdW1lbnQuZ2V0RWxlbWVudEJ5SWQoJ3N0YWdlU2F2ZV8nK2lkKTsKICBpZiAoc2VsICYmIGJ0bikgYnRuLnN0eWxlLmRpc3BsYXkgPSAoc2VsLnZhbHVlICE9PSAoYy5zdGFnZXx8J0FwcGxpZWQnKSkgPyAnaW5saW5lLWJsb2NrJyA6ICdub25lJzsKfTsKd2luZG93LmNvbW1pdFN0YWdlID0gZnVuY3Rpb24oaWQpewogIGNvbnN0IHNlbCA9IGRvY3VtZW50LmdldEVsZW1lbnRCeUlkKCdzdGFnZVNlbF8nK2lkKTsKICBpZiAoc2VsKSBzYXZlU3RhZ2UoaWQsIHNlbC52YWx1ZSk7Cn07"),
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
    print("Save move:", s.count("Save move"), "| commitStage:", s.count("window.commitStage ="))
