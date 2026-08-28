#!/usr/bin/env python3
"""Refresh the publication list on publications.html from PubMed.

Runs monthly from .github/workflows/update-publications.yml, and can be run by
hand:  python scripts/update_publications.py

Only the regions between the PUBS / YEARS / STAMP marker comments are rewritten,
so anything else you edit on the page is left alone. Standard library only, so
the workflow needs no dependencies.
"""

import datetime
import json
import pathlib
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGE = ROOT / "publications.html"
DATA = ROOT / "pubs.json"

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
# NCBI asks callers to identify themselves.
TOOL = "gentry-lab-website"
EMAIL = "matthew.gentry@ufl.edu"

# Searches are unioned. Add to this list rather than widening one query.
QUERIES = [
    "Gentry MS[Author] AND (glycogen OR laforin OR malin OR Lafora)",
    "Gentry MS[Author] AND (Kentucky[Affiliation] OR Florida[Affiliation])",
]

# Names shown in bold. Add former members here as you like.
LAB_AUTHORS = {
    "Gentry MS", "Colpaert M", "Fermont L", "Singh PK", "Chen T",
    "Brennan K", "Cantrell AR", "Liu Y", "Valdivia G",
}

# Topic chips. A paper can match several.
RULES = [
    ("gsd", r"lafora|glycogen storage|pompe|polyglucosan|epm2|corpora amylacea|glut1|cori"),
    ("neuro", r"alzheimer|neurodegener|dementia|tau\b|amyloid|parkinson|apoe|astrocyt|neuron|"
              r"brain|cns|epilep|seizure|myoclon|spinal cord|dopaminergic|synapt"),
    ("cancer", r"cancer|tumou?r|carcinoma|sarcoma|neuroblastoma|glioma|glioblastoma|oncogen|"
               r"malignan|metasta"),
    ("enzyme", r"phosphatase|structur|crystal|laforin|malin|ubiquitin ligase|carbohydrate.binding|"
               r"kinase|snrk1|ampk|enzymolog|dimeriz|oligomeriz|binding module"),
    ("therapy", r"therap|treatment|drug|inhibit|antisense|gene therapy|preclinical|pre-clinical|"
                r"clinical trial|biomarker|alglucosidase|small.molecule"),
    ("methods", r"mass spectrom|maldi|imaging|spatial|metabolom|glycom|assay|protocol|pipeline|"
                r"quantitat|machine.learning|ai-driven|nanobody|microwave fixation"),
]

SKIP_JOURNALS = {"biorxiv", "medrxiv"}          # preprints; the published version is listed
SKIP_TYPES = {"Published Erratum", "Retracted Publication"}


# ---------------------------------------------------------------- fetching
def get(endpoint, params):
    params = dict(params, tool=TOOL, email=EMAIL)
    url = EUTILS + endpoint + "?" + urllib.parse.urlencode(params)
    for attempt in range(4):
        try:
            with urllib.request.urlopen(url, timeout=60) as resp:
                return resp.read()
        except Exception as exc:                # noqa: BLE001
            if attempt == 3:
                raise
            print(f"  retry {attempt + 1} after {exc}", file=sys.stderr)
            time.sleep(3 * (attempt + 1))
    raise RuntimeError("unreachable")


def search(query):
    raw = get("esearch.fcgi", {"db": "pubmed", "term": query, "retmax": 500, "retmode": "json"})
    return json.loads(raw)["esearchresult"]["idlist"]


def text(node, path, default=""):
    found = node.find(path)
    return "".join(found.itertext()).strip() if found is not None else default


def fetch(pmids):
    out = []
    for i in range(0, len(pmids), 100):
        chunk = pmids[i:i + 100]
        raw = get("efetch.fcgi", {"db": "pubmed", "id": ",".join(chunk), "retmode": "xml"})
        root = ET.fromstring(raw)
        for art in root.findall(".//PubmedArticle"):
            out.append(parse(art))
        time.sleep(0.4)                          # stay well inside NCBI's rate limit
    return out


def parse(art):
    ids = {e.get("IdType"): (e.text or "").strip() for e in art.findall("PubmedData/ArticleIdList/ArticleId")}
    authors = []
    for a in art.findall(".//AuthorList/Author"):
        last, initials = text(a, "LastName"), text(a, "Initials")
        if last:
            authors.append(f"{last} {initials}".strip())

    year = text(art, ".//Article/Journal/JournalIssue/PubDate/Year")
    if not year:
        medline = text(art, ".//Article/Journal/JournalIssue/PubDate/MedlineDate")
        m = re.search(r"\d{4}", medline)
        year = m.group(0) if m else ""
    if not year:
        year = text(art, ".//PubMedPubDate[@PubStatus='pubmed']/Year")

    return {
        "pmid": text(art, "MedlineCitation/PMID"),
        "doi": ids.get("doi", ""),
        "pmc": ids.get("pmc", ""),
        "title": text(art, ".//Article/ArticleTitle").rstrip("."),
        "journal": text(art, ".//Article/Journal/ISOAbbreviation")
                   or text(art, ".//Article/Journal/Title"),
        "year": int(year) if year.isdigit() else 0,
        "authors": authors,
        "types": [(e.text or "") for e in art.findall(".//PublicationTypeList/PublicationType")],
        "mesh": [text(m, "DescriptorName") for m in art.findall(".//MeshHeadingList/MeshHeading")],
        "kw": [(k.text or "").strip() for k in art.findall(".//KeywordList/Keyword")],
    }


