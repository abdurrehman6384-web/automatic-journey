"""
OrkasSEOAgent — Orkas Marketplace Skills (MIT)
================================================
Extracted from:
  orkas/resources/builtin/marketplace/agents/e064dca9e1bd/skills/
    seo-crawl/scripts/crawl.py
    seo-content/scripts/content.py
    seo-keywords/scripts/keywords.py
    geo-score/scripts/geo_score.py
    geo-probe/scripts/geo_probe.py
    seo-cwv/scripts/cwv.py
    seo-monitor/scripts/monitor.py

Also from the video agent:
  orkas/resources/builtin/marketplace/agents/79df9cc89f5f/
    skills/_shared/scripts/src/video_analyze.ts  (patterns ported to Python)

Pure Python — stdlib only for core logic, requests for network calls.
All return {"ok": bool, ...} — never raise.
"""

from __future__ import annotations

import json
import logging
import math
import os
import re
import time
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

log = logging.getLogger("rgs.orkas_seo")
ENABLED: bool = True

def _ok(d: Any = None) -> Dict: return {"ok": True, "result": d}
def _err(m: str) -> Dict:
    log.warning("OrkasSEO: %s", m)
    return {"ok": False, "error": m}

try:
    import requests as _req
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False


# ── Shared helpers (from Orkas seo-content / geo-probe) ──────────────────────
_WORD_RE = re.compile(r"\b[\w'-]+\b", re.UNICODE)
_STOP = {"the","and","for","with","your","you","our","are","that","this","from",
         "what","how","why","can","all","any","into","out","get","a","an","of",
         "to","in","is","it","on","by","or","be","as","open","source","free",
         "best","top","client","app","tool","tools"}

_AI_PHRASES = [
    "delve into","delve deeper","leverage the power","in today's fast-paced",
    "in today's digital","ever-evolving","cutting-edge","state-of-the-art",
    "seamlessly","robust solution","unlock the power","navigate the complexities",
    "tapestry of","testament to","it's important to note","when it comes to",
    "plethora of","game-changer","elevate your","embark on","in the realm of",
]

_STAT_RE   = re.compile(r"\b\d+(?:\.\d+)?\s*%")
_MONEY_RE  = re.compile(r"[$€£¥]\s?\d[\d,]*")
_AUTH_RE   = re.compile(r"\b(according to|study found|research shows|report that|survey found)\b", re.I)
_YEAR_RE   = re.compile(r"\bin (?:19|20)\d\d\b")
_SENT_SPLIT= re.compile(r"[.!?。！？]+")

_AI_BOTS = ("GPTBot","OAI-SearchBot","ChatGPT-User","ClaudeBot","PerplexityBot",
            "Google-Extended","CCBot","Claude-SearchBot")

_TRANSACTIONAL = re.compile(r"\b(buy|purchase|order|price|pricing|cost|quote|discount|free trial|trial|download|install|sign.?up|subscribe)\b", re.I)
_COMMERCIAL    = re.compile(r"\b(best|top|review|reviews|vs|versus|alternatives?|comparison|compare|tools?|software|platforms?)\b", re.I)
_INFORMATIONAL = re.compile(r"\b(what is|how to|why does|guide|tutorial|explain|definition|meaning)\b", re.I)


