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
    
    # Add pricing with discount display
    pricing = appt.get('pricing', {})
    discount_percent = int(pricing.get('discount_percent') or appt.get('discount_percentage') or 0)
    
    # 🔒 PREFER NEW KEYS (original_total, final_total)
    final_total = pricing.get('final_total') or pricing.get('final_price') or appt.get('final_total') or appt.get('total')
    original_total = pricing.get('original_total') or pricing.get('original_price') or appt.get('original_total')
    
    # 🧮 REVERSE CALCULATION: Only if orig is missing but we have discount
    if original_total is None and discount_percent > 0 and final_total:
        original_total = int(round(final_total / (1 - discount_percent / 100)))
    
    # Determine if discount is actually applied
    has_discount = discount_percent > 0 and original_total and final_total and original_total > final_total
    
    if has_discount:
        # Show: Cena (orig) precrtano + Popust + Za naplatu
        items.append(LineItem("💰", "Cena (orig)", f"<s>{original_total:,.0f}</s> RSD"))
        items.append(LineItem("🏷️", "Popust", f"-{discount_percent}%"))
        items.append(LineItem("✅", "Za naplatu", f"<b>{final_total:,.0f}</b> RSD"))
    elif final_total:
        items.append(LineItem("💰", "Cena", f"{final_total:,.0f} RSD"))
    
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
    
    # 💰 Add pricing with discount display from snapshot
    pricing = appt.get('pricing', {})
    discount_percent = int(pricing.get('discount_percent') or appt.get('snapshot_discount_percentage') or 0)
    
    # Get final price first
    final_price = pricing.get('final_price') or appt.get('snapshot_price') or appt.get('total_price')
    
    # Get original price - if not available and discount exists, calculate it
    if pricing.get('original_price'):
        original_price = pricing.get('original_price')
    elif appt.get('snapshot_original_price') and appt.get('snapshot_original_price') > 0:
        original_price = appt.get('snapshot_original_price')
    elif discount_percent > 0 and final_price:
        # Reverse calculate: original = final / (1 - discount/100)
        original_price = int(round(final_price / (1 - discount_percent / 100)))
    else:
        original_price = appt.get('original_total_price') or final_price
    
    # Determine if discount is actually applied
    has_discount = discount_percent > 0 and original_price and final_price and original_price > final_price
    
    if has_discount:
        # Show: Cena (orig) precrtano + Popust + Za naplatu
        items.append(LineItem("💰", "Cena (orig)", f"<s>{original_price:,.0f}</s> RSD"))
        items.append(LineItem("🏷️", "Popust", f"-{discount_percent}%"))
        items.append(LineItem("✅", "Za naplatu", f"<b>{final_price:,.0f}</b> RSD"))
    elif final_price:
        items.append(LineItem("💰", "Cena", f"{final_price:,.0f} RSD"))
    
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
