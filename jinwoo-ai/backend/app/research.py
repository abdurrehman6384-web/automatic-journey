"""Tank's no-fetch public-web research planning guard.

This is deliberately not a crawler. It validates explicit public targets and
creates a visible plan for a later, approved retrieval step. No URL is opened,
DNS-resolved, scraped, or handed to Firecrawl/Crawl4AI/Web-Agent here.
"""

from __future__ import annotations

import ipaddress
import re
from urllib.parse import parse_qsl, urlparse, urlunparse

from .schemas import ResearchPlan, ResearchTarget


class ResearchPolicyError(ValueError):
    """A safe error shown when a target is not an approved public-web URL."""


_PRIVATE_HOST_SUFFIXES = (".local", ".localhost", ".internal", ".home", ".lan")
_SENSITIVE_QUERY_KEYS = {
    "access-token", "access_token", "api-key", "api_key", "apikey", "auth", "authorization", "bearer",
    "cookie", "credential", "credentials", "key", "password", "secret", "session", "session_id",
    "sessionid", "sig", "signature", "token",
}
_DOMAIN_LABEL = re.compile(r"(?!-)[a-z0-9-]{1,63}(?<!-)$")


def _validate_target(raw_url: str) -> ResearchTarget:
    candidate = raw_url.strip()
    if not candidate or len(candidate) > 2_048:
        raise ResearchPolicyError("Each research target must be a non-empty URL up to 2,048 characters.")
    try:
        parsed = urlparse(candidate)
        port = parsed.port
    except ValueError as error:
        raise ResearchPolicyError("A research target has an invalid URL or port.") from error
    if parsed.scheme != "https":
        raise ResearchPolicyError("Only explicit HTTPS public-web targets can be planned.")
    if parsed.username or parsed.password:
        raise ResearchPolicyError("Research targets cannot contain login credentials.")
    if port not in (None, 443):
        raise ResearchPolicyError("Research targets must use the standard HTTPS port.")
    hostname = (parsed.hostname or "").casefold().rstrip(".")
    if not hostname or hostname == "localhost" or hostname.endswith(_PRIVATE_HOST_SUFFIXES):
        raise ResearchPolicyError("Private, local and localhost targets are not allowed.")
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        address = None
    if address is not None:
        raise ResearchPolicyError("Literal IP targets are not allowed; use an explicit public domain instead.")
    labels = hostname.split(".")
    if (
        not hostname.isascii()
        or len(labels) < 2
        or all(label.isdecimal() for label in labels)
        or any(_DOMAIN_LABEL.fullmatch(label) is None for label in labels)
    ):
        raise ResearchPolicyError("Research targets must use a valid public domain hostname.")
    if any(key.casefold() in _SENSITIVE_QUERY_KEYS for key, _ in parse_qsl(parsed.query, keep_blank_values=True)):
        raise ResearchPolicyError("Research targets cannot include credential-like query parameters.")
    sanitized_url = urlunparse(parsed._replace(fragment=""))
    return ResearchTarget(url=sanitized_url, hostname=hostname)


def build_research_plan(
    *,
    framework_id: str,
    topic: str,
    targets: list[str],
    confirm_public_sources: bool,
) -> ResearchPlan:
    """Validate explicit public targets and return a non-executing Tank plan."""

    if len(topic.strip()) < 2:
        raise ResearchPolicyError("Describe a research topic before creating a plan.")
    if targets and not confirm_public_sources:
        raise ResearchPolicyError("Confirm that you are authorised to research the listed public sources before planning retrieval.")

    approved_targets: list[ResearchTarget] = []
    seen_urls: set[str] = set()
    for raw_target in targets:
        target = _validate_target(raw_target)
        if target.url not in seen_urls:
            approved_targets.append(target)
            seen_urls.add(target.url)

    return ResearchPlan(
        framework_id=framework_id,
        topic=topic.strip(),
        targets=approved_targets,
        safeguards=[
            "No network request, browser session, cookie, crawl or scrape has started.",
            "Only explicit HTTPS public targets without credentials may be considered later.",
            "A future retrieval run needs visible user approval, rate/size limits and cited output.",
            "Private networks, localhost, authenticated sites and workspace uploads remain disallowed.",
        ],
        next_steps=[
            "Review the listed source targets and remove anything you do not own or have permission to research.",
            "Approve a separate bounded retrieval mission only after the framework licence and local runtime are reviewed.",
            "Have Tank cite each fetched source and keep raw research data in the selected local workspace.",
        ],
    )
