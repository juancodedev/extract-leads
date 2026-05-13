"""
Configurable lead scoring engine.

Takes a lead dict and applies a scoring rubric defined in config.
Returns the lead with lead_score, lead_tier, and scoring_notes added.
"""
from typing import Dict, List, Optional


class LeadScorer:
    """Score and tier leads based on configurable weights and rules."""

    def __init__(self, config: Dict):
        self.config = config
        scoring = config.get("scoring", {})
        self.weights = scoring.get("weights", {})
        self.tiers = scoring.get("tiers", {})
        self.base_score = scoring.get("base_score", 50)
        self.max_score = scoring.get("max_score", 100)

        self._build_industry_bonuses()
        self._build_premium_locations()

    def _build_industry_bonuses(self):
        """Map industry keywords to bonus scores for fast lookup."""
        self.industry_bonuses: List[tuple] = []
        for industry in self.config.get("search", {}).get("industries", []):
            name = industry.get("name", "")
            bonus = industry.get("bonus_score", 0)
            for keyword in industry.get("keywords", []):
                self.industry_bonuses.append((keyword.lower(), bonus, name))

    def _build_premium_locations(self):
        """Build set of premium location names for fast lookup."""
        self.premium_locations: set = set()
        for loc in self.config.get("search", {}).get("locations", []):
            if loc.get("premium"):
                self.premium_locations.add(loc["city"].lower())

    def score(self, lead: Dict) -> Dict:
        """Apply scoring rubric to a single lead.

        The lead dict is returned with additional keys:
            - lead_score (int)
            - lead_tier (str: HOT/WARM/COOL/COLD)
            - scoring_notes (str)
        """
        score = self.base_score
        notes = []

        # Industry bonus
        industry_text = (
            (lead.get("industry", "") + " " + lead.get("google_type", ""))
            .lower()
        )
        for keyword, bonus, ind_name in self.industry_bonuses:
            if keyword in industry_text:
                score += bonus
                notes.append(f"Industry: {ind_name} (+{bonus})")
                break

        # Digital presence
        if lead.get("website"):
            score += self.weights.get("website", 15)
            notes.append(f"Website (+{self.weights.get('website', 15)})")

        if lead.get("instagram_handle") or lead.get("facebook_url") or lead.get("linkedin_url"):
            score += self.weights.get("active_social", 20)
            notes.append(f"Social media (+{self.weights.get('active_social', 20)})")

        # Multiple contact channels
        channel_fields = [
            "phone", "email", "website",
            "facebook_url", "instagram_handle", "linkedin_url",
        ]
        channel_count = sum(1 for f in channel_fields if lead.get(f))
        if channel_count >= 2:
            extra = self.weights.get("multiple_channels", 10)
            score += extra
            notes.append(f"{channel_count} channels (+{extra})")

        # Premium location
        city = (lead.get("city") or "").lower()
        if city in self.premium_locations:
            extra = self.weights.get("premium_location", 10)
            score += extra
            notes.append(f"Premium location (+{extra})")

        # High rating as quality signal
        rating = lead.get("google_rating")
        if rating and isinstance(rating, (int, float)) and rating >= 4.5:
            extra = self.weights.get("pain_points", 15) // 3
            score += extra
            notes.append(f"Rating {rating}/5 (+{extra})")

        # Contact person found
        if lead.get("contact_person"):
            extra = self.weights.get("owner_info", 5)
            score += extra
            notes.append(f"Owner info (+{extra})")

        # Cap at max and determine tier
        final_score = min(score, self.max_score)
        tier = self._get_tier(final_score)

        return {
            **lead,
            "lead_score": final_score,
            "lead_tier": tier,
            "scoring_notes": " | ".join(notes) if notes else "Base score only",
        }

    def _get_tier(self, score: int) -> str:
        """Map a numeric score to a tier name."""
        for tier_name, (low, high) in self.tiers.items():
            if low <= score <= high:
                return tier_name.upper()
        return "COLD"

    @staticmethod
    def classify_industry(
        business_types: List[str],
        business_name: str,
        config: Dict,
    ) -> str:
        """Classify a business into a target industry from config.

        Matches by checking if any industry keyword appears in
        the place types or business name.
        """
        name_lower = business_name.lower() if business_name else ""
        types_text = " ".join(t.lower() for t in business_types)
        combined = types_text + " " + name_lower

        for industry in config.get("search", {}).get("industries", []):
            for keyword in industry.get("keywords", []):
                if keyword.lower() in combined:
                    return industry["name"]

        if business_types:
            raw = business_types[0].replace("_", " ").title()
            return raw
        return "Unknown"

    @staticmethod
    def extract_city(address: str, config: Dict) -> str:
        """Extract city name from a full address string."""
        if not address:
            return ""
        addr_lower = address.lower()

        # Remove postal codes (e.g., "8780000 La Granja" → "La Granja")
        import re as _re
        cleaned = _re.sub(r'\b\d{5,7}\b', '', addr_lower).strip()

        # Check each part of the address against known locations
        parts = [p.strip() for p in cleaned.split(",")]

        # Try matching each part against known cities
        for loc in config.get("search", {}).get("locations", []):
            city_lower = loc["city"].lower()
            if city_lower in cleaned:
                return loc["city"]

        # Fallback: second-to-last part of comma-separated address
        if len(parts) >= 2:
            candidate = parts[-2].strip()
            # Strip numbers/zip remnants from candidate
            candidate = _re.sub(r'^\d+\s*', '', candidate).strip()
            return candidate if candidate else parts[-1].strip()
        return parts[0].strip() if parts else ""
