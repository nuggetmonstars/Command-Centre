import re, sys
COACHES, TARGET = sys.argv[1], sys.argv[2]
src = open(COACHES, encoding="utf-8").read()
i = src.find("apiKey")
if i == -1:
    print("No apiKey found in", COACHES); sys.exit(1)
start = src.rfind("{", 0, i); end = src.find("}", i)
if start == -1 or end == -1:
    print("Could not bracket the config object."); sys.exit(1)
cfg = src[start:end+1].strip()
tgt = open(TARGET, encoding="utf-8").read()
if "PASTE_FROM_COACHES_HTML" not in tgt:
    print(TARGET, "already wired."); sys.exit(0)
new, n = re.subn(r'const FIREBASE_CONFIG\s*=\s*\{.*?\};',
                 'const FIREBASE_CONFIG = ' + cfg + ';', tgt, flags=re.S)
if n != 1:
    print("Expected 1 config block, found", n); sys.exit(1)
open(TARGET, "w", encoding="utf-8").write(new)
print("Done. Placeholder remaining (want 0):", new.count("PASTE_FROM_COACHES_HTML"))
