import re

# 文末の誤字・脱字を補正（正規表現, 置換後）
PHRASE_MAP = [
  (re.compile(r"教えてく$"), "教えてください"),
  (re.compile(r"教えて$"), "教えてください"),
  (re.compile(r"おしえてく$"), "おしえてください"),
  (re.compile(r"おしえて$"), "おしえてください"),
  (re.compile(r"おしえて下さい$"), "おしえてください"),
  (re.compile(r"教えて下さい$"), "教えてください"),
]

def normalize_user_input(text: str) -> str:
  t = text.strip()
  for pat, repl in PHRASE_MAP:
    t = pat.sub(repl, t)
  return t