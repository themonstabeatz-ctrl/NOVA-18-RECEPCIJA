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
    import logging
    logger = logging.getLogger(__name__)
    
    # 🔥 DEBUG LOG
    logger.info(f"📧 BUILD_SPA_EMAIL input: pricing={appt.get('pricing')}, original_total={appt.get('original_total')}, final_total={appt.get('final_total')}, has_discount={appt.get('has_discount')}")
    
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
    💆 MASSAGE ADAPTER - Localized email based on lang field
    🌐 Supports: sr, en, ru, th
    🔒 Uses resolve_pricing as single source of truth
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # 🌐 LOCALIZATION DICTIONARIES
    TRANSLATIONS = {
        'sr': {
            'title': 'Uspešno zakazano!',
            'treatment': 'Tretman',
            'details': 'Detalji',
            'duration': 'Trajanje',
            'date': 'Datum',
            'time': 'Vreme',
            'name': 'Ime',
            'phone': 'Telefon',
            'price': 'Cena',
            'price_orig': 'Cena (orig)',
            'discount': 'Popust',
            'to_pay': 'Za naplatu',
            'footer': 'Stignite 10 min pre termina. Otkazivanje 4h unapred.',
            'minutes': 'min'
        },
        'en': {
            'title': 'Successfully Booked!',
            'treatment': 'Treatment',
            'details': 'Details',
            'duration': 'Duration',
            'date': 'Date',
            'time': 'Time',
            'name': 'Name',
            'phone': 'Phone',
            'price': 'Price',
            'price_orig': 'Price (orig)',
            'discount': 'Discount',
            'to_pay': 'To pay',
            'footer': 'Please arrive 10 min before your appointment. Cancellation 4h in advance.',
            'minutes': 'min'
        },
        'ru': {
            'title': 'Успешно забронировано!',
            'treatment': 'Процедура',
            'details': 'Детали',
            'duration': 'Продолжительность',
            'date': 'Дата',
            'time': 'Время',
            'name': 'Имя',
            'phone': 'Телефон',
            'price': 'Цена',
            'price_orig': 'Цена (ориг)',
            'discount': 'Скидка',
            'to_pay': 'К оплате',
            'footer': 'Пожалуйста, приходите за 10 минут до записи. Отмена за 4 часа.',
            'minutes': 'мин'
        },
        'th': {
            'title': 'จองสำเร็จแล้ว!',
            'treatment': 'การรักษา',
            'details': 'รายละเอียด',
            'duration': 'ระยะเวลา',
            'date': 'วันที่',
            'time': 'เวลา',
            'name': 'ชื่อ',
            'phone': 'โทรศัพท์',
            'price': 'ราคา',
            'price_orig': 'ราคา (เดิม)',
            'discount': 'ส่วนลด',
            'to_pay': 'ชำระเงิน',
            'footer': 'กรุณามาถึงก่อนนัดหมาย 10 นาที ยกเลิกล่วงหน้า 4 ชั่วโมง',
            'minutes': 'นาที'
        }
    }
    
    # Get language (default: sr)
    lang = appt.get('lang', 'sr') or 'sr'
    if lang not in TRANSLATIONS:
        lang = 'sr'
    t = TRANSLATIONS[lang]
    
    # 🔥 DEBUG LOG
    logger.info(f"📧 BUILD_MASSAGE_EMAIL lang={lang}, message={appt.get('message', 'N/A')[:50] if appt.get('message') else 'N/A'}...")
    
    full_name = f"{appt.get('client_first_name', '')} {appt.get('client_last_name', '')}".strip()
    
    # Get service name and details
    service_name = appt.get('service_name') or 'Masaža'
    message = appt.get('message')  # Localized message from frontend
    duration_min = appt.get('duration_min', 0)
    
    items = [
        LineItem("💆", t['treatment'], service_name),
    ]
    
    # Add details from message if available
    if message:
        items.append(LineItem("📋", t['details'], message))
    
    # Add duration
    if duration_min:
        items.append(LineItem("⏱", t['duration'], f"{duration_min} {t['minutes']}"))
    
    # Add standard fields
    items.extend([
        LineItem("📅", t['date'], _format_date(appt.get('start_time'))),
        LineItem("🕐", t['time'], _format_time(appt.get('start_time'))),
        LineItem("👤", t['name'], full_name),
        LineItem("📞", t['phone'], appt.get('client_phone') or 'N/A'),
    ])
    
    # 🔒 USE resolve_pricing AS SINGLE SOURCE OF TRUTH
    pricing = resolve_pricing(appt)
    original_total = pricing["original_total"]
    final_total = pricing["final_total"]
    discount_percent = pricing["discount_percent"]
    has_discount = pricing["has_discount"]
    
    if has_discount:
        # Show: Cena (orig) precrtano + Popust + Za naplatu
        items.append(LineItem("💰", t['price_orig'], f"<s>{original_total:,}</s> RSD"))
        items.append(LineItem("🏷️", t['discount'], f"-{discount_percent}%"))
        items.append(LineItem("✅", t['to_pay'], f"<b>{final_total:,}</b> RSD"))
    elif final_total:
        items.append(LineItem("💰", t['price'], f"{final_total:,} RSD"))
    
    m = ClientEmailModel(
        salon_name="Bua Luang Thai Spa",
        client_full_name=full_name,
        title=t['title'],
        items=items,
        footer_note=t['footer'],
        contact_email="bualuangthailandspa@gmail.com",
        contact_phone="+381 62 625 500",
        address_line="Abebe Bikile 10A"
    )
    
    return render_client_shared(m)



