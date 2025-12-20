"""
📧 EMAIL TEMPLATES - Admin template
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
    price: Optional[float]
    address_line: str
    contact_email: str
    contact_phone: str
    booking_type: str = "spa"  # spa or massage


def render_admin_email(d: BookingEmailData) -> tuple:
    """
    🔔 ADMIN EMAIL - Internal notification
    Plain, informative, for staff
    """
    subject = f"[NEW BOOKING] {d.service_title} - {d.date_str} {d.time_str} - {d.client_full_name}"
    
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Nova Rezervacija - Admin</title>
</head>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background: #f5f5f5;">
    <div style="background: #fff; padding: 20px; border-radius: 8px; border-left: 4px solid #d4af37;">
        <h2 style="margin: 0 0 15px 0; color: #333;">🔔 Nova Rezervacija</h2>
        
        <table style="width: 100%; border-collapse: collapse;">
            <tr>
                <td style="padding: 8px 0; border-bottom: 1px solid #eee; font-weight: bold; width: 120px;">Tip:</td>
                <td style="padding: 8px 0; border-bottom: 1px solid #eee;">{d.booking_type.upper()}</td>
            </tr>
            <tr>
                <td style="padding: 8px 0; border-bottom: 1px solid #eee; font-weight: bold;">Usluga:</td>
                <td style="padding: 8px 0; border-bottom: 1px solid #eee;">{d.service_title}</td>
            </tr>
            {"<tr><td style='padding: 8px 0; border-bottom: 1px solid #eee; font-weight: bold;'>Detalji:</td><td style='padding: 8px 0; border-bottom: 1px solid #eee;'>" + d.service_details + "</td></tr>" if d.service_details else ""}
            <tr>
                <td style="padding: 8px 0; border-bottom: 1px solid #eee; font-weight: bold;">Datum:</td>
                <td style="padding: 8px 0; border-bottom: 1px solid #eee;">{d.date_str}</td>
            </tr>
            <tr>
                <td style="padding: 8px 0; border-bottom: 1px solid #eee; font-weight: bold;">Vreme:</td>
                <td style="padding: 8px 0; border-bottom: 1px solid #eee;">{d.time_str}</td>
            </tr>
            {"<tr><td style='padding: 8px 0; border-bottom: 1px solid #eee; font-weight: bold;'>Trajanje:</td><td style='padding: 8px 0; border-bottom: 1px solid #eee;'>" + str(d.duration_min) + " min</td></tr>" if d.duration_min else ""}
            {"<tr><td style='padding: 8px 0; border-bottom: 1px solid #eee; font-weight: bold;'>Cena:</td><td style='padding: 8px 0; border-bottom: 1px solid #eee;'>" + f"{d.price:,.0f}".replace(",", ".") + " RSD</td></tr>" if d.price else ""}
        </table>
        
        <h3 style="margin: 20px 0 10px 0; color: #666; font-size: 14px;">👤 PODACI O KLIJENTU</h3>
        <table style="width: 100%; border-collapse: collapse;">
            <tr>
                <td style="padding: 8px 0; border-bottom: 1px solid #eee; font-weight: bold; width: 120px;">Ime:</td>
                <td style="padding: 8px 0; border-bottom: 1px solid #eee;">{d.client_full_name}</td>
            </tr>
            <tr>
                <td style="padding: 8px 0; border-bottom: 1px solid #eee; font-weight: bold;">Telefon:</td>
                <td style="padding: 8px 0; border-bottom: 1px solid #eee;"><a href="tel:{d.client_phone}">{d.client_phone}</a></td>
            </tr>
            <tr>
                <td style="padding: 8px 0; font-weight: bold;">Email:</td>
                <td style="padding: 8px 0;"><a href="mailto:{d.client_email}">{d.client_email}</a></td>
            </tr>
        </table>
        
        <p style="margin-top: 20px; padding: 10px; background: #f9f9f9; border-radius: 4px; font-size: 12px; color: #666;">
            Ova poruka je automatski generisana. Za pitanja kontaktirajte recepciju.
        </p>
    </div>
</body>
</html>
"""
    return subject, html
