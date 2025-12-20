"""
📧 EMAIL TEMPLATES - Separate templates for Admin and Client
- Admin: Internal notification, plain style
- Client: Beautiful confirmation with salon branding
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


def render_client_email(d: BookingEmailData) -> tuple:
    """
    ✨ CLIENT EMAIL - Beautiful confirmation
    Branded, welcoming, with salon info and rules
    """
    subject = f"✅ Uspešno zakazano - {d.salon_name}"
    
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Potvrda Rezervacije - {d.salon_name}</title>
</head>
<body style="font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 0; background: #f4f4f4;">
    <div style="max-width: 640px; margin: 0 auto; background: #ffffff; border: 1px solid #ddd;">
        
        <!-- HEADER - Dark with gold accent -->
        <div style="padding: 24px; background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%); text-align: center;">
            <h1 style="margin: 0; font-size: 28px; color: #d4af37; font-weight: 300; letter-spacing: 2px;">
                {d.salon_name}
            </h1>
            <p style="margin: 8px 0 0 0; color: #888; font-size: 12px; letter-spacing: 1px;">
                AUTHENTIC THAI MASSAGE & SPA
            </p>
        </div>
        
        <!-- GREETING -->
        <div style="padding: 30px 24px 20px 24px;">
            <p style="font-size: 18px; margin: 0 0 8px 0; color: #333;">
                Poštovani/a <strong>{d.client_full_name}</strong>,
            </p>
            <p style="font-size: 20px; margin: 0; color: #2e7d32;">
                ✅ <strong>Vaša rezervacija je uspešno kreirana!</strong>
            </p>
        </div>
        
        <!-- BOOKING DETAILS BOX -->
        <div style="margin: 0 24px 20px 24px; padding: 20px; background: #fafafa; border-radius: 12px; border: 1px solid #eee;">
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="padding: 10px 0; font-size: 14px; color: #666; width: 100px;">Tretman:</td>
                    <td style="padding: 10px 0; font-size: 16px; font-weight: bold; color: #333;">{d.service_title}</td>
                </tr>
                {"<tr><td style='padding: 10px 0; font-size: 14px; color: #666;'>Detalji:</td><td style='padding: 10px 0; font-size: 14px; color: #555;'>" + d.service_details + "</td></tr>" if d.service_details else ""}
                <tr>
                    <td style="padding: 10px 0; font-size: 14px; color: #666;">Datum:</td>
                    <td style="padding: 10px 0; font-size: 16px; font-weight: bold; color: #333;">📅 {d.date_str}</td>
                </tr>
                <tr>
                    <td style="padding: 10px 0; font-size: 14px; color: #666;">Vreme:</td>
                    <td style="padding: 10px 0; font-size: 16px; font-weight: bold; color: #333;">🕐 {d.time_str}</td>
                </tr>
                {"<tr><td style='padding: 10px 0; font-size: 14px; color: #666;'>Trajanje:</td><td style='padding: 10px 0; font-size: 14px; color: #555;'>⏱ " + str(d.duration_min) + " minuta</td></tr>" if d.duration_min else ""}
                {"<tr><td style='padding: 10px 0; font-size: 14px; color: #666;'>Cena:</td><td style='padding: 10px 0; font-size: 16px; font-weight: bold; color: #d4af37;'>" + f"{d.price:,.0f}".replace(",", ".") + " RSD</td></tr>" if d.price else ""}
            </table>
        </div>
        
        <!-- IMPORTANT NOTICE -->
        <div style="margin: 0 24px 24px 24px; padding: 16px; border-left: 4px solid #d4af37; background: #fffdf5;">
            <p style="margin: 0 0 8px 0; font-weight: bold; color: #333;">📌 Važne napomene:</p>
            <ul style="margin: 0; padding-left: 18px; color: #555; font-size: 14px; line-height: 1.8;">
                <li>Molimo vas da stignete <strong>10 minuta pre</strong> zakazanog termina</li>
                <li>Otkazivanje je moguće <strong>minimum 4 sata</strong> unapred</li>
                <li>Za sve izmene, kontaktirajte nas telefonom</li>
            </ul>
        </div>
        
        <!-- FOOTER - Contact info -->
        <div style="padding: 20px 24px; background: #1a1a1a; color: #d4af37;">
            <table style="width: 100%;">
                <tr>
                    <td style="font-size: 14px; line-height: 1.8;">
                        📍 {d.address_line}<br/>
                        📞 <a href="tel:{d.contact_phone}" style="color: #d4af37; text-decoration: none;">{d.contact_phone}</a><br/>
                        📧 <a href="mailto:{d.contact_email}" style="color: #d4af37; text-decoration: none;">{d.contact_email}</a>
                    </td>
                </tr>
            </table>
            <p style="margin: 16px 0 0 0; font-size: 11px; color: #666; text-align: center;">
                Hvala vam što ste izabrali {d.salon_name}! 🙏
            </p>
        </div>
        
    </div>
</body>
</html>
"""
    return subject, html
