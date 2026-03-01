"""llm_toolkit_schema.namespaces.guard — Content guardrail payload types.

Classes
-------
GuardBlockedPayload
    ``llm.guard.blocked`` — an input was rejected by a guardrail policy.
GuardFlaggedPayload
    ``llm.guard.flagged`` — an output was flagged (but not blocked) by a
    guardrail policy.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional


@dataclass(frozen=True)
class GuardBlockedPayload:
    """Payload for ``llm.guard.blocked``.

    Parameters
    ----------
    policy_id:
        Unique identifier for the guardrail policy that triggered.
    policy_name:
        Human-readable name for the policy.
    input_hash:
        SHA-256 hex digest (or similar fingerprint) of the blocked input.
    violation_types:
        List of violation categories, e.g. ``["jailbreak", "prompt_injection"]``.
    action:
        Disposition taken — always ``"blocked"`` for this payload type.
    severity:
        Severity level: ``"low"``, ``"medium"``, ``"high"``, ``"critical"``.
    """

    policy_id: str
    policy_name: str
    input_hash: str
    violation_types: List[str]
    action: str = "blocked"
    severity: str = "high"

    # -----------------------------------------------------------------
    # Validation
    # -----------------------------------------------------------------

    def __post_init__(self) -> None:
        for attr in ("policy_id", "policy_name", "input_hash"):
            value = getattr(self, attr)
            if not value or not isinstance(value, str):
                raise ValueError(f"GuardBlockedPayload.{attr} must be a non-empty string")
        if not isinstance(self.violation_types, list) or not self.violation_types:
            raise ValueError(
                "GuardBlockedPayload.violation_types must be a non-empty list of strings"
            )
        for v in self.violation_types:
            if not isinstance(v, str):
                raise TypeError("Each violation_type must be a string")
        if self.severity not in frozenset({"low", "medium", "high", "critical"}):
            raise ValueError(
                f"GuardBlockedPayload.severity must be low/medium/high/critical, "
                f"got {self.severity!r}"
            )

    # -----------------------------------------------------------------
    # Serialisation
    # -----------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Return a plain dict suitable for ``Event.payload``."""
        return {
            "policy_id": self.policy_id,
            "policy_name": self.policy_name,
            "input_hash": self.input_hash,
            "violation_types": list(self.violation_types),
            "action": self.action,
            "severity": self.severity,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GuardBlockedPayload":
        """Reconstruct a :class:`GuardBlockedPayload` from a plain dict."""
        return cls(
            policy_id=str(data["policy_id"]),
            policy_name=str(data["policy_name"]),
            input_hash=str(data["input_hash"]),
            violation_types=list(data["violation_types"]),
            action=str(data.get("action", "blocked")),
            severity=str(data.get("severity", "high")),
        )


@dataclass(frozen=True)
class GuardFlaggedPayload:
    """Payload for ``llm.guard.flagged``.

    Parameters
    ----------
    policy_id:
        Unique identifier for the guardrail policy that triggered.
    policy_name:
        Human-readable name for the policy.
    output_hash:
        SHA-256 hex digest (or similar fingerprint) of the flagged output.
    flag_types:
        List of flag categories, e.g. ``["toxic_language", "pii_leak"]``.
    action:
        Disposition taken — always ``"flagged"`` for this payload type.
    severity:
        Severity level: ``"low"``, ``"medium"``, ``"high"``, ``"critical"``.
    """

    policy_id: str
    policy_name: str
    output_hash: str
    flag_types: List[str]
    action: str = "flagged"
    severity: str = "medium"

    # -----------------------------------------------------------------
    # Validation
    # -----------------------------------------------------------------

    def __post_init__(self) -> None:
        for attr in ("policy_id", "policy_name", "output_hash"):
            value = getattr(self, attr)
            if not value or not isinstance(value, str):
                raise ValueError(f"GuardFlaggedPayload.{attr} must be a non-empty string")
        if not isinstance(self.flag_types, list) or not self.flag_types:
            raise ValueError(
                "GuardFlaggedPayload.flag_types must be a non-empty list of strings"
            )
        for f in self.flag_types:
            if not isinstance(f, str):
                raise TypeError("Each flag_type must be a string")
        if self.severity not in frozenset({"low", "medium", "high", "critical"}):
            raise ValueError(
                f"GuardFlaggedPayload.severity must be low/medium/high/critical, "
                f"got {self.severity!r}"
            )

    # -----------------------------------------------------------------
    # Serialisation
    # -----------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Return a plain dict suitable for ``Event.payload``."""
        return {
            "policy_id": self.policy_id,
            "policy_name": self.policy_name,
            "output_hash": self.output_hash,
            "flag_types": list(self.flag_types),
            "action": self.action,
            "severity": self.severity,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GuardFlaggedPayload":
        """Reconstruct a :class:`GuardFlaggedPayload` from a plain dict."""
        return cls(
            policy_id=str(data["policy_id"]),
            policy_name=str(data["policy_name"]),
            output_hash=str(data["output_hash"]),
            flag_types=list(data["flag_types"]),
            action=str(data.get("action", "flagged")),
            severity=str(data.get("severity", "medium")),
        )


__all__: list[str] = [
    "GuardBlockedPayload",
    "GuardFlaggedPayload",
    "GuardPolicy",
]


class GuardPolicy:
    """Runtime enforcement policy for content guardrails.

    Wraps user-supplied checker callables and produces the appropriate
    :class:`GuardBlockedPayload` or :class:`GuardFlaggedPayload` — or
    ``None`` when no violation is detected.

    Parameters
    ----------
    input_checker:
        Callable ``(input_hash: str) -> Optional[GuardBlockedPayload]``.
        Return a :class:`GuardBlockedPayload` to block the input, or
        ``None`` to allow it.
    output_checker:
        Callable ``(output_hash: str) -> Optional[GuardFlaggedPayload]``.
        Return a :class:`GuardFlaggedPayload` to flag the output, or
        ``None`` to pass it.
    fail_closed:
        When ``True`` and a checker is *not* configured for a direction,
        every input/output is blocked/flagged with a default violation
        payload.  Default ``False`` (fail-open — unconfigured checkers
        allow everything).

    Example::

        def my_input_check(h: str) -> Optional[GuardBlockedPayload]:
            if h in blocklist:
                return GuardBlockedPayload(
                    policy_id="p1", policy_name="blocklist",
                    input_hash=h, violation_types=["blocked_content"]
                )
            return None

        policy = GuardPolicy(input_checker=my_input_check)
        result = policy.check_input(sha256_hex)
        if result is not None:
            # input was blocked
            ...
    """

    def __init__(
        self,
        *,
        input_checker: Optional[Callable[[str], Optional[GuardBlockedPayload]]] = None,
        output_checker: Optional[Callable[[str], Optional[GuardFlaggedPayload]]] = None,
        fail_closed: bool = False,
    ) -> None:
        self._input_checker = input_checker
        self._output_checker = output_checker
        self._fail_closed = fail_closed

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def check_input(self, input_hash: str) -> Optional[GuardBlockedPayload]:
        """Run the input checker against *input_hash*.

        Parameters
        ----------
        input_hash:
            SHA-256 hex digest (or equivalent fingerprint) of the input
            to inspect.

        Returns
        -------
        :class:`GuardBlockedPayload` if the input should be blocked,
        ``None`` if it is permitted.
        """
        if self._input_checker is not None:
            return self._input_checker(input_hash)
        if self._fail_closed:
            return GuardBlockedPayload(
                policy_id="guard-policy",
                policy_name="GuardPolicy (fail-closed)",
                input_hash=input_hash,
                violation_types=["no_checker_configured"],
                severity="high",
            )
        return None

    def check_output(self, output_hash: str) -> Optional[GuardFlaggedPayload]:
        """Run the output checker against *output_hash*.

        Parameters
        ----------
        output_hash:
            SHA-256 hex digest (or equivalent fingerprint) of the output
            to inspect.

        Returns
        -------
        :class:`GuardFlaggedPayload` if the output should be flagged,
        ``None`` if it passes.
        """
        if self._output_checker is not None:
            return self._output_checker(output_hash)
        if self._fail_closed:
            return GuardFlaggedPayload(
                policy_id="guard-policy",
                policy_name="GuardPolicy (fail-closed)",
                output_hash=output_hash,
                flag_types=["no_checker_configured"],
                severity="medium",
            )
        return None

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"GuardPolicy(input_checker={self._input_checker!r}, "
            f"output_checker={self._output_checker!r}, "
            f"fail_closed={self._fail_closed!r})"
        )