# ══════════════════════════════════════════════════════════════════════════════
# SEO Crawler (from seo-crawl)
# ══════════════════════════════════════════════════════════════════════════════
class SEOCrawler:
    """Lightweight SEO crawler — no external deps beyond requests."""

    def crawl(self, url: str, timeout: float = 15) -> Dict:
        """Crawl a URL and return SEO-relevant page data."""
        if not _HAS_REQUESTS:
            return _err("requests not installed: pip install requests")
        if not url.startswith(("http://","https://")):
            url = "https://" + url
        try:
            resp = _req.get(url, timeout=timeout,
                            headers={"User-Agent": "RGS-OrkasSEO/1.0"},
                            allow_redirects=True)
            final_url = resp.url
            html = resp.text
            return _ok(self._parse_page(html, final_url, resp.status_code))
        except Exception as exc:
            return _err(f"crawl: {exc}")

    def _parse_page(self, html: str, url: str, status: int) -> Dict:
        """Extract SEO signals from raw HTML."""
        # Try BeautifulSoup, fall back to regex
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
            title = soup.title.string.strip() if soup.title else ""
            h1s = [h.get_text(strip=True) for h in soup.find_all("h1")]
            h2s = [h.get_text(strip=True) for h in soup.find_all("h2")][:10]
            meta_desc = ""
            meta_tag = soup.find("meta", attrs={"name": "description"})
            if meta_tag:
                meta_desc = meta_tag.get("content", "")
            body_text = soup.body.get_text(" ", strip=True) if soup.body else ""
            images = soup.find_all("img")
            imgs_total  = len(images)
            imgs_no_alt = sum(1 for i in images if not i.get("alt"))
            links = [a.get("href","") for a in soup.find_all("a", href=True)]
            external_links = [l for l in links if l.startswith("http") and url not in l]
            robots_meta = ""
            robot_tag = soup.find("meta", attrs={"name": re.compile("robots", re.I)})
            if robot_tag:
                robots_meta = robot_tag.get("content", "")
            is_indexable = "noindex" not in robots_meta.lower()
            words = _WORD_RE.findall(body_text)
            word_count = len(words)
            first_para = body_text[:500]
        except ImportError:
            # Regex fallback
            title = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
            title = title.group(1).strip() if title else ""
            h1s = re.findall(r"<h1[^>]*>(.*?)</h1>", html, re.I | re.S)
            h2s = re.findall(r"<h2[^>]*>(.*?)</h2>", html, re.I | re.S)[:10]
            meta_desc = ""
            body_text = re.sub(r"<[^>]+>", " ", html)
            imgs_total = html.count("<img")
            imgs_no_alt = len(re.findall(r"<img(?![^>]*alt=)[^>]*>", html, re.I))
            external_links = re.findall(r'href=["\']https?://[^"\']+["\']', html)
            is_indexable = "noindex" not in html.lower()
            word_count = len(body_text.split())
            first_para = body_text[:500]
            words = body_text.split()

        return {
            "url": url, "status": status, "https": url.startswith("https://"),
            "title": title, "h1s": h1s, "h2s": h2s, "meta_description": meta_desc,
            "word_count": word_count, "first_paragraph": first_para[:200],
            "images_total": imgs_total, "images_missing_alt": imgs_no_alt,
            "external_link_count": len(external_links), "is_indexable": is_indexable,
            "h1_count": len(h1s),
        }


