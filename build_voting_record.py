#!/usr/bin/env python3
"""
Build the Voting Record Matrix data + page from official Maine Legislature
roll-call HTML (the "printer friendly" roll-call details pages).

Pipeline:
  sources/rollcalls/*.html  ->  voting-record-data.json  ->  voting-record.html

Each roll call is parsed for its overview (RC #, LD, date, motion, tallies) and
its per-member Yea/Nay/Absent/Excused list. The parser SELF-VERIFIES: the count
of parsed member votes must reconcile exactly to the tallies printed on the
official page, or the build aborts. Nothing ships unless the numbers match.

Vote codes as recorded by the Legislature: Y=Yea, N=Nay, X=Absent, E=Excused.
A "Yea" on ENACTMENT = a vote for the bill that enacted the tax increase(s).
"""
import html as htmllib
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "sources" / "rollcalls"
ROSTERS = ROOT / "sources" / "rosters"
SENATE_ROSTER = ROSTERS / "senate.html"
# 'List by District' page (House). The alphabetical roster has no district
# numbers; drop the district-listing page here to fill House districts in.
HOUSE_DISTRICT_ROSTER = ROSTERS / "house-districts.html"

# --- Which roll call enacted which bill/column ------------------------------
# Each bill is ONE column (one vote). The taxes it enacted are listed so the
# column header can say what a Yea actually bought.
BILLS = [
    {
        "key": "ld210",
        "label": "FY26–27 Budget",
        "ld": "LD 210",
        "chapter": "PL 2025, c. 388",
        "legislature": "132nd",
        "date": "2025-06-18",
        "date_label": "Jun 18, 2025",
        "motion": "Enactment",
        "house_file": "house-rc583-ld210-2025.html",
        "senate_file": "senate-rc635-ld210-2025.html",
        "tracker_rows": [1, 2, 4, 5, 6, 23, 25, 26, 27, 28, 31],
        "taxes": [
            "Tobacco tax +75%", "Streaming services tax", "Cannabis tax +40%",
            "Real estate transfer tax +173%", "Service provider tax base expanded",
            "Pension exemption phase-out", "Paint fee tripled",
            "Hunting & fishing license fees", "Concealed carry permit fees",
            "Arborist license fee", "Property tax relief funds swept",
        ],
    },
    {
        "key": "ld2212",
        "label": "2026 Supplemental",
        "ld": "LD 2212",
        "chapter": "PL 2025, c. 650",
        "legislature": "132nd",
        "date": "2026-04-09",
        "date_label": "Apr 8–9, 2026",
        "motion": "Enactment",
        "house_file": "house-rc791-ld2212-2026.html",
        "senate_file": "senate-rc927-ld2212-2026.html",
        "tracker_rows": [9, 11, 12, 13, 14, 15, 29, 32],
        "taxes": [
            "2% income surtax over $1M", "BETR eliminated for retail",
            "Federal conformity phased", "Decoupled from OBBBA business breaks",
            "Employer FMLA credit repealed", "Declined OBBBA individual cuts",
            "Manufactured housing transfer fee", "Budget stabilization fund drained",
        ],
    },
]

CELL_RE = re.compile(r'<td class="rccell" valign="top">(.*?)</td>', re.S)
TR_RE = re.compile(r"<tr>(.*?)</tr>", re.S)


def clean(cell: str) -> str:
    txt = re.sub(r"<[^>]+>", "", cell)
    txt = htmllib.unescape(txt).replace("\xa0", " ")
    return txt.strip()


def parse_overview(html: str) -> dict:
    rc = re.search(r"Roll-call #(\d+): LD (\d+)", html)
    yeas = re.search(
        r"Yeas \(Y\):\s*(\d+),\s*Nays \(N\):\s*(\d+),\s*"
        r"Absent \(X\):\s*(\d+),\s*Excused \(E\):\s*(\d+)",
        html, re.S,
    )
    dt = re.search(r"Date:.*?<td class=\"rccell\" valign=\"top\">\s*(.*?)\s*</td>", html, re.S)
    return {
        "rc": int(rc.group(1)),
        "ld": int(rc.group(2)),
        "date": clean(dt.group(1)) if dt else "",
        "tally": {k: int(v) for k, v in zip("YNXE", yeas.groups())},
    }


def parse_members(html: str) -> list:
    """Return [(surname, town, party, vote), ...] from the Details table."""
    details = html.split("Details</b>")[-1]
    members = []
    for tr in TR_RE.findall(details):
        cells = [clean(c) for c in CELL_RE.findall(tr)]
        if len(cells) < 7:
            continue
        for name, party, vote in ((cells[0], cells[1], cells[2]),
                                   (cells[4], cells[5], cells[6])):
            if not name or not party:
                continue  # trailing empty half-row
            surname, _, town = name.partition(" of ")
            members.append((surname.strip(), town.strip(), party.strip(), vote.strip()))
    return members


