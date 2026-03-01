"""llm_toolkit_schema.namespaces.template — Prompt template payload types.

Classes
-------
TemplateRenderedPayload
    ``llm.template.rendered`` — a template was rendered successfully.
VariableMissingPayload
    ``llm.template.variable.missing`` — required variables were absent.
TemplateValidationFailedPayload
    ``llm.template.validation.failed`` — the template itself failed static
    validation (distinct from :class:`~llm_toolkit_schema.namespaces.fence.FenceValidationFailedPayload`,
    which validates *rendered output*).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Collection, Dict, List, Optional, Union


@dataclass(frozen=True)
class TemplateRenderedPayload:
    """Payload for ``llm.template.rendered``.

    Parameters
    ----------
    template_id:
        Unique identifier for the template.
    template_version:
        Version string for the template, e.g. ``"2.1.0"``.
    variable_count:
        Number of variables that were substituted during rendering.
    render_duration_ms:
        Optional wall-clock render time in milliseconds.
    output_length:
        Optional character length of the rendered output.
    """

    template_id: str
    template_version: str
    variable_count: int
    render_duration_ms: Optional[float] = None
    output_length: Optional[int] = None

    # -----------------------------------------------------------------
    # Validation
    # -----------------------------------------------------------------

    def __post_init__(self) -> None:
        if not self.template_id or not isinstance(self.template_id, str):
            raise ValueError("TemplateRenderedPayload.template_id must be a non-empty string")
        if not self.template_version or not isinstance(self.template_version, str):
            raise ValueError("TemplateRenderedPayload.template_version must be a non-empty string")
        if not isinstance(self.variable_count, int) or self.variable_count < 0:
            raise ValueError("TemplateRenderedPayload.variable_count must be a non-negative int")
        if self.render_duration_ms is not None and (
            not isinstance(self.render_duration_ms, (int, float))
            or self.render_duration_ms < 0
        ):
            raise ValueError(
                "TemplateRenderedPayload.render_duration_ms must be a non-negative number or None"
            )
        if self.output_length is not None and (
            not isinstance(self.output_length, int) or self.output_length < 0
        ):
            raise ValueError(
                "TemplateRenderedPayload.output_length must be a non-negative int or None"
            )

    # -----------------------------------------------------------------
    # Serialisation
    # -----------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Return a plain dict suitable for ``Event.payload``."""
        result: Dict[str, Any] = {
            "template_id": self.template_id,
            "template_version": self.template_version,
            "variable_count": self.variable_count,
        }
        if self.render_duration_ms is not None:
            result["render_duration_ms"] = self.render_duration_ms
        if self.output_length is not None:
            result["output_length"] = self.output_length
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TemplateRenderedPayload":
        """Reconstruct a :class:`TemplateRenderedPayload` from a plain dict."""
        return cls(
            template_id=str(data["template_id"]),
            template_version=str(data["template_version"]),
            variable_count=int(data["variable_count"]),
            render_duration_ms=data.get("render_duration_ms"),
            output_length=(
                int(data["output_length"]) if data.get("output_length") is not None else None
            ),
        )