# ══════════════════════════════════════════════════════════════════════════════
# Content Quality Audit (from seo-content)
# ══════════════════════════════════════════════════════════════════════════════
class ContentAuditor:
    """Orkas seo-content heuristics — E-E-A-T, GEO-readiness, AI-cliché detection."""

    _WEIGHTS = {"critical": 25, "high": 12, "medium": 6, "low": 2}

    def audit(self, page_data: Dict) -> Dict:
        """
        page_data: output of SEOCrawler.crawl()["result"]
        Returns findings list + scores.
        """
        text = page_data.get("first_paragraph", "") + " " + \
               " ".join(page_data.get("h1s", [])) + " " + \
               " ".join(page_data.get("h2s", []))
        findings = []
        score = 100

        # Word count
        wc = page_data.get("word_count", 0)
        if wc < 300:
            findings.append({"severity": "critical", "msg": f"Very thin content ({wc} words)"})
            score -= self._WEIGHTS["critical"]
        elif wc < 700:
            findings.append({"severity": "high", "msg": f"Short content ({wc} words)"})
            score -= self._WEIGHTS["high"]

        # H1
        if page_data.get("h1_count", 0) == 0:
            findings.append({"severity": "critical", "msg": "Missing H1 tag"})
            score -= self._WEIGHTS["critical"]
        elif page_data.get("h1_count", 0) > 1:
            findings.append({"severity": "medium", "msg": "Multiple H1 tags"})
            score -= self._WEIGHTS["medium"]

        # Meta description
        md = page_data.get("meta_description", "")
        if not md:
            findings.append({"severity": "high", "msg": "Missing meta description"})
            score -= self._WEIGHTS["high"]
        elif len(md) > 160:
            findings.append({"severity": "low", "msg": f"Meta description too long ({len(md)} chars)"})
            score -= self._WEIGHTS["low"]

        # Images alt
        total_imgs = page_data.get("images_total", 0)
        missing_alt = page_data.get("images_missing_alt", 0)
        if total_imgs and missing_alt / total_imgs > 0.5:
            findings.append({"severity": "medium",
                             "msg": f"{missing_alt}/{total_imgs} images missing alt text"})
            score -= self._WEIGHTS["medium"]

        # HTTPS
        if not page_data.get("https"):
            findings.append({"severity": "critical", "msg": "Site not using HTTPS"})
            score -= self._WEIGHTS["critical"]

        # AI clichés
        ai_count = sum(1 for phrase in _AI_PHRASES if phrase in text.lower())
        if ai_count > 3:
            findings.append({"severity": "medium",
                             "msg": f"AI-cliché phrases detected ({ai_count})"})
            score -= self._WEIGHTS["medium"]

        # Claims / authority signals
        claims = (len(_STAT_RE.findall(text)) + len(_MONEY_RE.findall(text)) +
                  len(_AUTH_RE.findall(text)) + len(_YEAR_RE.findall(text)))
        if claims == 0 and wc > 500:
            findings.append({"severity": "medium",
                             "msg": "No statistics or authority claims found"})
            score -= self._WEIGHTS["medium"]

        # First paragraph quality (GEO: answer-first)
        fp = page_data.get("first_paragraph", "")
        if fp and len(fp.split()) < 15:
            findings.append({"severity": "low",
                             "msg": "First paragraph too short for GEO answer-first pattern"})
            score -= self._WEIGHTS["low"]

        return _ok({
            "score": max(0, score),
            "grade": "A" if score >= 90 else "B" if score >= 75 else "C" if score >= 60 else "D",
            "findings": findings,
            "url": page_data.get("url", ""),
        })


# ══════════════════════════════════════════════════════════════════════════════
# Keyword Processor (from seo-keywords)
# ══════════════════════════════════════════════════════════════════════════════
_MODIFIERS = {
    "best","top","good","great","cheap","free","paid","new","review","reviews",
    "compare","comparison","vs","versus","alternative","alternatives","guide",
    "tutorial","how","what","why","when","where","which","who","is","are","does",
    "do","can","should","the","a","an","of","to","in","on","for","with","and",
    "or","my","your","you",
}

class KeywordProcessor:
    """From Orkas seo-keywords: normalize, dedupe, classify intent, cluster."""

    def process(self, keywords: List[str]) -> Dict:
        """Normalize and classify a list of keyword strings."""
        normalized = self._normalize(keywords)
        classified = [self._classify(kw) for kw in normalized]
        clusters   = self._cluster(normalized)
        return _ok({
            "keywords": classified,
            "clusters": clusters,
            "count": len(classified),
        })

    def _normalize(self, keywords: List[str]) -> List[str]:
        seen, out = set(), []
        for kw in keywords:
            kw = kw.strip().lower()
            if kw and kw not in seen:
                seen.add(kw)
                out.append(kw)
        return out

    def _classify(self, kw: str) -> Dict:
        intent = "informational"
        if _TRANSACTIONAL.search(kw):
            intent = "transactional"
        elif _COMMERCIAL.search(kw):
            intent = "commercial"
        elif _INFORMATIONAL.search(kw):
            intent = "informational"
        else:
            intent = "navigational"
        words = _WORD_RE.findall(kw)
        core = [w for w in words if w not in _MODIFIERS and len(w) > 2]
        return {"keyword": kw, "intent": intent, "word_count": len(words),
                "core_terms": core, "long_tail": len(words) >= 4}

    def _cluster(self, keywords: List[str]) -> List[Dict]:
        """Group keywords by shared core terms."""
        from collections import defaultdict
        groups: Dict[str, List[str]] = defaultdict(list)
        for kw in keywords:
            words = _WORD_RE.findall(kw)
            key = " ".join(sorted(w for w in words
                                   if w not in _MODIFIERS and len(w) > 2)[:2])
            if key:
                groups[key].append(kw)
        return [{"cluster": k, "keywords": v, "size": len(v)}
                for k, v in sorted(groups.items(), key=lambda x: -len(x[1]))]


