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

    render_html(data)
    print("Wrote voting-record.html")


def render_html(data: dict) -> None:
    template = (ROOT / "voting-record.template.html").read_text()
    payload = json.dumps(data, ensure_ascii=False)
    html = template.replace("/*__DATA__*/null", payload)
    (ROOT / "voting-record.html").write_text(html)


if __name__ == "__main__":
    main()
