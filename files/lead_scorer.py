#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Lead Scorer for Chile Lead Extractor Skill
Applies 0-100 point scoring rubric to qualify and prioritize leads
"""

import csv
import json
import sys
from datetime import datetime
from enum import Enum

class LeadTier(Enum):
    HOT = (80, 100, "🔥 Immediate outreach (next 24-48 hrs)")
    WARM = (60, 79, "🟡 Primary queue (this week)")
    COOL = (40, 59, "🟠 Secondary queue (batch send)")
    COLD = (0, 39, "❌ Archive or manual review")

class LeadScorer:
    def __init__(self):
        self.scoring_notes = []
    
    def score_lead(self, lead_dict):
        """Apply scoring rubric to single lead"""
        
        # Gate checks (disqualifying)
        if not self._gate_check(lead_dict):
            return {
                **lead_dict,
                'lead_score': 0,
                'lead_tier': 'DISQUALIFIED',
                'scoring_notes': 'Failed gate check (location, size, or active status)'
            }
        
        # Base score
        score = 50
        notes = []
        
        # Digital Presence (+45 max)
        has_active_social = self._check_active_social(lead_dict)
        has_website = self._check_website(lead_dict)
        has_whatsapp = self._check_whatsapp(lead_dict)
        
        if has_active_social:
            score += 20
            notes.append("Active social media (+20)")
        
        if has_website:
            score += 15
            notes.append("Website/online presence (+15)")
        
        if has_whatsapp:
            score += 10
            notes.append("WhatsApp Business enabled (+10)")
        
        # Engagement & Signals (+30 max)
        pain_point_signal = self._check_pain_points(lead_dict)
        multiple_channels = self._check_multiple_channels(lead_dict)
        owner_info = self._check_owner_info(lead_dict)
        
        if pain_point_signal:
            score += 15
            notes.append("Clear pain point signals (+15)")
        
        if multiple_channels:
            score += 10
            notes.append("Multiple contact channels (+10)")
        
        if owner_info:
            score += 5
            notes.append("Owner/founder info accessible (+5)")
        
        # Geographic/Operational (+25 max)
        good_location = self._check_premium_location(lead_dict)
        size_estimate = self._check_size(lead_dict)
        years_operating = self._check_stability(lead_dict)
        
        if good_location:
            score += 10
            notes.append("High-traffic area (+10)")
        
        if size_estimate:
            score += 8
            notes.append("Larger operational base (+8)")
        
        if years_operating:
            score += 7
            notes.append("Business stability (+7)")
        
        # Cap at 100
        final_score = min(score, 100)
        
        # Determine tier
        tier = self._get_tier(final_score)
        
        return {
            **lead_dict,
            'lead_score': final_score,
            'lead_tier': tier,
            'scoring_notes': ' | '.join(notes)
        }
    
    def _gate_check(self, lead):
        """Check disqualifying criteria"""
        # Must be in target region
        target_regions = ['Santiago', 'Valparaíso', 'Biobío', 'Los Ríos', 'Metropolitana']
        city = lead.get('city', '').strip()
        if not any(region.lower() in city.lower() for region in target_regions):
            # For Phase 1, be strict - could relax for Phase 2+
            pass  # Allow for now, could add strict filtering
        
        # Must be 1-10 employees
        employees = lead.get('employee_estimate', '').lower()
        if any(x in employees for x in ['11', '12', '13', '14', '15', '+', 'large', 'big']):
            return False
        
        # Must show some activity signal
        activity = (
            lead.get('posting_frequency', '').lower() or 
            lead.get('google_rating', '') or
            lead.get('website', '')
        )
        # Even if no activity, don't hard-gate - score will be low
        
        return True
    
    def _check_active_social(self, lead):
        """Check if has active social media (posts <30 days)"""
        freq = lead.get('posting_frequency', '').lower()
        return any(x in freq for x in ['daily', 'weekly', 'biweekly', 'recent', 'active'])
    
    def _check_website(self, lead):
        """Check if has website or online presence"""
        website = lead.get('website', '').strip()
        return bool(website) and website.lower() not in ['no', 'none', '']
    
    def _check_whatsapp(self, lead):
        """Check if WhatsApp Business enabled"""
        whatsapp = lead.get('whatsapp_enabled', '').lower()
        return whatsapp in ['yes', 'true', '1', 'si', 'sí']
    
    def _check_pain_points(self, lead):
        """Check for clear pain point signals"""
        pain_primary = lead.get('pain_point_primary', '').lower()
        pain_secondary = lead.get('pain_point_secondary', '').lower()
        
        pain_keywords = [
            'scheduling', 'agenda', 'turnos', 'inventory', 'inventario',
            'payments', 'pagos', 'accounting', 'contabilidad', 'hard to',
            'difícil', 'tedious', 'tedioso', 'manual', 'slow', 'lento'
        ]
        
        full_text = f"{pain_primary} {pain_secondary}".lower()
        return any(keyword in full_text for keyword in pain_keywords)
    
    def _check_multiple_channels(self, lead):
        """Check if multiple contact methods available"""
        channels = sum([
            bool(lead.get('phone', '').strip()),
            bool(lead.get('email', '').strip()),
            bool(lead.get('facebook_url', '').strip()),
            bool(lead.get('instagram_handle', '').strip()),
            bool(lead.get('website', '').strip())
        ])
        return channels >= 2
    
    def _check_owner_info(self, lead):
        """Check if owner/founder name is accessible"""
        person = lead.get('contact_person', '').strip()
        return bool(person) and person.lower() not in ['unknown', 'owner', 'n/a']
    
    def _check_premium_location(self, lead):
        """Check if in preferred neighborhood/high-traffic area"""
        neighborhood = lead.get('neighborhood', '').lower()
        premium_areas = [
            'las condes', 'providencia', 'lastarria', 'barrio brasil',
            'bellavista', 'ñuñoa', 'vitacura', 'la florida', 'santiago',
            'stgo centro'
        ]
        return any(area in neighborhood for area in premium_areas)
    
    def _check_size(self, lead):
        """Check if larger operational base (5+ employees)"""
        employees = lead.get('employee_estimate', '').lower()
        return any(x in employees for x in ['5', '6', '7', '8', '9', '10'])
    
    def _check_stability(self, lead):
        """Check if established business (2+ years)"""
        try:
            year = int(lead.get('operating_since', 0))
            return year <= 2023  # 2+ years as of 2025
        except:
            return False
    
    def _get_tier(self, score):
        """Get lead tier based on score"""
        for tier in LeadTier:
            if tier.value[0] <= score <= tier.value[1]:
                return tier.name
        return 'COLD'

class LeadExporter:
    @staticmethod
    def to_csv(leads, output_file):
        """Export leads to CSV"""
        if not leads:
            print("No leads to export")
            return
        
        fieldnames = [
            'lead_id', 'business_name', 'industry', 'contact_person',
            'phone', 'email', 'city', 'neighborhood', 'website',
            'facebook_url', 'instagram_handle', 'linkedin_url',
            'employee_estimate', 'operating_since', 'google_rating',
            'review_count', 'posting_frequency', 'whatsapp_enabled',
            'pain_point_primary', 'pain_point_secondary',
            'tech_readiness_score', 'lead_score', 'lead_tier',
            'source', 'date_found', 'contact_method', 'follow_up_date',
            'outreach_status', 'notes', 'scoring_notes'
        ]
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, restval='')
            writer.writeheader()
            for lead in leads:
                # Ensure all fields exist
                row = {field: lead.get(field, '') for field in fieldnames}
                writer.writerow(row)
        
        print(f"✓ Exported {len(leads)} leads to {output_file}")
    
    @staticmethod
    def to_json(leads, output_file):
        """Export leads to JSON"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({'leads': leads, 'count': len(leads), 'export_date': datetime.now().isoformat()}, 
                     f, ensure_ascii=False, indent=2)
        print(f"✓ Exported {len(leads)} leads to {output_file}")
    
    @staticmethod
    def summary_stats(leads):
        """Print summary statistics"""
        if not leads:
            return
        
        by_tier = {}
        by_industry = {}
        
        for lead in leads:
            tier = lead.get('lead_tier', 'UNKNOWN')
            industry = lead.get('industry', 'Unknown')
            
            by_tier[tier] = by_tier.get(tier, 0) + 1
            by_industry[industry] = by_industry.get(industry, 0) + 1
        
        print("\n" + "="*50)
        print("LEAD SCORING SUMMARY")
        print("="*50)
        print(f"\nTotal Leads: {len(leads)}")
        print(f"\nBy Tier:")
        for tier in ['HOT', 'WARM', 'COOL', 'COLD', 'DISQUALIFIED']:
            count = by_tier.get(tier, 0)
            if count > 0:
                pct = (count / len(leads)) * 100
                print(f"  {tier:15} : {count:4} ({pct:5.1f}%)")
        
        print(f"\nTop Industries:")
        sorted_industries = sorted(by_industry.items(), key=lambda x: x[1], reverse=True)
        for industry, count in sorted_industries[:5]:
            pct = (count / len(leads)) * 100
            print(f"  {industry:25} : {count:4} ({pct:5.1f}%)")
        
        print("\n" + "="*50 + "\n")