# ══════════════════════════════════════════════════════════════════════════════
# GEO Score (from Orkas geo-score)
# ══════════════════════════════════════════════════════════════════════════════
class GEOScorer:
    """Generative Engine Optimisation score — 5 dimensions."""

    _WEIGHTS = {"citability": 0.25, "structure": 0.20, "multimodal": 0.15,
                "authority": 0.20, "technical": 0.20}

    def score(self, page_data: Dict) -> Dict:
        """Score a page for GEO (AI-engine visibility)."""
        fp = page_data.get("first_paragraph", "")
        wc = page_data.get("word_count", 0)
        h1c = page_data.get("h1_count", 0)
        imgs = page_data.get("images_total", 0)
        imgs_no_alt = page_data.get("images_missing_alt", 0)
        ext_links = page_data.get("external_link_count", 0)
        https = page_data.get("https", False)
        indexable = page_data.get("is_indexable", True)

        # Citability: answer-first, claims, quotable facts
        fp_words = len(fp.split()) if fp else 0
        claims = (len(_STAT_RE.findall(fp)) + len(_AUTH_RE.findall(fp)) +
                  len(_YEAR_RE.findall(fp)))
        cit = min(100, (fp_words / 30) * 40 + claims * 15 + (ext_links > 2) * 20)

        # Structure: H1, headings, word count
        struct = min(100, (h1c == 1) * 30 + min(wc / 1500, 1) * 40 +
                    (len(page_data.get("h2s", [])) >= 3) * 30)

        # Multimodal: images with alt
        if imgs == 0:
            mm = 50
        else:
            good_imgs = imgs - imgs_no_alt
            mm = min(100, (good_imgs / max(imgs, 1)) * 100)

        # Authority: HTTPS, external links, structured data
        auth = ((https) * 40 + min(ext_links / 5, 1) * 40 + 20)

        # Technical: indexable, HTTPS
        tech = (indexable * 60 + https * 40)

        final = (cit   * self._WEIGHTS["citability"] +
                 struct * self._WEIGHTS["structure"] +
                 mm     * self._WEIGHTS["multimodal"] +
                 auth   * self._WEIGHTS["authority"] +
                 tech   * self._WEIGHTS["technical"])

        return _ok({
            "geo_score": round(final, 1),
            "dimensions": {
                "citability": round(cit, 1),
                "structure":  round(struct, 1),
                "multimodal": round(mm, 1),
                "authority":  round(auth, 1),
                "technical":  round(tech, 1),
            },
            "grade": "A" if final >= 80 else "B" if final >= 65 else "C" if final >= 50 else "D",
        })


