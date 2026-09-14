#!/usr/bin/env python3
"""Town/region filter shows the full region list per state (not just active-coach regions). Run from ~/Command-Centre."""
import base64
f="recruitment.html"
s=open(f,encoding="utf-8").read()
P=[
  ("map","Y29uc3QgQUxMX1NUQVRFUyA9IFsiVklDIiwiTlNXIiwiUUxEIiwiU0EiLCJXQSJdOw==","Y29uc3QgQUxMX1NUQVRFUyA9IFsiVklDIiwiTlNXIiwiUUxEIiwiU0EiLCJXQSJdOwpjb25zdCBIVUJTX0JZX1NUQVRFID0gewogIFZJQzogWyJNZWxib3VybmUiLCJHZWVsb25nIiwiQmFsbGFyYXQiLCJCZW5kaWdvIiwiR2lwcHNsYW5kIl0sCiAgTlNXOiBbIlN5ZG5leSIsIldvbGxvbmdvbmciLCJOZXdjYXN0bGUiXSwKICBRTEQ6IFsiQnJpc2JhbmUiLCJTdW5zaGluZSBDb2FzdCIsIkdvbGQgQ29hc3QiLCJNYWNrYXkiLCJUb293b29tYmEiLCJUb3duc3ZpbGxlIiwiQ2Fpcm5zIl0sCiAgU0E6ICBbIkFkZWxhaWRlIl0sCiAgV0E6ICBbIlBlcnRoIl0KfTs="),
  ("townOptions","ZnVuY3Rpb24gdG93bk9wdGlvbnMoKXsKICBjb25zdCBwb29sID0gYWN0aXZlQ29hY2hlcygpLmZpbHRlcihjPT5mU3RhdGU9PT0iQWxsInx8Yy5zdGF0ZT09PWZTdGF0ZSk7CiAgY29uc3QgaHVicyA9IFsuLi5uZXcgU2V0KHBvb2wubWFwKGM9PmMuaHViKS5maWx0ZXIoQm9vbGVhbikpXS5zb3J0KCk7CiAgbGV0IG8gPSBgPG9wdGlvbiB2YWx1ZT0iQWxsIj5BbGwgcmVnaW9ucyAoJHtodWJzLmxlbmd0aH0pPC9vcHRpb24+YDsKICBvICs9IGh1YnMubWFwKHQ9PmA8b3B0aW9uIHZhbHVlPSIke2VzYyh0KX0iICR7dD09PWZUb3duPydzZWxlY3RlZCc6Jyd9PiR7ZXNjKHQpfTwvb3B0aW9uPmApLmpvaW4oJycpOwogIHJldHVybiBvOwp9","ZnVuY3Rpb24gdG93bk9wdGlvbnMoKXsKICAvLyBjb21wbGV0ZSByZWdpb24gbGlzdCBmb3IgdGhlIHN0YXRlOiB0aGUgZml4ZWQgbWFwIFVOSU9OIGFueSBodWJzIHByZXNlbnQgaW4gdGhlIGRhdGEKICBsZXQgYmFzZSA9IFtdOwogIGlmIChmU3RhdGU9PT0iQWxsIikgeyBiYXNlID0gT2JqZWN0LnZhbHVlcyhIVUJTX0JZX1NUQVRFKS5mbGF0KCk7IH0KICBlbHNlIHsgYmFzZSA9IChIVUJTX0JZX1NUQVRFW2ZTdGF0ZV18fFtdKS5zbGljZSgpOyB9CiAgY29uc3Qgc2VlbiA9IENBTkRTLmZpbHRlcihjPT5mU3RhdGU9PT0iQWxsInx8Yy5zdGF0ZT09PWZTdGF0ZSkubWFwKGM9PmMuaHViKS5maWx0ZXIoQm9vbGVhbik7CiAgY29uc3QgaHVicyA9IFsuLi5uZXcgU2V0KFsuLi5iYXNlLCAuLi5zZWVuXSldLnNvcnQoKTsKICBsZXQgbyA9IGA8b3B0aW9uIHZhbHVlPSJBbGwiPkFsbCByZWdpb25zICgke2h1YnMubGVuZ3RofSk8L29wdGlvbj5gOwogIG8gKz0gaHVicy5tYXAodD0+YDxvcHRpb24gdmFsdWU9IiR7ZXNjKHQpfSIgJHt0PT09ZlRvd24/J3NlbGVjdGVkJzonJ30+JHtlc2ModCl9PC9vcHRpb24+YCkuam9pbignJyk7CiAgcmV0dXJuIG87Cn0="),
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
    print("HUBS_BY_STATE present:", s.count("HUBS_BY_STATE ="))