def titlecase(surname: str) -> str:
    def fix(word: str) -> str:
        w = word.lower()
        if w.startswith("o'") and len(w) > 2:
            return "O'" + w[2].upper() + w[3:]
        if w.startswith("mc") and len(w) > 2:
            return "Mc" + w[2].upper() + w[3:]
        return w[:1].upper() + w[1:]
    return " ".join("-".join(fix(s) for s in part.split("-")) for part in surname.split(" "))


PARTY_NAME = {"D": "Democrat", "R": "Republican", "I": "Independent", "U": "Unenrolled"}


def parse_senate_roster() -> list:
    """Senate district roster -> [{district, name_upper, party, county}].
    The district number is embedded in each senator's /districtN profile link."""
    if not SENATE_ROSTER.exists():
        return []
    raw = SENATE_ROSTER.read_text()
    out = []
    for m in re.finditer(
        r'href="/[Dd]istrict(\d+)"[^>]*>([^<]+)</a>[^(]*\(([A-Za-z])\s*-\s*([^)]+)\)', raw
    ):
        out.append({
            "district": int(m.group(1)),
            "name_upper": htmllib.unescape(m.group(2)).replace("\xa0", " ").strip().upper(),
            "party": m.group(3).upper(),
            "county": htmllib.unescape(m.group(4)).replace("\xa0", " ").strip(),
        })
    return out


_SUFFIXES = {"JR", "SR", "II", "III", "IV", "V"}


def norm_surname(s: str) -> str:
    """Uppercase surname key tolerant of the roster sources' quirks: JS-escaped
    and doubled apostrophes (O\\'\\'Halloran) and curly quotes all fold to a
    single straight apostrophe."""
    s = s.replace("\\", "").replace("’", "'").replace("‘", "'")
    s = re.sub(r"'{2,}", "'", s)
    return s.upper().strip()


def _drop_suffix(toks: list) -> list:
    while len(toks) > 1 and toks[-1].upper().strip(".") in _SUFFIXES:
        toks = toks[:-1]
    return toks


def parse_house_district_roster() -> dict:
    """House 'List by District' page -> {SURNAME: [{first, district, party}]}.
    That page lists district number + full name + party (no town), so we key by
    surname and disambiguate same-surname members by first name below."""
    if not HOUSE_DISTRICT_ROSTER.exists():
        return {}
    raw = HOUSE_DISTRICT_ROSTER.read_text()
    by_last = {}
    for m in re.finditer(r">District\s+(\d+)</a></td><td>([^<]+)</td><td>([^<]+)</td>", raw):
        toks = _drop_suffix(htmllib.unescape(m.group(2)).strip().split())
        if not toks:
            continue
        by_last.setdefault(norm_surname(toks[-1]), []).append(
            {"first": toks[0].upper(), "district": int(m.group(1)), "party": m.group(3).strip()})
    return by_last


def house_alpha_firstnames() -> dict:
    """(SURNAME, TOWN_UP) -> first-name token, from the alphabetical roster.
    Used only to disambiguate same-surname House members across the district
    roster (which has no town)."""
    f = ROSTERS / "house-alpha.html"
    if not f.exists():
        return {}
    out = {}
    for m in re.finditer(
        r"<br\s*/>\s*([^<,]+),\s*([^<]+?)\s*<br\s*/>\s*State Representative"
        r"\s*<br\s*/>\s*\([A-Za-z]\s*-\s*([^)]+)\)", f.read_text(), re.S):
        first = m.group(2).split()
        out[(norm_surname(m.group(1)),
             htmllib.unescape(m.group(3)).replace("\xa0", " ").strip().upper())] = \
            (first[0].upper() if first else "")
    return out


def attach_districts(roster: list) -> None:
    """Add a `district` to each legislator. Senate districts come from the
    Senate roster (matched by county + surname); House districts from the House
    'List by District' page (matched by surname, disambiguated by first name via
    the alphabetical roster). Anything not matched is left None — never guessed."""
    sen = parse_senate_roster()
    hd = parse_house_district_roster()
    afn = house_alpha_firstnames()
    n_sen = sum(1 for r in roster if r["chamber"] == "Senate")
    n_house = sum(1 for r in roster if r["chamber"] == "House")
    sen_m = house_m = 0
    unmatched = []
    for r in roster:
        r["district"] = None
        if r["chamber"] == "Senate":
            for s in sen:
                if s["county"].upper() == r["town"].upper() and s["name_upper"].endswith(r["name"].upper()):
                    r["district"] = s["district"]; sen_m += 1; break
        else:
            cands = hd.get(norm_surname(r["name"]), [])
            if len(cands) == 1:
                r["district"] = cands[0]["district"]
            elif len(cands) > 1:
                fn = afn.get((norm_surname(r["name"]), r["town"].upper()))
                pick = [c for c in cands if c["first"] == fn]
                if len(pick) == 1:
                    r["district"] = pick[0]["district"]
            if r["district"] is not None:
                house_m += 1
            elif hd:
                unmatched.append(r["name"] + " of " + r["town"])
    print(f"Districts: Senate {sen_m}/{n_sen} | House {house_m}/{n_house}")
    if unmatched:
        print("  House unmatched (left blank, not guessed): " + ", ".join(unmatched))


