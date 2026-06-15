"""
Configurable lead scoring engine.

Takes a lead dict and applies a scoring rubric defined in config.
Returns the lead with lead_score, lead_tier, and scoring_notes added.

All default values live in DEFAULT_CONFIG (config_loader.py).
Config keys are guaranteed present by _merge_with_defaults().
"""

import re as _re


class LeadScorer:
    """Score and tier leads based on opportunity for specific services."""

    def __init__(self, config: dict, goal: str = "general"):
        """
        Args:
            config: Configuration dictionary.
            goal: The service being offered ('web', 'seo', 'ads', 'general').
                 This affects how the score is calculated (e.g., if goal is 'web',
                 NOT having a website is a high score).
        """
        self.config = config
        self.goal = goal.lower()
        scoring = config.get("scoring", {})
        self.weights = scoring.get("weights", {})
        self.tiers = scoring.get("tiers", {})
        self.base_score = scoring.get("base_score", 50)
        self.max_score = scoring.get("max_score", 100)

        bonuses = scoring.get("goal_bonuses", {})
        self._gb_web = bonuses.get("web", {})
        self._gb_seo = bonuses.get("seo", {})
        self._gb_ads = bonuses.get("ads", {})
        self._gb_general = bonuses.get("general", {})
        self._gb_auto = bonuses.get("automatizacion", {})
        self._gb_reservas = bonuses.get("reservas", {})
        self._gb_menus = bonuses.get("menus", {})
        self._gb_inventarios = bonuses.get("inventarios", {})
        self._gb_pos = bonuses.get("pos", {})

        self._build_industry_bonuses()
        self._build_premium_locations()

    def _build_industry_bonuses(self):
        """Map industry keywords to bonus scores for fast lookup."""
        self.industry_bonuses: list[tuple] = []
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

    def score(self, lead: dict) -> dict:
        """Apply scoring rubric to a single lead.

        The lead dict is returned with additional keys:
            - lead_score (int)
            - lead_tier (str: HOT/WARM/COOL/COLD)
            - scoring_notes (str)
        """
        score = self.base_score
        notes = []
        flags = {}

        # Industry bonus
        industry_text = (lead.get("industry", "") + " " + lead.get("google_type", "")).lower()
        for keyword, bonus, ind_name in self.industry_bonuses:
            if keyword in industry_text:
                score += bonus
                notes.append(f"Industry: {ind_name} (+{bonus})")
                break

        # Goal-based Opportunity Scoring (Inspired by kit-prospeccion)
        if self.goal == "web":
            if not lead.get("website"):
                bonus = self._gb_web.get("no_site_bonus", 40)
                score += bonus
                notes.append(f"No Website: Max opportunity for web design (+{bonus})")
                flags["needs_website"] = True
            else:
                penalty = self._gb_web.get("has_site_penalty", -10)
                score += penalty
                notes.append(f"Has Website: Lower opportunity for web design ({penalty})")

        elif self.goal == "seo":
            if lead.get("website"):
                # Basic check: if it has website but no active social
                if not lead.get("instagram_handle") and not lead.get("facebook_url"):
                    bonus = self._gb_seo.get("no_social_bonus", 20)
                    score += bonus
                    notes.append(f"Has web but no social: SEO/Marketing opportunity (+{bonus})")
                    flags["has_web_no_social"] = True

                # Check for other signals from analyzer if available
                audit = lead.get("audit_data", {})
                if audit:
                    seo = audit.get("seo", {})
                    if not seo.get("has_meta_description") or not seo.get("has_h1"):
                        bonus = self._gb_seo.get("poor_tech_bonus", 30)
                        score += bonus
                        notes.append(f"Poor technical SEO detected (+{bonus})")
                        flags["needs_seo"] = True
            else:
                penalty = self._gb_seo.get("no_site_penalty", -20)
                score += penalty
                notes.append(f"No website: Cannot sell SEO yet ({penalty})")

        elif self.goal == "ads":
            if lead.get("website"):
                bonus = self._gb_ads.get("has_site_bonus", 20)
                score += bonus
                notes.append(f"Has web: Ready for Ads traffic (+{bonus})")

            rating = lead.get("google_rating")
            threshold = self._gb_ads.get("low_rating_threshold", 4.2)
            if rating and isinstance(rating, (int, float)) and rating < threshold:
                bonus = self._gb_ads.get("low_rating_bonus", 15)
                score += bonus
                notes.append(f"Rating < {threshold} ({rating}): Needs reputation boost (+{bonus})")

        elif self.goal == "automatizacion":
            gb = self._gb_auto
            if not lead.get("website"):
                bonus = gb.get("no_site_bonus", 40)
                score += bonus
                notes.append(f"No website: automation opportunity (+{bonus})")
                flags["needs_website"] = True

            # Check booking — from audit_data if available, or from booking_links field
            audit = lead.get("audit_data", {})
            has_booking = (
                audit.get("booking", {}).get("has_booking") or
                bool(lead.get("booking_links"))
            )
            if not has_booking:
                bonus = gb.get("no_booking_bonus", 30)
                score += bonus
                notes.append(f"No booking system (+{bonus})")
            elif lead.get("website") and not has_booking:
                bonus = gb.get("has_site_no_booking_bonus", 15)
                score += bonus
                notes.append(f"Has site but no booking (+{bonus})")

            if not lead.get("whatsapp_link"):
                bonus = gb.get("no_whatsapp_bonus", 20)
                score += bonus
                notes.append(f"No WhatsApp: manual communication (+{bonus})")

        elif self.goal == "reservas":
            gb = self._gb_reservas
            audit = lead.get("audit_data", {})
            has_booking = (
                audit.get("booking", {}).get("has_booking") or
                bool(lead.get("booking_links"))
            )

            if has_booking:
                penalty = gb.get("has_booking_penalty", -30)
                score += penalty
                notes.append(f"Already has booking ({penalty})")
            else:
                bonus = gb.get("no_booking_bonus", 40)
                score += bonus
                notes.append(f"No booking: reservation system opportunity (+{bonus})")

                if lead.get("website"):
                    bonus2 = gb.get("has_site_no_booking_bonus", 20)
                    score += bonus2
                    notes.append(f"Has site, add booking (+{bonus2})")

            # Service industry bonus
            industry = (lead.get("industry") or "").lower()
            service_keywords = ["barbería", "barberia", "peluquería", "spa", "estética", "belleza",
                                "salud", "bienestar", "clínica", "masajes", "veterinaria", "mascotas"]
            if any(kw in industry for kw in service_keywords):
                bonus = gb.get("service_industry_bonus", 15)
                score += bonus
                notes.append(f"Service industry (+{bonus})")

        elif self.goal == "menus":
            gb = self._gb_menus
            industry = (lead.get("industry") or "").lower()
            food_keywords = ["cafetería", "café", "restaurante", "restaurant",
                             "comida", "panadería", "pastelería", "food",
                             "heladería", "helado", "postres", "rotisería",
                             "pizzería", "sushi", "empanadas"]
            # Use word-boundary matching to avoid false positives (e.g. "bar" in "barbería")
            industry_words = set(_re.split(r"[,\s]+", industry))
            is_food = any(kw in industry_words for kw in food_keywords)

            if is_food:
                bonus = gb.get("food_industry_bonus", 35)
                score += bonus
                notes.append(f"Food industry (+{bonus})")
            else:
                penalty = gb.get("non_food_penalty", -10)
                score += penalty
                notes.append(f"Non-food industry ({penalty})")

            audit = lead.get("audit_data", {})
            content = audit.get("content", {})
            has_prices = content.get("has_prices", False)
            has_gallery = content.get("has_gallery", False)

            if lead.get("website"):
                if not has_prices:
                    bonus = gb.get("no_prices_bonus", 30)
                    score += bonus
                    notes.append(f"No prices on website (+{bonus})")
                if not has_gallery:
                    bonus = gb.get("no_gallery_bonus", 20)
                    score += bonus
                    notes.append(f"No gallery on website (+{bonus})")
                if has_prices and has_gallery:
                    penalty = gb.get("mature_site_penalty", -20)
                    score += penalty
                    notes.append(f"Mature site: menus already present ({penalty})")

        elif self.goal == "inventarios":
            gb = self._gb_inventarios
            industry = (lead.get("industry") or "").lower()
            retail_keywords = ["tienda", "retail", "minimarket", "ferretería", "almacén",
                               "boutique", "farmacia", "supermercado", "librería", "despensa"]
            is_retail = any(kw in industry for kw in retail_keywords)

            if is_retail:
                bonus = gb.get("retail_industry_bonus", 30)
                score += bonus
                notes.append(f"Retail industry (+{bonus})")

            if lead.get("website"):
                bonus = gb.get("has_site_bonus", 20)
                score += bonus
                notes.append(f"Has website (+{bonus})")

                audit = lead.get("audit_data", {})
                tech = audit.get("tech_stack", [])
                basic_cms = any(cms in str(tech) for cms in ["UENI", "Custom", "Unknown", "Wix", "MiNegocio"])
                if basic_cms:
                    bonus = gb.get("basic_cms_bonus", 15)
                    score += bonus
                    notes.append(f"Basic CMS detected (+{bonus})")

            has_booking = (
                lead.get("audit_data", {}).get("booking", {}).get("has_booking") or
                bool(lead.get("booking_links"))
            )
            if has_booking:
                penalty = gb.get("has_booking_penalty", -10)
                score += penalty
                notes.append(f"Already has digital tools ({penalty})")

        elif self.goal == "pos":
            gb = self._gb_pos
            has_phone = bool(lead.get("phone"))
            has_whatsapp = bool(lead.get("whatsapp_link"))

            if has_phone and not has_whatsapp:
                bonus = gb.get("phone_no_whatsapp_bonus", 30)
                score += bonus
                notes.append(f"Phone orders, no WhatsApp (+{bonus})")

            if not lead.get("website"):
                bonus = gb.get("no_site_bonus", 25)
                score += bonus
                notes.append(f"No website: POS opportunity (+{bonus})")
            else:
                audit = lead.get("audit_data", {})
                contact = audit.get("contact", {})
                if not contact.get("has_contact_form"):
                    bonus = gb.get("site_no_form_bonus", 20)
                    score += bonus
                    notes.append(f"Website without contact form (+{bonus})")

            # Digital maturity penalty
            if has_whatsapp and lead.get("website"):
                audit = lead.get("audit_data", {})
                has_form = audit.get("contact", {}).get("has_contact_form", False)
                if has_form:
                    penalty = gb.get("digital_mature_penalty", -15)
                    score += penalty
                    notes.append(f"Digitally mature — less POS need ({penalty})")

        else:  # General quality-based scoring
            if lead.get("website"):
                score += self.weights.get("website", 15)
                notes.append(f"Website (+{self.weights.get('website', 15)})")

            if lead.get("instagram_handle") or lead.get("facebook_url") or lead.get("linkedin_url"):
                score += self.weights.get("active_social", 20)
                notes.append(f"Social media (+{self.weights.get('active_social', 20)})")

        # Common signals
        # Multiple contact channels
        channel_fields = [
            "phone",
            "email",
            "website",
            "facebook_url",
            "instagram_handle",
            "linkedin_url",
        ]
        channel_count = sum(1 for f in channel_fields if lead.get(f))
        if channel_count >= 2:
            extra = self.weights.get("multiple_channels", 10)
            score += extra
            notes.append(f"{channel_count} channels (+{extra})")

        # WhatsApp contact (high conversion value, especially in Chile)
        if lead.get("whatsapp_link"):
            extra = self.weights.get("whatsapp", 10)
            score += extra
            notes.append(f"WhatsApp (+{extra})")

        # Premium location
        city = (lead.get("city") or "").lower()
        if city in self.premium_locations:
            extra = self.weights.get("premium_location", 10)
            score += extra
            notes.append(f"Premium location (+{extra})")

        # High rating as quality signal (only for general)
        if self.goal == "general":
            rating = lead.get("google_rating")
            threshold = self._gb_general.get("high_rating_threshold", 4.5)
            if rating and isinstance(rating, (int, float)) and rating >= threshold:
                extra = self.weights.get("pain_points", 15) // 3
                score += extra
                notes.append(f"Rating {rating}/5 (+{extra})")

        # Contact person found
        if lead.get("contact_person"):
            extra = self.weights.get("owner_info", 5)
            score += extra
            notes.append(f"Owner info (+{extra})")

        # Cap at max and determine tier
        final_score = max(0, min(score, self.max_score))
        tier = self._get_tier(final_score)

        return {
            **lead,
            "lead_score": final_score,
            "lead_tier": tier,
            "scoring_notes": " | ".join(notes) if notes else "Base score only",
            "needs_website": flags.get("needs_website", False),
            "needs_seo": flags.get("needs_seo", False),
            "has_web_no_social": flags.get("has_web_no_social", False),
        }

    def _get_tier(self, score: int) -> str:
        """Map a numeric score to a tier name."""
        for tier_name, (low, high) in self.tiers.items():
            if low <= score <= high:
                return tier_name.upper()  # type: ignore[no-any-return]
        return "COLD"

    @staticmethod
    def classify_industry(
        business_types: list[str],
        business_name: str,
        config: dict,
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
                    return industry["name"]  # type: ignore[no-any-return]

        if business_types:
            raw = business_types[0].replace("_", " ").title()
            return raw
        return "Unknown"

    @staticmethod
    def extract_city(address: str, config: dict) -> str:
        """Extract city name from a full address string."""
        if not address:
            return ""
        addr_lower = address.lower()

        # Remove postal codes (e.g., "8780000 La Granja" → "La Granja")
        cleaned = _re.sub(r"\b\d{5,7}\b", "", addr_lower).strip()

        # Check each part of the address against known locations
        parts = [p.strip() for p in cleaned.split(",")]

        # Try matching each part against known cities
        for loc in config.get("search", {}).get("locations", []):
            city_lower = loc["city"].lower()
            if city_lower in cleaned:
                return loc["city"]  # type: ignore[no-any-return]

        # Fallback: second-to-last part of comma-separated address
        if len(parts) >= 2:
            candidate = parts[-2].strip()
            # Strip numbers/zip remnants from candidate
            candidate = _re.sub(r"^\d+\s*", "", candidate).strip()
            return candidate if candidate else parts[-1].strip()
        return parts[0].strip() if parts else ""
