import json, os, re, sys
CACHE = os.environ.get("EXPLAINER_CACHE", os.path.expanduser("~/.cache/explainer-video"))
CUR = {"USD": "$", "EUR": "€", "GBP": "£", "INR": "₹", "CAD": "$", "AUD": "$"}
CUR_WORD = {"$": "dollars", "€": "euros", "£": "pounds", "₹": "rupees"}
PERIOD_WORD = {"mo": "a month", "month": "a month", "yr": "a year", "year": "a year", "wk": "a week", "day": "a day", "user": "per user", "seat": "per seat"}

def load(path):
    v = json.load(open(path))
    v["_dir"] = os.path.dirname(os.path.abspath(path))
    return v

def fix_price_text(s, warn=None):
    """Display rule: whole amounts drop decimals ($20.00 -> $20, $20.0 -> $20); cents stay as two digits ($19.9 -> $19.90)."""
    def rep(m):
        sym, whole, frac = m.group(1), m.group(2), m.group(3)
        if frac and set(frac) == {"0"}:
            if warn is not None: warn.append(m.group(0))
            return f"{sym}{whole}"
        if frac and len(frac) == 1: return f"{sym}{whole}.{frac}0"
        return m.group(0)
    return re.sub(r"([$€£₹])(\d[\d,]*)(?:\.(\d+))?", rep, s)

def spoken(s, acronyms=()):
    """Turn display text into something the voice reads naturally."""
    def money(m):
        sym, whole, frac, per = m.group(1), m.group(2).replace(",", ""), m.group(3), m.group(4)
        w = CUR_WORD.get(sym, "")
        out = f"{whole} {w}" if not frac or set(frac) == {"0"} else f"{whole} {w} {frac.ljust(2,'0')[:2]}"
        if per: out += " " + PERIOD_WORD.get(per.lower(), "per " + per)
        return out
    s = re.sub(r"([$€£₹])(\d[\d,]*)(?:\.(\d+))?(?:\s*/\s*([A-Za-z]+))?", money, s)
    s = re.sub(r"(\w)\+", r"\1 Plus", s)          # Privacy+ -> Privacy Plus
    s = s.replace("&", " and ").replace("%", " percent")
    s = re.sub(r"\b[\w-]+(?:\.[\w-]+)*\.(?:com|io|ai|org|net|co|dev|app)\b", lambda m: m.group(0).replace(".", " dot "), s)
    s = re.sub(r"(\w)/(\w)", r"\1 slash \2", s)
    for a in acronyms: s = re.sub(rf"\b{re.escape(a)}\b", " ".join(a), s)
    return s
