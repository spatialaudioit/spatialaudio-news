"""Public RSS/release collector. Python standard library only; no keys or AI."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from hashlib import sha256
from html import unescape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
import subprocess
import time
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
UTC = timezone.utc
MAX_BYTES = 4 * 1024 * 1024


class PlainText(HTMLParser):
    def __init__(self):
        super().__init__(); self.parts = []; self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"): self.hidden += 1
        elif tag in ("p", "br", "li", "h2", "h3", "div"): self.parts.append(" ")

    def handle_endtag(self, tag):
        if tag in ("script", "style"): self.hidden = max(0, self.hidden - 1)
        elif tag in ("p", "li", "div"): self.parts.append(" ")

    def handle_data(self, data):
        if not self.hidden: self.parts.append(data)


def plain(value):
    parser = PlainText(); parser.feed(value or "")
    return re.sub(r"\s+", " ", unescape(" ".join(parser.parts))).strip()


def iso(dt):
    return dt.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def parse_date(value):
    if not value: raise ValueError("Data mancante")
    try: dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError: dt = parsedate_to_datetime(value)
    if dt.tzinfo is None: raise ValueError("Fuso orario mancante")
    return dt.astimezone(UTC)


def canonical_url(value):
    u = urlsplit((value or "").strip())
    if u.scheme != "https" or not u.hostname or u.username or u.password:
        raise ValueError("È richiesto un URL HTTPS pubblico")
    if u.port not in (None, 443): raise ValueError("Porta non ammessa")
    query = [(k, v) for k, v in parse_qsl(u.query, keep_blank_values=True)
             if not k.lower().startswith("utm_") and k.lower() not in ("fbclid", "gclid")]
    path = u.path.rstrip("/") or "/"
    return urlunsplit(("https", u.hostname.lower(), path, urlencode(sorted(query)), ""))


def rss_items(raw):
    if b"<!DOCTYPE" in raw.upper() or b"<!ENTITY" in raw.upper():
        raise ValueError("Dichiarazioni XML non ammesse")
    root = ET.fromstring(raw)
    if root.tag != "rss": raise ValueError("RSS 2.0 atteso")
    result = []
    for item in root.findall("./channel/item"):
        description = item.findtext("description") or ""
        content = item.findtext("{http://purl.org/rss/1.0/modules/content/}encoded") or ""
        result.append({"title": plain(item.findtext("title")), "url": item.findtext("link"),
                       "date": item.findtext("pubDate"), "description": plain(description),
                       "search_text": plain(description + " " + content)})
    return result


def release_items(raw):
    data = json.loads(raw)
    if not isinstance(data, list): raise ValueError("Elenco dei rilasci atteso")
    return [{"title": (x.get("name") or x["tag_name"]),
             "url": x["html_url"], "date": x.get("published_at"),
             "description": plain(x.get("body")), "search_text": plain(x.get("body"))}
            for x in data if not x.get("draft") and not x.get("prerelease")]


def atom_items(raw):
    if b"<!DOCTYPE" in raw.upper() or b"<!ENTITY" in raw.upper(): raise ValueError("Dichiarazioni XML non ammesse")
    root = ET.fromstring(raw); ns = {"a": "http://www.w3.org/2005/Atom"}
    if root.tag != "{http://www.w3.org/2005/Atom}feed": raise ValueError("Feed Atom atteso")
    result = []
    for item in root.findall("a:entry", ns):
        link = next((x.get("href") for x in item.findall("a:link", ns) if x.get("rel", "alternate") == "alternate"), None)
        content = plain(item.findtext("a:content", default="", namespaces=ns))
        summary = plain(item.findtext("a:summary", default="", namespaces=ns))
        published = item.findtext("a:published", namespaces=ns)
        result.append({"title": plain(item.findtext("a:title", namespaces=ns)), "url": link,
                       "date": published or item.findtext("a:updated", namespaces=ns),
                       "date_kind": "published" if published else "updated",
                       "description": summary or content, "search_text": summary + " " + content})
    return result


def fetch(source):
    if source.get('additional_urls'):
        base = {k: v for k, v in source.items() if k != 'additional_urls'}
        results = [fetch({**base, 'url': url}) for url in [source['url'], *source['additional_urls']]]
        items = [item for records, _ in results for item in records]
        errors = [status.get('error', 'Canale non disponibile') for _, status in results if status['status'] != 'ok']
        return items, {'id': source['id'], 'name': source['name'], 'url': source['url'],
                       'status': 'error' if errors else 'ok', 'received': len(items),
                       'pages': len(results), **({'error': '; '.join(errors)[:200]} if errors else {})}
    canonical_url(source["url"])
    request = Request(source["url"], headers={
        "User-Agent": "SpatialaudioNews/1.0 (+https://github.com/spatialaudioit/spatialaudio-news)",
        "Accept": "*/*"})
    for attempt in range(3):
        try:
            if source.get('transport') == 'curl':
                response = subprocess.run(['curl','--fail','--location','--silent','--show-error',
                                           '--max-time','15','--max-filesize',str(MAX_BYTES),
                                           '--proto','=https','--proto-redir','=https',
                                           '--user-agent',request.get_header('User-agent'),source['url']],
                                          capture_output=True, check=True, timeout=20)
                raw = response.stdout; endpoint = source['url']
            else:
                with urlopen(request, timeout=15) as response:
                    if response.status != 200: raise ValueError("HTTP " + str(response.status))
                    raw = response.read(MAX_BYTES + 1)
                    endpoint = response.url
            if len(raw) > MAX_BYTES: raise ValueError("Fonte troppo grande")
            parser = {"rss": rss_items, "atom": atom_items, "github_releases": release_items}[source["type"]]
            items = parser(raw)
            if source.get("title_prefix"):
                for item in items: item["title"] = source["title_prefix"] + " — " + item["title"]
            if not items: raise ValueError("Fonte vuota o formato cambiato")
            return items, {"id": source["id"], "name": source["name"], "url": source["url"],
                           "status": "ok", "http_status": 200, "endpoint": endpoint, "received": len(items)}
        except Exception as error:
            if attempt == 2:
                detail = ('curl exit ' + str(error.returncode) + ': ' + error.stderr.decode(errors='replace')[:180]
                          if isinstance(error, subprocess.CalledProcessError) else type(error).__name__ + ': ' + str(error)[:200])
                return [], {"id": source["id"], "name": source["name"], "url": source["url"],
                            "status": "error", "error": detail, "received": 0}
            time.sleep(attempt + 1)


def normalize(item, source, config, now):
    published = parse_date(item.get("date"))
    if published > now: raise ValueError("Data futura")
    if published < now - timedelta(days=config["max_age_days"]): raise ValueError("Fuori finestra temporale")
    original_url = item.get("url") or ""
    if source.get("upgrade_http_links") and original_url.startswith("http://") and urlsplit(original_url).hostname in source["article_hosts"]:
        original_url = "https://" + original_url[7:]
    url = canonical_url(original_url)
    u = urlsplit(url)
    if u.hostname not in source["article_hosts"]: raise ValueError("Dominio originale non autorizzato")
    if not u.path.startswith(source.get("article_path_prefix", "/")): raise ValueError("Percorso non autorizzato")
    title = plain(item.get("title"))
    if not title: raise ValueError("Titolo mancante")
    if any(re.search(p, title, re.I) for p in source.get("exclude_title_patterns", [])): return None
    text = " ".join([title, item.get("search_text", ""), source.get("context", "")])
    # A topical headline takes precedence over incidental topics in a long release.
    category = None
    for candidate in (title, text):
        category = next((topic["category"] for topic in config["topics"]
                         if any(re.search(pattern, candidate, re.I) for pattern in topic["patterns"])), None)
        if category: break
    if not category: return None
    # Prefer a topical excerpt rather than the opening of a mixed-topic press release.
    excerpt = item.get("description") or item.get("search_text", "")
    sentences = re.split(r"(?<=[.!?])\s+", item.get("search_text", ""))
    topical = next((s for s in sentences if any(re.search(p, s, re.I)
                   for t in config["topics"] for p in t["patterns"])), None)
    if topical: excerpt = topical
    words = excerpt.split()
    description = " ".join(words[:config["description_words"]])
    if len(words) > config["description_words"]: description += "…"
    if not description: description = "Aggiornamento ufficiale: consulta la fonte originale per i dettagli."
    return {"id": sha256(url.encode()).hexdigest()[:20], "title": title[:300], "url": url,
            "published_at": iso(published), "source_id": source["id"], "source": source["name"],
            "category": category, "description": description, "description_kind": "source_excerpt",
            "date_kind": item.get("date_kind", source.get("date_kind", "published")),
            "first_seen_at": iso(now), "last_seen_at": iso(now)}


def merge(previous, incoming):
    records = {canonical_url(x["url"]): dict(x) for x in previous}
    for item in incoming:
        key = canonical_url(item["url"])
        if key in records: item = {**item, "first_seen_at": records[key]["first_seen_at"]}
        records[key] = item
    return sorted(records.values(), key=lambda x: (x["published_at"], x["id"]), reverse=True)


def select(records, config, now):
    selected = []; counts = {}
    allowed = {s["id"] for s in config["sources"] if s.get("enabled", True)}
    sources = {s["id"]: s for s in config["sources"]}
    for record in records:
        sid = record["source_id"]; published = parse_date(record["published_at"])
        if sid not in allowed or not now - timedelta(days=config["max_age_days"]) <= published <= now: continue
        if any(re.search(p, record["title"], re.I) for p in sources[sid].get("exclude_title_patterns", [])): continue
        if counts.get(sid, 0) >= config["max_items_per_source"]: continue
        selected.append(record); counts[sid] = counts.get(sid, 0) + 1
        if len(selected) >= config["max_items"]: break
    return selected


def atomic_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def collect(config_path, output_root):
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if not 1 <= config["max_items"] <= 20: raise ValueError("La rassegna ammette da 1 a 20 notizie")
    now = datetime.now(UTC); stamp = iso(now)
    archive_path = output_root / "history/articles.json"
    records = json.loads(archive_path.read_text()) if archive_path.exists() else []
    old_path = output_root / "public/news.json"
    old = json.loads(old_path.read_text()) if old_path.exists() else {}
    sources = [s for s in config["sources"] if s.get("enabled", True)]
    if not sources or len({s["id"] for s in sources}) != len(sources): raise ValueError("Fonti mancanti o ID duplicati")
    incoming = []; diagnostics = []
    with ThreadPoolExecutor(max_workers=3) as pool:
        for source, (items, status) in zip(sources, pool.map(fetch, sources)):
            accepted = 0; rejected = 0
            for item in items:
                try:
                    record = normalize(item, source, config, now)
                    if record: incoming.append(record); accepted += 1
                except (ValueError, TypeError, KeyError, OverflowError): rejected += 1
            diagnostics.append({**status, "accepted": accepted, "rejected": rejected, "checked_at": stamp})
            dates = []
            for item in items:
                try: dates.append(parse_date(item.get("date")))
                except (ValueError, TypeError, OverflowError): pass
            diagnostics[-1]["latest_entry_at"] = iso(max(dates)) if dates else None
    merged = merge(records, incoming)
    success = sum(s["status"] == "ok" for s in diagnostics)
    status = "ok" if success == len(sources) else "partial" if success else "error"
    selected = select(merged, config, now)
    payload = {"schema_version": 1, "kind": "spatialaudio-news", "run_id": stamp,
               "checked_at": stamp, "last_success_at": stamp if success else old.get("last_success_at"),
               "status": status, "max_items": config["max_items"], "total_archived": len(merged),
               "policy": {"max_age_days": config["max_age_days"], "max_items_per_source": config["max_items_per_source"],
                          "descriptions": "Brevi estratti delle fonti, in lingua originale; nessuna sintesi AI."},
               "sources": diagnostics, "items": selected}
    states = {x["id"]: x for x in diagnostics}
    payload["source_catalog"] = [{"id": s["id"], "name": s["name"], "homepage": s["homepage"],
                                  "priority": s.get("priority", "Media"), "topics": s.get("monitor", "Audio spaziale"),
                                  "enabled": s.get("enabled", True), "note": s.get("note", ""),
                                  "status": states.get(s["id"], {}).get("status", "disabled"),
                                  "accepted": states.get(s["id"], {}).get("accepted", 0),
                                  "latest_entry_at": states.get(s["id"], {}).get("latest_entry_at")}
                                 for s in config["sources"]]
    if not selected and not success and old.get("items"): payload["items"] = old["items"]
    atomic_json(archive_path, merged)
    atomic_json(old_path, payload)
    run_path = output_root / "history/runs.json"
    runs = json.loads(run_path.read_text()) if run_path.exists() else []
    runs.append({"run_id": stamp, "status": status, "selected": len(selected), "archived": len(merged),
                 "sources": diagnostics})
    atomic_json(run_path, runs[-400:])
    print(json.dumps({"status": status, "selected": len(payload["items"]), "archived": len(merged),
                      "sources": [{"id": s["id"], "status": s["status"], "accepted": s["accepted"]} for s in diagnostics]}))
    # Publish diagnostics and retain prior data even during outages. The workflow flags the run afterwards.
    return status


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=ROOT / "sources.json")
    parser.add_argument("--output-root", type=Path, default=ROOT)
    args = parser.parse_args()
    collect(args.config, args.output_root)