# ══════════════════════════════════════════════════════════════════════════════
# Core Web Vitals (from Orkas seo-cwv)
# ══════════════════════════════════════════════════════════════════════════════
class CoreWebVitals:
    """Google PageSpeed Insights API wrapper (from Orkas seo-cwv skill)."""

    PSI_ENDPOINT = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"

    def fetch(self, url: str, strategy: str = "mobile",
              api_key: Optional[str] = None, timeout: float = 60) -> Dict:
        params = [("url", url), ("strategy", strategy), ("category", "performance")]
        if api_key:
            params.append(("key", api_key))
        full_url = self.PSI_ENDPOINT + "?" + urllib.parse.urlencode(params)
        try:
            req = urllib.request.Request(full_url,
                headers={"User-Agent": "RGS-OrkasCWV/1.0"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8", "replace"))
            return _ok(self._parse(data, url, strategy))
        except Exception as exc:
            return _err(f"PSI fetch error: {exc}")

    def _parse(self, data: Dict, url: str, strategy: str) -> Dict:
        lhr = data.get("lighthouseResult", {})
        cats = lhr.get("categories", {})
        perf_score = cats.get("performance", {}).get("score", None)
        audits = lhr.get("audits", {})
        def _ms(audit_id):
            a = audits.get(audit_id, {})
            return a.get("numericValue")
        return {
            "url": url, "strategy": strategy,
            "performance_score": round((perf_score or 0) * 100, 1),
            "lcp_ms":  _ms("largest-contentful-paint"),
            "cls":     _ms("cumulative-layout-shift"),
            "fid_ms":  _ms("max-potential-fid"),
            "ttfb_ms": _ms("server-response-time"),
            "fcp_ms":  _ms("first-contentful-paint"),
        }


# ══════════════════════════════════════════════════════════════════════════════
# OrkasSEOAgent unified facade
# ══════════════════════════════════════════════════════════════════════════════
class OrkasSEOAgent:
    def __init__(self):
        self.crawler   = SEOCrawler()
        self.auditor   = ContentAuditor()
        self.keywords  = KeywordProcessor()
        self.geo       = GEOScorer()
        self.cwv       = CoreWebVitals()

    def full_audit(self, url: str) -> Dict:
        """Crawl + content audit + GEO score in one call."""
        crawl_r = self.crawler.crawl(url)
        if not crawl_r["ok"]:
            return crawl_r
        page = crawl_r["result"]
        content_r = self.auditor.audit(page)
        geo_r     = self.geo.score(page)
        return _ok({
            "url": url,
            "page": page,
            "content_audit": content_r.get("result"),
            "geo_score":     geo_r.get("result"),
        })

    def dispatch(self, action: str, **kwargs) -> Dict:
        map_ = {
            "crawl":          lambda: self.crawler.crawl(**kwargs),
            "audit_content":  lambda: self.auditor.audit(kwargs.get("page_data", {})),
            "process_keywords": lambda: self.keywords.process(kwargs.get("keywords", [])),
            "geo_score":      lambda: self.geo.score(kwargs.get("page_data", {})),
            "cwv":            lambda: self.cwv.fetch(**kwargs),
            "full_audit":     lambda: self.full_audit(**kwargs),
        }
        fn = map_.get(action)
        if fn is None:
            return _err(f"Unknown action: {action!r}")
        try:
            return fn()
        except Exception as exc:
            return _err(str(exc))


# ── singletons ────────────────────────────────────────────────────────────────
AGENT = OrkasSEOAgent()


def smoke_test() -> bool:
    # keyword processor (no network)
    r = AGENT.keywords.process(["best python tutorial", "python tutorial 2024",
                                 "how to learn python", "buy python course"])
    ok = r["ok"] and r["result"]["count"] >= 3
    # geo scorer (no network)
    r2 = AGENT.geo.score({"word_count": 1200, "h1_count": 1, "https": True,
                           "is_indexable": True, "images_total": 3,
                           "images_missing_alt": 0, "external_link_count": 5,
                           "first_paragraph": "RGS AI Desktop is an open-source PyQt6 agent. According to benchmarks it achieves 95% accuracy in 2024."})
    ok = ok and r2["ok"] and r2["result"]["geo_score"] > 50
    log.info("OrkasSEOAgent smoke_test: %s", "PASS" if ok else "FAIL")
    return ok


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    print(smoke_test())