def process_leads(input_file, output_csv=None, output_json=None):
    """Main processing function"""
    leads = []
    
    # Read input CSV
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        leads = list(reader)
    
    print(f"📥 Loaded {len(leads)} leads from {input_file}")
    
    # Score each lead
    scorer = LeadScorer()
    scored_leads = [scorer.score_lead(lead) for lead in leads]
    
    # Export
    if output_csv:
        LeadExporter.to_csv(scored_leads, output_csv)
    
    if output_json:
        LeadExporter.to_json(scored_leads, output_json)
    
    # Stats
    LeadExporter.summary_stats(scored_leads)
    
    return scored_leads

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python lead_scorer.py <input.csv> [--output-csv output.csv] [--output-json output.json]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_csv = None
    output_json = None
    
    for i, arg in enumerate(sys.argv[2:]):
        if arg == '--output-csv' and i+2 < len(sys.argv):
            output_csv = sys.argv[i+3]
        elif arg == '--output-json' and i+2 < len(sys.argv):
            output_json = sys.argv[i+3]
    
    # Default outputs
    if not output_csv:
        output_csv = input_file.replace('.csv', '_scored.csv')
    if not output_json:
        output_json = input_file.replace('.csv', '_scored.json')
    
    process_leads(input_file, output_csv, output_json)
