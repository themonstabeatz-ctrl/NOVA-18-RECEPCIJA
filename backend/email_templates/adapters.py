"""
📧 EMAIL ADAPTERS
Convert SPA/MASSAGE appointment data to shared ClientEmailModel
"""

from datetime import datetime
from typing import Optional, Any
from .client_shared import ClientEmailModel, LineItem, render_client_shared


def _format_date(dt: Any) -> str:
    """Format datetime to DD.MM.YYYY"""
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
            return dt.strftime('%d.%m.%Y')
        except:
            return dt
    elif isinstance(dt, datetime):
        return dt.strftime('%d.%m.%Y')
    return 'N/A'


def _format_time(dt: Any) -> str:
    """Format datetime to HH:MM"""
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
            return dt.strftime('%H:%M')
        except:
            return ''
    elif isinstance(dt, datetime):
        return dt.strftime('%H:%M')
    return ''


def build_client_email_for_spa(appt: dict) -> tuple:
    """
    🧖 SPA ADAPTER - Uses SAME template as MASSAGE!
    Only difference is the content (items)
    """
    full_name = f"{appt.get('client_first_name', '')} {appt.get('client_last_name', '')}".strip()
    
    items = [
        LineItem("💆", "Tretman", appt.get('service_name') or 'SPA')
    ]
    
    # Add service description/variant if exists
    if appt.get('service_description'):
        items.append(LineItem("📋", "Detalji", appt['service_description']))
    
    # Add SPA zone if exists
    spa_zone = appt.get('spa_zone')
    if spa_zone:
        items.append(LineItem("🧖", "SPA zona", spa_zone))
    
    # Add duration if exists
    duration = appt.get('duration_min')
    if duration:
        items.append(LineItem("⏱", "Trajanje", f"{duration} min"))
    
    # Add standard fields
    items.extend([
        LineItem("📅", "Datum", _format_date(appt.get('start_time'))),
        LineItem("🕐", "Vreme", _format_time(appt.get('start_time'))),
        LineItem("👤", "Ime", full_name),
        LineItem("📞", "Telefon", appt.get('client_phone') or 'N/A'),
    ])
    
    m = ClientEmailModel(
        salon_name="Bua Luang Thai Spa",
        client_full_name=full_name,
        title="Uspešno zakazano!",
        items=items,
        footer_note="Stignite 10 min pre termina. Otkazivanje 4h unapred.",
        contact_email="bualuangthailandspa@gmail.com",
        contact_phone="+381 62 625 500",
        address_line="Abebe Bikile 10A"
    )
    
    return render_client_shared(m)


def build_client_email_for_massage(appt: dict) -> tuple:
    """
    💆 MASSAGE ADAPTER - Uses SAME template as SPA!
    This is the original "MASAŽE" format
    """
    full_name = f"{appt.get('client_first_name', '')} {appt.get('client_last_name', '')}".strip()
    
    items = [
        LineItem("💆", "Tretman", appt.get('service_name') or 'Masaža'),
        LineItem("📅", "Datum", _format_date(appt.get('start_time'))),
        LineItem("🕐", "Vreme", _format_time(appt.get('start_time'))),
        LineItem("👤", "Ime", full_name),
        LineItem("📞", "Telefon", appt.get('client_phone') or 'N/A'),
    ]
    
    m = ClientEmailModel(
        salon_name="Bua Luang Thai Spa",
        client_full_name=full_name,
        title="Uspešno zakazano!",
        items=items,
        footer_note="Stignite 10 min pre termina. Otkazivanje 4h unapred.",
        contact_email="bualuangthailandspa@gmail.com",
        contact_phone="+381 62 625 500",
        address_line="Abebe Bikile 10A"
    )
    
    return render_client_shared(m)
