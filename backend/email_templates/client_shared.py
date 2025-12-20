"""
📧 SHARED CLIENT EMAIL TEMPLATE
One source of truth - used by BOTH SPA and MASSAGE
This is the "MASAŽE" design that SPA must also use.
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class LineItem:
    """Single line item in email details box"""
    icon: str      # emoji icon
    label: str     # field name
    value: str     # field value


@dataclass 
class ClientEmailModel:
    """Data model for client confirmation email"""
    salon_name: str
    client_full_name: str
    title: str                      # "Uspešno zakazano!"
    items: List[LineItem]           # tretman, datum, vreme, ime, telefon, etc.
    footer_note: str                # "Stignite 10 min pre..."
    contact_email: str
    contact_phone: str
    address_line: str
    website_url: str = "https://www.bualuangthaispa.rs"
    logo_url: str = "https://customer-assets.emergentagent.com/job_massage-booking-fix/artifacts/2m8jgqjv_Bua%20luang%20logo%20crna%20senka.png"
    background_url: str = "https://customer-assets.emergentagent.com/job_massage-booking-fix/artifacts/pfz1db04_podloga%20prazna.jpg"
    brand_bg: str = "#0d0d0d"
    brand_gold: str = "#c9a227"


def render_client_shared(m: ClientEmailModel) -> tuple:
    """
    🎨 SHARED CLIENT EMAIL RENDERER
    This is the MASAŽE design - SPA uses IDENTICAL layout!
    
    Returns: (subject, html)
    """
    subject = f"✅ Uspešno zakazano - {m.salon_name}"
    
    # Build items HTML rows
    items_html = ""
    for i, item in enumerate(m.items):
        border_style = 'border-top: 1px solid #eee;' if i > 0 else ''
        items_html += f'''
                                                        <tr>
                                                            <td style="padding: 8px 0; color: #333; font-size: 14px; {border_style}">
                                                                <span style="color: {m.brand_gold};">{item.icon}</span> <strong>{item.label}:</strong>
                                                                <span style="float: right; font-weight: normal;">{item.value}</span>
                                                            </td>
                                                        </tr>'''
    
    # THIS IS THE MASAŽE DESIGN - IDENTICAL FOR SPA
    html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #1a1a1a;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #1a1a1a;">
        <tr>
            <td align="center" style="padding: 10px;">
                <table width="450" cellpadding="0" cellspacing="0" style="background-color: {m.brand_bg}; border-radius: 10px; overflow: hidden; border: 1px solid {m.brand_gold};">
                    
                    <!-- Header with Logo and Background Image -->
                    <tr>
                        <td style="background-image: url('{m.background_url}'); background-size: cover; background-position: center; padding: 30px; text-align: center;">
                            <a href="{m.website_url}" style="text-decoration: none;">
                                <img src="{m.logo_url}" alt="{m.salon_name}" style="width: 180px; height: auto; display: block; margin: 0 auto;" />
                            </a>
                        </td>
                    </tr>
                    
                    <!-- Main Content - Dark with Gold Border -->
                    <tr>
                        <td style="background-color: #1a1a1a; padding: 20px;">
                            <table width="100%" style="background-color: {m.brand_bg}; border: 2px solid {m.brand_gold}; border-radius: 8px;">
                                <tr>
                                    <td style="padding: 20px;">
                                        <!-- Greeting -->
                                        <p style="color: {m.brand_gold}; font-size: 16px; margin: 0 0 10px 0;">
                                            Poštovani/a {m.client_full_name},
                                        </p>
                                        <p style="color: #4CAF50; font-size: 18px; font-weight: bold; margin: 0 0 20px 0;">
                                            ✅ {m.title}
                                        </p>
                                        
                                        <!-- Appointment Details Box - White Background -->
                                        <table width="100%" style="background-color: #ffffff; border-radius: 8px; margin-bottom: 15px;">
                                            <tr>
                                                <td style="padding: 15px;">
                                                    <table width="100%">
                                                        {items_html}
                                                    </table>
                                                </td>
                                            </tr>
                                        </table>
                                        
                                        <!-- Important Note - Yellow Background -->
                                        <table width="100%" style="background-color: #fffde7; border-radius: 5px; border-left: 4px solid {m.brand_gold};">
                                            <tr>
                                                <td style="padding: 12px; color: #5d4e37; font-size: 13px;">
                                                    {m.footer_note}
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Footer - Contact Info -->
                    <tr>
                        <td style="background-color: {m.brand_bg}; padding: 20px; text-align: center; border-top: 1px solid #333;">
                            <p style="color: {m.brand_gold}; margin: 0 0 10px 0; font-size: 14px;">
                                📧 {m.contact_email}
                            </p>
                            <p style="color: {m.brand_gold}; margin: 0 0 10px 0; font-size: 14px;">
                                📞 {m.contact_phone} | 📍 {m.address_line}
                            </p>
                            <p style="margin: 15px 0 10px 0;">
                                <a href="{m.website_url}" style="display: inline-block; background-color: {m.brand_gold}; color: {m.brand_bg}; text-decoration: none; padding: 10px 25px; border-radius: 5px; font-size: 14px; font-weight: bold;">
                                    🌐 www.bualuangthaispa.rs
                                </a>
                            </p>
                            <p style="color: #ff69b4; margin: 10px 0 0 0; font-size: 18px;">
                                🌸
                            </p>
                        </td>
                    </tr>
                    
                </table>
            </td>
        </tr>
    </table>
</body>
</html>'''
    
    return subject, html