@dataclass(frozen=True)
class VariableMissingPayload:
    """Payload for ``llm.template.variable.missing``.

    Parameters
    ----------
    template_id:
        Unique identifier for the template that was being rendered.
    missing_variables:
        List of variable names that were required but absent from the
        render context.
    required_variables:
        Full list of variable names declared as required by the template.
    """

    template_id: str
    missing_variables: List[str]
    required_variables: List[str]

    # -----------------------------------------------------------------
    # Validation
    # -----------------------------------------------------------------

    def __post_init__(self) -> None:
        if not self.template_id or not isinstance(self.template_id, str):
            raise ValueError("VariableMissingPayload.template_id must be a non-empty string")
        if not isinstance(self.missing_variables, list) or not self.missing_variables:
            raise ValueError("VariableMissingPayload.missing_variables must be a non-empty list")
        for v in self.missing_variables:
            if not isinstance(v, str):
                raise TypeError("Each missing_variable must be a string")
        if not isinstance(self.required_variables, list) or not self.required_variables:
            raise ValueError(
                "VariableMissingPayload.required_variables must be a non-empty list"
            )
        for v in self.required_variables:
            if not isinstance(v, str):
                raise TypeError("Each required_variable must be a string")
        # Every missing variable must appear in required variables.
        missing_set = frozenset(self.missing_variables)
        required_set = frozenset(self.required_variables)
        extra = missing_set - required_set
        if extra:
            raise ValueError(
                f"missing_variables contains names not in required_variables: {extra}"
            )

    # -----------------------------------------------------------------
    # Serialisation
    # -----------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Return a plain dict suitable for ``Event.payload``."""
        return {
            "template_id": self.template_id,
            "missing_variables": list(self.missing_variables),
            "required_variables": list(self.required_variables),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VariableMissingPayload":
        """Reconstruct a :class:`VariableMissingPayload` from a plain dict."""
        return cls(
            template_id=str(data["template_id"]),
            missing_variables=list(data["missing_variables"]),
            required_variables=list(data["required_variables"]),
        )


@dataclass(frozen=True)
class TemplateValidationFailedPayload:
    """Payload for ``llm.template.validation.failed``.

    This event is raised when the *template definition itself* fails
    validation (e.g. syntax errors, undefined variables in the template
    body), as opposed to validation of rendered LLM output which is handled
    by :class:`~llm_toolkit_schema.namespaces.fence.FenceValidationFailedPayload`.

    Parameters
    ----------
    template_id:
        Unique identifier for the template that failed validation.
    validation_errors:
        Ordered list of human-readable error messages.
    validator:
        Optional identifier of the validator component that raised the
        errors.
    """

    template_id: str
    validation_errors: List[str]
    validator: Optional[str] = None

    # -----------------------------------------------------------------
    # Validation
    # -----------------------------------------------------------------

    def __post_init__(self) -> None:
        if not self.template_id or not isinstance(self.template_id, str):
            raise ValueError(
                "TemplateValidationFailedPayload.template_id must be a non-empty string"
            )
        if not isinstance(self.validation_errors, list) or not self.validation_errors:
            raise ValueError(
                "TemplateValidationFailedPayload.validation_errors must be a non-empty list"
            )
        for err in self.validation_errors:
            if not isinstance(err, str):
                raise TypeError("Each validation_error must be a string")

    # -----------------------------------------------------------------
    # Serialisation
    # -----------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Return a plain dict suitable for ``Event.payload``."""
        result: Dict[str, Any] = {
            "template_id": self.template_id,
            "validation_errors": list(self.validation_errors),
        }
        if self.validator is not None:
            result["validator"] = self.validator
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TemplateValidationFailedPayload":
        """Reconstruct a :class:`TemplateValidationFailedPayload` from a plain dict."""
        return cls(
            template_id=str(data["template_id"]),
            validation_errors=list(data["validation_errors"]),
            validator=data.get("validator"),
        )


__all__: list[str] = [
    "TemplateRenderedPayload",
    "VariableMissingPayload",
    "TemplateValidationFailedPayload",
    "TemplatePolicy",
]


class TemplatePolicy:
    """Runtime enforcement policy for prompt templates.

    Provides helpers for validating required variables before rendering and
    for validating the rendered output after rendering, producing the
    appropriate :class:`VariableMissingPayload`,
    :class:`TemplateRenderedPayload`, or
    :class:`TemplateValidationFailedPayload`.

    Parameters
    ----------
    template_id:
        Unique identifier for the template this policy governs.
    required_variables:
        Ordered list of variable names that *must* be supplied for
        rendering to succeed.
    template_version:
        Version string for the template, e.g. ``"1.0.0"`` (default).
    output_validator:
        Optional callable ``(rendered_output: str) -> Optional[str]``.
        Return ``None`` if the rendered output is valid, or a non-empty
        error message string if it is not.

    Example::

        policy = TemplatePolicy(
            template_id="system-prompt-v3",
            required_variables=["user_name", "context"],
            output_validator=lambda s: None if len(s) < 4096 else "output too long",
        )
        missing = policy.validate_variables({"user_name": "Alice"})
        if missing is not None:
            # emit an event with missing.to_dict() and abort
            ...
        result = policy.validate_output(rendered_text)
    """

    def __init__(
        self,
        template_id: str,
        required_variables: List[str],
        *,
        template_version: str = "1.0.0",
        output_validator: Optional[Callable[[str], Optional[str]]] = None,
    ) -> None:
        if not template_id or not isinstance(template_id, str):
            raise ValueError("TemplatePolicy.template_id must be a non-empty string")
        if not isinstance(required_variables, list):
            raise TypeError("TemplatePolicy.required_variables must be a list")
        for v in required_variables:
            if not isinstance(v, str):
                raise TypeError("Each required variable name must be a string")
        if output_validator is not None and not callable(output_validator):
            raise TypeError("TemplatePolicy.output_validator must be callable or None")
        self._template_id = template_id
        self._required_variables: List[str] = list(required_variables)
        self._template_version = template_version
        self._output_validator = output_validator

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def template_id(self) -> str:
        """Unique identifier for the governed template."""
        return self._template_id

    @property
    def required_variables(self) -> List[str]:
        """List of required variable names."""
        return list(self._required_variables)

    def validate_variables(
        self,
        provided: Collection[str],
    ) -> Optional[VariableMissingPayload]:
        """Check that all required variables are present in *provided*.

        Parameters
        ----------
        provided:
            Collection of variable names supplied for this render.

        Returns
        -------
        ``None`` if all required variables are satisfied, or a
        :class:`VariableMissingPayload` listing the absent names.
        """
        provided_set = frozenset(provided)
        missing = [v for v in self._required_variables if v not in provided_set]
        if not missing:
            return None
        return VariableMissingPayload(
            template_id=self._template_id,
            missing_variables=missing,
            required_variables=list(self._required_variables),
        )

    def validate_output(
        self,
        rendered_output: str,
        *,
        variable_count: Optional[int] = None,
        render_duration_ms: Optional[float] = None,
    ) -> Union[TemplateRenderedPayload, TemplateValidationFailedPayload]:
        """Validate the rendered output string.

        Runs the configured *output_validator* if one was supplied.  If no
        validator is configured the output is considered valid.

        Parameters
        ----------
        rendered_output:
            The string produced after variable substitution.
        variable_count:
            Number of variables substituted (used in the success payload;
            defaults to the number of declared required variables).
        render_duration_ms:
            Optional wall-clock render time for the success payload.

        Returns
        -------
        :class:`TemplateRenderedPayload` on success, or
        :class:`TemplateValidationFailedPayload` on failure.
        """
        if self._output_validator is not None:
            error = self._output_validator(rendered_output)
            if error:
                return TemplateValidationFailedPayload(
                    template_id=self._template_id,
                    validation_errors=[error],
                    validator="TemplatePolicy",
                )
        return TemplateRenderedPayload(
            template_id=self._template_id,
            template_version=self._template_version,
            variable_count=(
                variable_count
                if variable_count is not None
                else len(self._required_variables)
            ),
            render_duration_ms=render_duration_ms,
            output_length=len(rendered_output),
        )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"TemplatePolicy(template_id={self._template_id!r}, "
            f"required_variables={self._required_variables!r}, "
            f"template_version={self._template_version!r})"
        )