def build_client_email_for_couples(appt: dict) -> tuple:
    """
    👫 COUPLES MASSAGE ADAPTER - Localized email based on lang field
    🌐 Supports: sr, en, ru, th
    
    Shows:
    - Person 1 services + duration
    - Person 2 services + duration
    - Total price
    - Date/time
    - Client contact info
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # 🌐 LOCALIZATION DICTIONARIES FOR COUPLES
    TRANSLATIONS = {
        'sr': {
            'title': 'Masaža za parove - Uspešno zakazano!',
            'person1': 'Osoba 1',
            'person2': 'Osoba 2',
            'services': 'Usluge',
            'duration': 'Trajanje',
            'date': 'Datum',
            'time': 'Vreme',
            'name': 'Ime',
            'phone': 'Telefon',
            'price': 'Ukupna cena',
            'price_orig': 'Cena (orig)',
            'discount': 'Popust',
            'to_pay': 'Za naplatu',
            'footer': 'Stignite 10 min pre termina. Otkazivanje 4h unapred.',
            'minutes': 'min'
        },
        'en': {
            'title': 'Couples Massage - Successfully Booked!',
            'person1': 'Person 1',
            'person2': 'Person 2',
            'services': 'Services',
            'duration': 'Duration',
            'date': 'Date',
            'time': 'Time',
            'name': 'Name',
            'phone': 'Phone',
            'price': 'Total price',
            'price_orig': 'Price (orig)',
            'discount': 'Discount',
            'to_pay': 'To pay',
            'footer': 'Please arrive 10 min before your appointment. Cancellation 4h in advance.',
            'minutes': 'min'
        },
        'ru': {
            'title': 'Массаж для пар - Успешно забронировано!',
            'person1': 'Персона 1',
            'person2': 'Персона 2',
            'services': 'Услуги',
            'duration': 'Продолжительность',
            'date': 'Дата',
            'time': 'Время',
            'name': 'Имя',
            'phone': 'Телефон',
            'price': 'Общая цена',
            'price_orig': 'Цена (ориг)',
            'discount': 'Скидка',
            'to_pay': 'К оплате',
            'footer': 'Пожалуйста, приходите за 10 минут до записи. Отмена за 4 часа.',
            'minutes': 'мин'
        },
        'th': {
            'title': 'นวดคู่รัก - จองสำเร็จแล้ว!',
            'person1': 'บุคคลที่ 1',
            'person2': 'บุคคลที่ 2',
            'services': 'บริการ',
            'duration': 'ระยะเวลา',
            'date': 'วันที่',
            'time': 'เวลา',
            'name': 'ชื่อ',
            'phone': 'โทรศัพท์',
            'price': 'ราคารวม',
            'price_orig': 'ราคา (เดิม)',
            'discount': 'ส่วนลด',
            'to_pay': 'ชำระเงิน',
            'footer': 'กรุณามาถึงก่อนนัดหมาย 10 นาที ยกเลิกล่วงหน้า 4 ชั่วโมง',
            'minutes': 'นาที'
        }
    }
    
    # Get language (default: sr)
    lang = appt.get('lang', 'sr') or 'sr'
    if lang not in TRANSLATIONS:
        lang = 'sr'
    t = TRANSLATIONS[lang]
    
    # 🔥 DEBUG LOG
    logger.info(f"📧 BUILD_COUPLES_EMAIL lang={lang}, person1_count={len(appt.get('person1_services_snapshot', []))}, person2_count={len(appt.get('person2_services_snapshot', []))}")
    
    full_name = f"{appt.get('client_first_name', '')} {appt.get('client_last_name', '')}".strip()
    
    items = []
    
    # --- PERSON 1 SERVICES ---
    person1_services = appt.get('person1_services_snapshot', [])
    if person1_services:
        # Build person1 services string: "Service1 (60min), Service2 (30min)"
        p1_parts = []
        p1_total_duration = 0
        for svc in person1_services:
            name = svc.get('name', 'N/A')
            # Remove [PAROVI] prefix for cleaner display
            if name.startswith('[PAROVI] '):
                name = name[9:]
            dur = svc.get('duration', 0)
            p1_total_duration += dur
            p1_parts.append(f"{name} ({dur}{t['minutes']})")
        
        items.append(LineItem("👤", t['person1'], ', '.join(p1_parts)))
    
    # --- PERSON 2 SERVICES ---
    person2_services = appt.get('person2_services_snapshot', [])
    if person2_services:
        # Build person2 services string
        p2_parts = []
        p2_total_duration = 0
        for svc in person2_services:
            name = svc.get('name', 'N/A')
            # Remove [PAROVI] prefix for cleaner display
            if name.startswith('[PAROVI] '):
                name = name[9:]
            dur = svc.get('duration', 0)
            p2_total_duration += dur
            p2_parts.append(f"{name} ({dur}{t['minutes']})")
        
        items.append(LineItem("👤", t['person2'], ', '.join(p2_parts)))
    
    # --- TOTAL DURATION ---
    total_duration = appt.get('duration_min', 0)
    if total_duration:
        items.append(LineItem("⏱", t['duration'], f"{total_duration} {t['minutes']}"))
    
    # Add standard fields
    items.extend([
        LineItem("📅", t['date'], _format_date(appt.get('start_time'))),
        LineItem("🕐", t['time'], _format_time(appt.get('start_time'))),
        LineItem("👤", t['name'], full_name),
        LineItem("📞", t['phone'], appt.get('client_phone') or 'N/A'),
    ])
    
    # --- PRICING ---
    # Get pricing from appointment data
    original_total = appt.get('original_total') or appt.get('snapshot_original_price') or 0
    final_total = appt.get('final_total') or appt.get('snapshot_price') or appt.get('discounted_price') or 0
    discount_percent = appt.get('discount_percentage') or appt.get('snapshot_discount_percentage') or 0
    has_discount = discount_percent > 0 and final_total < original_total
    
    if has_discount:
        # Show: Cena (orig) precrtano + Popust + Za naplatu
        items.append(LineItem("💰", t['price_orig'], f"<s>{int(original_total):,}</s> RSD"))
        items.append(LineItem("🏷️", t['discount'], f"-{int(discount_percent)}%"))
        items.append(LineItem("✅", t['to_pay'], f"<b>{int(final_total):,}</b> RSD"))
    elif final_total:
        items.append(LineItem("💰", t['price'], f"{int(final_total):,} RSD"))
    
    m = ClientEmailModel(
        salon_name="Bua Luang Thai Spa",
        client_full_name=full_name,
        title=t['title'],
        items=items,
        footer_note=t['footer'],
        contact_email="bualuangthailandspa@gmail.com",
        contact_phone="+381 62 625 500",
        address_line="Abebe Bikile 10A"
    )
    
    return render_client_shared(m)
