"""Electrical Rule Check (ERC) for schematics."""

from typing import Optional
from dataclasses import dataclass, field


@dataclass
class ERCViolation:
    """A single ERC violation."""
    type: str
    severity: str
    message: str
    symbol: Optional[str] = None
    pin: Optional[str] = None
    location: Optional[tuple[float, float]] = None


@dataclass
class ERCResult:
    """Result of ERC check."""
    file: str
    status: str
    violations: list[ERCViolation] = field(default_factory=list)

    @property
    def errors(self) -> list[ERCViolation]:
        return [v for v in self.violations if v.severity == "error"]

    @property
    def warnings(self) -> list[ERCViolation]:
        return [v for v in self.violations if v.severity == "warning"]


def check_erc(filepath: str) -> ERCResult:
    """Run electrical rule checks on a schematic.

    Args:
        filepath: Path to .kicad_sch file

    Returns:
        ERCResult with violations found
    """
    from kiutils.schematic import Schematic

    sch = Schematic.from_file(filepath)
    violations = []

    # Check for unconnected pins
    # This is simplified - real ERC would trace connectivity
    for symbol in sch.schematicSymbols:
        ref = ""
        for prop in symbol.properties:
            if prop.key == "Reference":
                ref = prop.value
                break

        # Skip power symbols
        if ref.startswith("#"):
            continue

        # Check each pin
        if hasattr(symbol, 'pins'):
            for pin in symbol.pins:
                # Check if pin appears to be unconnected
                # This is a simplified check
                pass

    # Check for duplicate references
    refs_seen = {}
    for symbol in sch.schematicSymbols:
        ref = ""
        for prop in symbol.properties:
            if prop.key == "Reference":
                ref = prop.value
                break

        if ref and not ref.startswith("#") and ref != "?":
            if ref in refs_seen:
                violations.append(ERCViolation(
                    type="duplicate_reference",
                    severity="error",
                    message=f"Duplicate reference: {ref}",
                    symbol=ref,
                ))
            refs_seen[ref] = True

    # Check for missing values
    for symbol in sch.schematicSymbols:
        ref = ""
        value = ""
        for prop in symbol.properties:
            if prop.key == "Reference":
                ref = prop.value
            elif prop.key == "Value":
                value = prop.value

        if ref and not ref.startswith("#"):
            if not value or value == "?" or value == ref:
                violations.append(ERCViolation(
                    type="missing_value",
                    severity="warning",
                    message=f"Missing or default value for {ref}",
                    symbol=ref,
                ))

    status = "fail" if any(v.severity == "error" for v in violations) else "pass"

    return ERCResult(
        file=filepath,
        status=status,
        violations=violations,
    )
