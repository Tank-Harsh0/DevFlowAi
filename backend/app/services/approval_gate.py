"""
Human Approval Gate.

Presents each fix proposal to the developer and records their decision.

Two operating modes:
  1. Interactive — prompts stdin (real CLI use).
  2. Programmatic — accepts a pre-supplied decisions dict keyed by finding_id.
     Used by the orchestrator when called non-interactively (tests, API).

Constraints (ARCHITECTURE.md §9):
  - Must not proceed without at least one developer action.
  - HIGH risk fixes: displayed as recommendations only, no application prompt.
  - Decisions are recorded in approved_fix_plan.json.
"""
from __future__ import annotations

from app.core.logging import get_logger
from app.models.fix_proposal import FixProposal, ProposalStatus

logger = get_logger(__name__)

# Valid interactive choices
_CHOICES = {"a": ProposalStatus.APPROVED, "s": ProposalStatus.SKIPPED, "r": ProposalStatus.REJECTED}


class ApprovalGate:
    """Collects developer decisions for each fix proposal.

    Args:
        decisions: Optional mapping of finding_id → ProposalStatus.
                   When supplied, the gate runs non-interactively (no stdin).
                   When None, the gate prompts the developer on stdin.
    """

    def __init__(self, decisions: dict[str, ProposalStatus] | None = None) -> None:
        self._decisions = decisions
        self._interactive = decisions is None

    def review(self, proposals: list[FixProposal]) -> list[FixProposal]:
        """Apply decisions to *proposals* and return the updated list.

        Args:
            proposals: FixProposal objects from the Fix Planner.

        Returns:
            Same list with status fields updated.
        """
        if not proposals:
            logger.info("Approval Gate: no proposals to review")
            return proposals

        updated: list[FixProposal] = []
        for proposal in proposals:
            decision = self._decide(proposal)
            # Pydantic models are immutable — create a copy with updated status
            updated.append(proposal.model_copy(update={"status": decision}))
            logger.info(
                "Approval Gate: %s → %s", proposal.finding_id, decision.value
            )

        approved = sum(1 for p in updated if p.status == ProposalStatus.APPROVED)
        logger.info(
            "Approval Gate complete: %d/%d approved",
            approved,
            len(updated),
        )
        return updated

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _decide(self, proposal: FixProposal) -> ProposalStatus:
        """Return the decision for a single proposal."""
        from app.models.finding import FixRisk  # avoid circular at module level

        # HIGH risk: never prompt for application — mark as skipped automatically
        if proposal.fix_risk == FixRisk.HIGH:
            logger.info(
                "Approval Gate: %s is HIGH risk — auto-skipped (recommendation only)",
                proposal.finding_id,
            )
            return ProposalStatus.SKIPPED

        # Non-interactive: look up pre-supplied decision
        if not self._interactive:
            status = (self._decisions or {}).get(
                proposal.finding_id, ProposalStatus.SKIPPED
            )
            return status

        # Interactive: prompt developer
        return self._prompt(proposal)

    def _prompt(self, proposal: FixProposal) -> ProposalStatus:
        """Print the proposal and wait for developer input."""
        print("\n" + "=" * 70)
        print(f"  Finding:     {proposal.finding_id}")
        print(f"  Risk:        {proposal.fix_risk.value.upper()}")
        print(f"  Description: {proposal.description}")
        if proposal.diff:
            print("\n  Diff:")
            for line in proposal.diff.splitlines()[:30]:
                print(f"    {line}")
            if proposal.diff.count("\n") > 30:
                print("    ... (diff truncated)")
        print("\n  [a] Approve   [s] Skip   [r] Reject")
        while True:
            choice = input("  Decision: ").strip().lower()
            if choice in _CHOICES:
                return _CHOICES[choice]
            print("  Please enter 'a', 's', or 'r'.")
