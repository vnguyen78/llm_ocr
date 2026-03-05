from typing import List
from app.models.audit import AuditFlag, AuditSeverity
from app.models.claim import Claim

class AuditorService:
    """
    Service for performing Shadow Audit checks (Compliance).
    """
    
    def validate_claim(self, claim: Claim) -> List[AuditFlag]:
        """
        Runs all compliance checks on a claim.
        Current checks:
        1. Math Guard: detailed line items sum == total amount (±0.01)
        """
        flags = []
        flags.extend(self._check_math_guard(claim))
        return flags

    def _check_math_guard(self, claim: Claim) -> List[AuditFlag]:
        calculated_sum = 0.0
        parsed_total = None
        
        found_line_items = False
        found_total = False
        
        if not claim.pages:
            return []

        for page in claim.pages:
            for tile in page.tiles:
                # tile.extraction might be a list or direct object depending on loading,
                # but safer to iterate if it's a relationship.
                extractions = tile.extraction if isinstance(tile.extraction, list) else [tile.extraction]
                
                for extraction in extractions:
                    if not extraction or not extraction.raw_json:
                        continue
                        
                    raw_fields = extraction.raw_json.get("fields", {})
                    # Normalize: LLM might return list or dict
                    fields = {}
                    if isinstance(raw_fields, list):
                        for f in raw_fields:
                            if isinstance(f, dict) and "name" in f:
                                fields[f["name"]] = f
                    elif isinstance(raw_fields, dict):
                        fields = raw_fields
                    
                    # Accumulate Line Items
                    if "line_items" in fields:
                        items = fields["line_items"].get("value", [])
                        if items:
                            found_line_items = True
                            for item in items:
                                try:
                                    amount = float(item.get("amount", 0.0))
                                    calculated_sum += amount
                                except (ValueError, TypeError):
                                    continue
                    
                    # Find Total Amount
                    if "total_amount" in fields:
                        try:
                            val = fields["total_amount"].get("value")
                            if val is not None:
                                parsed_total = float(val)
                                found_total = True
                        except (ValueError, TypeError):
                            continue

        flags = []
        if found_line_items and found_total:
            diff = abs(calculated_sum - parsed_total)
            if diff > 0.01:
                flags.append(AuditFlag(
                    claim_id=claim.id,
                    code="MATH_MISMATCH",
                    description=f"Calculated sum {calculated_sum:.2f} does not match total {parsed_total:.2f}",
                    severity=AuditSeverity.CRITICAL
                ))
        
        return flags