# ---------------------------------------------------------------- shaping
def classify(r):
    hay = " ".join([r["title"], r["journal"]] + r["kw"] + r["mesh"]).lower()
    r["tags"] = [key for key, pat in RULES if re.search(pat, hay)] or ["other"]
    if "Review" in r["types"]:
        r["kind"] = "review"
    elif "Conference Proceedings" in r["types"] or re.search(r"workshop|symposium", r["title"], re.I):
        r["kind"] = "meeting"
    else:
        r["kind"] = "research"
    return r


def keep(r):
    return (r["pmid"] and r["title"] and r["year"]
            and r["journal"].lower() not in SKIP_JOURNALS
            and not (set(r["types"]) & SKIP_TYPES))


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def authors_html(names):
    def one(n):
        return f"<b>{esc(n)}</b>" if n in LAB_AUTHORS else esc(n)
    if len(names) <= 10:
        return ", ".join(one(n) for n in names)
    head, middle, tail = names[:6], names[6:-1], names[-1:]
    kept = [n for n in middle if n in LAB_AUTHORS]
    out = ", ".join(one(n) for n in head)
    if len(kept) < len(middle):
        out += " &hellip; "
        if kept:
            out += ", ".join(one(n) for n in kept) + ", "
    else:
        out += ", " + ", ".join(one(n) for n in kept) + ", "
    return out + ", ".join(one(n) for n in tail)


def entry_html(r):
    links = [f'<a class="publink" target="_blank" rel="noopener" href="https://pubmed.ncbi.nlm.nih.gov/{r["pmid"]}/">PubMed</a>']
    if r["doi"]:
        links.append(f'<a class="publink" target="_blank" rel="noopener" href="https://doi.org/{esc(r["doi"])}">DOI</a>')
    if r["pmc"]:
        links.append('<a class="publink" '
                     f'target="_blank" rel="noopener" href="https://pmc.ncbi.nlm.nih.gov/articles/{esc(r["pmc"])}/">Free full text</a>')
    hay = esc(" ".join([r["title"]] + r["authors"] + [r["journal"]]).lower().replace('"', ""))
    return (f'      <div class="pubitem" data-tags="{" ".join(r["tags"])}" data-kind="{r["kind"]}" '
            f'data-year="{r["year"]}" data-search="{hay}">\n'
            f'        <div class="pubtitle">{esc(r["title"])}</div>\n'
            f'        <div class="pubauthors">{authors_html(r["authors"])}</div>\n'
            f'        <div class="pubmeta"><span class="pubjournal">{esc(r["journal"])} {r["year"]}</span>'
            f'{"".join(links)}</div>\n'
            f'      </div>')


def splice(page, name, replacement):
    pattern = re.compile(f"(<!-- {name}:START -->).*?(<!-- {name}:END -->)", re.S)
    if not pattern.search(page):
        raise SystemExit(f"marker {name} not found in publications.html")
    return pattern.sub(lambda m: m.group(1) + replacement + m.group(2), page, count=1)


# ---------------------------------------------------------------- main
def main():
    pmids, seen = [], set()
    for q in QUERIES:
        found = search(q)
        print(f"{len(found):4d}  {q}")
        for p in found:
            if p not in seen:
                seen.add(p)
                pmids.append(p)
    print(f"{len(pmids):4d}  unique PMIDs")

    records = [classify(r) for r in fetch(pmids)]
    records = [r for r in records if keep(r)]
    records.sort(key=lambda r: (-r["year"], r["title"]))
    print(f"{len(records):4d}  after filtering")

    # Never let a bad run wipe a good list.
    if len(records) < 50:
        raise SystemExit(f"only {len(records)} records returned, refusing to overwrite the page")

    page = PAGE.read_text()
    page = splice(page, "PUBS", "\n" + "\n".join(entry_html(r) for r in records) + "\n      ")
    years = sorted({r["year"] for r in records}, reverse=True)
    page = splice(page, "YEARS", '<option value="all">All years</option>'
                  + "".join(f'<option value="{y}">{y}</option>' for y in years))
    page = splice(page, "STAMP", datetime.date.today().strftime("%d %B %Y"))
    PAGE.write_text(page)
    DATA.write_text(json.dumps(records, ensure_ascii=False, indent=1))
    print("wrote publications.html and pubs.json")


if __name__ == "__main__":
    main()
