"""
Shared booking domain definitions for lead enrichment and analysis.

Single source of truth for online booking/reservation system detection.
Both enricher.py and analyzer.py import from here.
"""

BOOKING_DOMAINS: dict[str, str] = {
    # From analyzer.py (20 entries) — human-readable names as keys
    "agendapro.com": "AgendaPro",
    "setmore.com": "Setmore",
    "tuu.cl": "TUU",
    "calendly.com": "Calendly",
    "acuityscheduling.com": "Acuity",
    "reservo.cl": "Reservo",
    "reservas.cl": "Reservas",
    "simplybook.me": "SimplyBook",
    "bookeo.com": "Bookeo",
    "youcanbook.me": "YouCanBook",
    "situdy.com": "Situdy",
    "turnero.cl": "Turnero",
    "timify.com": "Timify",
    "squareup.com/appointments": "Square Appointments",
    "wix.com/book": "Wix Bookings",
    "mibarbed.com": "MiBarbEd",
    "reservaenlinea.cl": "ReservaEnLinea",
    "agendaonline.cl": "AgendaOnline",
    "superbook": "SuperBook",
    "zenbooking": "ZenBooking",
    # Unique from enricher.py (excluded: "bookingsystem" — partial substring false positive)
    "appointmentplus.com": "AppointmentPlus",
}
# Union of analyzer (20) + enricher.appointmentplus.com (1) = 21 entries.
# Excluded: "bookingsystem" — generic term causing substring false positives.


BOOKING_SKIP: set[str] = {
    "terminos",
    "terms",
    "condiciones",
    "conditions",
    "privacy",
    "privacidad",
    "legal",
    "aviso-legal",
    "cookies",
    "blog",
    "faq",
    "ayuda",
    "help",
    "login",
    "registro",
    "register",
    "signin",
}
# Union of analyzer (17 terms) + enricher (13 terms) = 17 terms.
# enricher was missing: login, registro, register, signin.