def load_bill(bill: dict) -> dict:
    out = {"chambers": {}}
    for chamber, fkey in (("House", "house_file"), ("Senate", "senate_file")):
        raw = (SRC / bill[fkey]).read_text()
        ov = parse_overview(raw)
        members = parse_members(raw)
        # self-verify: parsed vote counts must equal the official tallies
        counts = {"Y": 0, "N": 0, "X": 0, "E": 0}
        for *_, v in members:
            counts[v] = counts.get(v, 0) + 1
        expected = ov["tally"]
        got = {"Y": counts["Y"], "N": counts["N"], "X": counts["X"], "E": counts["E"]}
        if got != expected:
            sys.exit(f"VERIFY FAIL {bill['key']} {chamber} RC#{ov['rc']}: "
                     f"parsed {got} != official {expected}")
        print(f"  OK  {bill['key']:7} {chamber:6} RC#{ov['rc']:<4} "
              f"Y{got['Y']} N{got['N']} X{got['X']} E{got['E']}  (={sum(got.values())})")
        out["chambers"][chamber] = {"rc": ov["rc"], "date": ov["date"], "members": members}
    return out


def main() -> None:
    print("Parsing + verifying roll calls against official tallies:")
    legislators = {}  # key -> record
    bills_meta = []
    for bill in BILLS:
        parsed = load_bill(bill)
        rc_by_ch = {}
        for chamber, data in parsed["chambers"].items():
            rc_by_ch[chamber] = data["rc"]
            for surname, town, party, vote in data["members"]:
                key = f"{chamber}|{surname}|{town}"
                rec = legislators.setdefault(key, {
                    "name": surname, "disp": titlecase(surname), "town": town,
                    "chamber": chamber, "party": party, "votes": {},
                })
                rec["party"] = party  # latest bill wins
                rec["votes"][bill["key"]] = vote
        bills_meta.append({
            "key": bill["key"], "label": bill["label"], "ld": bill["ld"],
            "chapter": bill["chapter"], "legislature": bill["legislature"],
            "date_label": bill["date_label"], "motion": bill["motion"],
            "house_rc": rc_by_ch["House"], "senate_rc": rc_by_ch["Senate"],
            "n_taxes": len(bill["tracker_rows"]), "tracker_rows": bill["tracker_rows"],
            "taxes": bill["taxes"],
        })

    roster = sorted(legislators.values(),
                    key=lambda r: (r["chamber"] != "House", r["name"], r["town"]))
    attach_districts(roster)
    n_house = sum(1 for r in roster if r["chamber"] == "House")
    n_senate = len(roster) - n_house
    print(f"Union roster: {len(roster)} legislators ({n_house} House, {n_senate} Senate)")

    data = {
        "meta": {
            "generated": date.today().isoformat(),
            "party_names": PARTY_NAME,
            "note": ("Every mark traces to an official Maine Legislature enactment "
                     "roll call. Y=Yea (a vote FOR the bill that enacted the increase). "
                     "Cells are blank where a member was not seated for that vote."),
        },
        "bills": bills_meta,
        "legislators": roster,
    }
    (ROOT / "voting-record-data.json").write_text(json.dumps(data, indent=2, ensure_ascii=False))
    print("Wrote voting-record-data.json")

    inject_into_page(data)


def inject_into_page(data: dict) -> None:
    """Inject the voting data into the 'By Legislator' block of the main tracker
    page (`html`), between the /*VOTING_DATA_START*/ .. /*VOTING_DATA_END*/
    markers. Everything else in `html` stays hand-authored."""
    payload = json.dumps(data, ensure_ascii=False)
    target = ROOT / "html"
    page = target.read_text()
    if "/*VOTING_DATA_START*/" not in page:
        sys.exit("marker /*VOTING_DATA_START*/ not found in html")
    new = re.sub(
        r"/\*VOTING_DATA_START\*/.*?/\*VOTING_DATA_END\*/",
        lambda _: "/*VOTING_DATA_START*/" + payload + "/*VOTING_DATA_END*/",
        page, flags=re.S,
    )
    target.write_text(new)
    print("Injected voting data into html (By Legislator view)")


if __name__ == "__main__":
    main()
