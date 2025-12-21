"""
📧 EMAIL ADAPTERS
Convert SPA/MASSAGE appointment data to shared ClientEmailModel

🔒 USES resolve_pricing FROM pricing_utils.py AS SINGLE SOURCE OF TRUTH
"""

from datetime import datetime
from typing import Optional, Any
from .client_shared import ClientEmailModel, LineItem, render_client_shared
import sys
sys.path.insert(0, '/app/backend')
from pricing_utils import resolve_pricing


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
    🔒 Uses resolve_pricing as single source of truth
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
    
    # 🔒 USE resolve_pricing AS SINGLE SOURCE OF TRUTH
    pricing = resolve_pricing(appt)
    original_total = pricing["original_total"]
    final_total = pricing["final_total"]
    discount_percent = pricing["discount_percent"]
    has_discount = pricing["has_discount"]
    
    if has_discount:
        # Show: Cena (orig) precrtano + Popust + Za naplatu
        items.append(LineItem("💰", "Cena (orig)", f"<s>{original_total:,}</s> RSD"))
        items.append(LineItem("🏷️", "Popust", f"-{discount_percent}%"))
        items.append(LineItem("✅", "Za naplatu", f"<b>{final_total:,}</b> RSD"))
    elif final_total:
        items.append(LineItem("💰", "Cena", f"{final_total:,} RSD"))
    
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
    🔒 Uses resolve_pricing as single source of truth
    """
    full_name = f"{appt.get('client_first_name', '')} {appt.get('client_last_name', '')}".strip()
    
    items = [
        LineItem("💆", "Tretman", appt.get('service_name') or 'Masaža'),
        LineItem("📅", "Datum", _format_date(appt.get('start_time'))),
        LineItem("🕐", "Vreme", _format_time(appt.get('start_time'))),
        LineItem("👤", "Ime", full_name),
        LineItem("📞", "Telefon", appt.get('client_phone') or 'N/A'),
    ]
    
    # 🔒 USE resolve_pricing AS SINGLE SOURCE OF TRUTH
    pricing = resolve_pricing(appt)
    original_total = pricing["original_total"]
    final_total = pricing["final_total"]
    discount_percent = pricing["discount_percent"]
    has_discount = pricing["has_discount"]
    
    if has_discount:
        # Show: Cena (orig) precrtano + Popust + Za naplatu
        items.append(LineItem("💰", "Cena (orig)", f"<s>{original_total:,}</s> RSD"))
        items.append(LineItem("🏷️", "Popust", f"-{discount_percent}%"))
        items.append(LineItem("✅", "Za naplatu", f"<b>{final_total:,}</b> RSD"))
    elif final_total:
        items.append(LineItem("💰", "Cena", f"{final_total:,} RSD"))
    
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
