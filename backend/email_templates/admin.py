"""
📧 EMAIL TEMPLATES - Admin template (COMPACT)
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class BookingEmailData:
    salon_name: str
    client_full_name: str
    client_phone: str
    client_email: str
    service_title: str
    service_details: Optional[str]  # osoba2, spa zone, varijanta...
    date_str: str
    time_str: str
    duration_min: Optional[int]
    price: Optional[float]  # final_price (for backwards compatibility)
    address_line: str
    contact_email: str
    contact_phone: str
    booking_type: str = "spa"  # spa or massage
    # Pricing fields for discount display
    original_price: Optional[float] = None
    discount_percent: Optional[int] = 0
    discount_amount: Optional[float] = None


# COMPACT ADMIN STYLES - minimal spacing
ADMIN_STYLES = {
    "font": "font-family:Arial,Helvetica,sans-serif;",
    "base": "font-size:14px; line-height:1.25; color:#111;",
    "h1": "margin:0 0 8px 0; font-size:22px; line-height:1.1; color:#333;",
    "section": "margin:0 0 10px 0;",
    "label": "font-weight:700; color:#111;",
    "value": "font-weight:400; color:#111;",
    "card": "padding:12px 14px; background:#ffffff; border:1px solid #e6e6e6; border-radius:12px;",
    "divider": "height:1px; background:#eee; margin:10px 0;",
    "table": "border-collapse:collapse; width:100%;",
    "tdL": "padding:4px 8px; vertical-align:top; font-weight:700; width:34%; color:#555; font-size:13px;",
    "tdR": "padding:4px 8px; vertical-align:top; font-size:13px;",
    "subheader": "font-size:13px; font-weight:700; margin:0 0 6px 0; color:#666;",
    "strikethrough": "text-decoration:line-through; color:#999;",
    "discount": "color:#e53935; font-weight:700;",
    "final": "color:#2e7d32; font-weight:700;",
}


def render_admin_email(d: BookingEmailData) -> tuple:
    """
    🔔 ADMIN EMAIL - COMPACT Internal notification
    Minimal spacing, no wasted space
    """
    S = ADMIN_STYLES
    
    subject = f"[NEW BOOKING] {d.service_title} - {d.date_str} {d.time_str} - {d.client_full_name}"
    
    # Build optional rows
    details_row = ""
    if d.service_details:
        details_row = f'''<tr>
          <td style="{S['tdL']}">Detalji:</td>
          <td style="{S['tdR']}">{d.service_details}</td>
        </tr>'''
    
    duration_row = ""
    if d.duration_min:
        duration_row = f'''<tr>
          <td style="{S['tdL']}">Trajanje:</td>
          <td style="{S['tdR']}">{d.duration_min} min</td>
        </tr>'''
    
    # Price display with discount
    price_row = ""
    if d.price or d.original_price:
        if d.discount_percent and d.discount_percent > 0 and d.original_price:
            # Show original (strikethrough) + discount + final
            price_row = f'''<tr>
          <td style="{S['tdL']}">Cena (orig):</td>
          <td style="{S['tdR']} {S['strikethrough']}">{d.original_price:,.0f} RSD</td>
        </tr>
        <tr>
          <td style="{S['tdL']}">Popust:</td>
          <td style="{S['tdR']} {S['discount']}">-{d.discount_percent}%</td>
        </tr>
        <tr>
          <td style="{S['tdL']}">Za naplatu:</td>
          <td style="{S['tdR']} {S['final']}">{d.price:,.0f} RSD</td>
        </tr>'''
        else:
            # No discount - just show price
            price_row = f'''<tr>
          <td style="{S['tdL']}">Cena:</td>
          <td style="{S['tdR']}">{d.price:,.0f} RSD</td>
        </tr>'''
    
    html = f'''<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="margin:0; padding:0;">
<div style="{S['font']} {S['base']} background:#f6f6f6; padding:14px;">
  <div style="max-width:520px; margin:0 auto; {S['card']}">

    <div style="{S['h1']}">🔔 Nova Rezervacija</div>

    <div style="{S['section']}">
      <table style="{S['table']}">
        <tr>
          <td style="{S['tdL']}">Tip:</td>
          <td style="{S['tdR']}">{d.booking_type.upper()}</td>
        </tr>
        <tr>
          <td style="{S['tdL']}">Usluga:</td>
          <td style="{S['tdR']}">{d.service_title}</td>
        </tr>
        {details_row}
        <tr>
          <td style="{S['tdL']}">Datum:</td>
          <td style="{S['tdR']}">{d.date_str}</td>
        </tr>
        <tr>
          <td style="{S['tdL']}">Vreme:</td>
          <td style="{S['tdR']}">{d.time_str}</td>
        </tr>
        {duration_row}
        {price_row}
      </table>
    </div>

    <div style="{S['divider']}"></div>

    <div style="{S['section']}">
      <div style="{S['subheader']}">👤 Podaci o klijentu</div>
      <table style="{S['table']}">
        <tr>
          <td style="{S['tdL']}">Ime:</td>
          <td style="{S['tdR']}">{d.client_full_name}</td>
        </tr>
        <tr>
          <td style="{S['tdL']}">Telefon:</td>
          <td style="{S['tdR']}"><a href="tel:{d.client_phone}" style="color:#111; text-decoration:none;">{d.client_phone}</a></td>
        </tr>
        <tr>
          <td style="{S['tdL']}">Email:</td>
          <td style="{S['tdR']}"><a href="mailto:{d.client_email}" style="color:#111; text-decoration:none;">{d.client_email}</a></td>
        </tr>
      </table>
    </div>

  </div>
  <p style="text-align:center; font-size:11px; color:#999; margin:10px 0 0 0;">Automatski generisano</p>
</div>
</body>
</html>'''
    
    return subject, html
