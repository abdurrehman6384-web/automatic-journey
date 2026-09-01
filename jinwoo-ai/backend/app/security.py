"""Greed's no-scan preflight for optional secret-scanner integrations.

This module deliberately creates only an approval-ready boundary. It does not
read a workspace, enumerate Git history, load a scanner, verify a credential,
or expose a candidate secret in an API/audit response.
"""

from __future__ import annotations

from .schemas import SecurityScanPlan, WorkspaceStatus


class SecurityPlanError(ValueError):
    """A user-safe error for an unauthorised or unbounded scan request."""


_SCANNERS = {
    "gitleaks": ("Gitleaks", False),
    "trufflehog": ("TruffleHog", True),
}


def build_security_scan_plan(
    *,
    scanner_id: str,
    workspace_status: WorkspaceStatus,
    confirm_authorized: bool,
) -> SecurityScanPlan:
    """Prepare a local, no-scan plan for a later explicitly approved review."""

    if not workspace_status.configured:
        raise SecurityPlanError("Select a workspace before preparing a bounded security scan plan.")
    if not confirm_authorized:
        raise SecurityPlanError("Confirm that you are authorised to review the selected workspace before preparing a scan plan.")
    scanner = _SCANNERS.get(scanner_id)
    if scanner is None:
        raise SecurityPlanError("Choose a reviewed secret-scanner adapter.")
    label, license_review_required = scanner
    safeguards = [
        "No workspace file, Git history, credential, scanner binary or external service has been accessed.",
        "Any future scan is read-only, limited to the selected workspace and requires a separate visible approval.",
        "Candidate findings must be masked in the UI and audit log; no automatic remediation is allowed.",
        "Credential verification, uploads, CI reporting and network calls remain disallowed by default.",
    ]
    if license_review_required:
        safeguards.insert(0, "TruffleHog remains blocked from activation until its AGPL-3.0 compatibility decision is documented.")
    return SecurityScanPlan(
        scanner_id=scanner_id,  # validated against the fixed local scanner registry above
        scanner_label=label,
        workspace_configured=True,
        license_review_required=license_review_required,
        safeguards=safeguards,
        next_steps=[
            "Review the workspace boundary and decide whether a read-only scan is necessary.",
            "Approve a separate bounded scan only after the selected scanner's version, licence and local configuration are reviewed.",
            "Deliver a redacted local report with remediation suggestions; do not send, verify or auto-fix findings.",
        ],
    )
