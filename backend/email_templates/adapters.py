"""
📧 EMAIL ADAPTERS
Convert SPA/MASSAGE appointment data to shared ClientEmailModel

🔒 USES resolve_pricing FROM pricing_utils.py AS SINGLE SOURCE OF TRUTH
🌐 SUPPORTS LOCALIZED SERVICE NAMES via name_i18n
"""

from datetime import datetime
from typing import Optional, Any, Dict
from .client_shared import ClientEmailModel, LineItem, render_client_shared
import sys
import re
sys.path.insert(0, '/app/backend')
from pricing_utils import resolve_pricing


# 🌐 SERVICE NAME TRANSLATIONS (for email localization)
SERVICE_TRANSLATIONS = {
    "Tradicionalna tajlandska masaža": {
        "sr": "Tradicionalna tajlandska masaža",
        "en": "Traditional Thai Massage",
        "ru": "Традиционный тайский массаж",
        "th": "นวดแผนไทยโบราณ"
    },
    "Aroma terapija": {
        "sr": "Aroma terapija",
        "en": "Aromatherapy Massage",
        "ru": "Ароматерапевтический массаж",
        "th": "นวดอโรม่าเทอราพี"
    },
    "Aromaterapija & topli kamen": {
        "sr": "Aromaterapija & topli kamen",
        "en": "Aromatherapy & Hot Stone",
        "ru": "Ароматерапия и горячие камни",
        "th": "อโรม่าเทอราพีและหินร้อน"
    },
    "Thai masaža sa toplim biljnim kompresama": {
        "sr": "Thai masaža sa toplim biljnim kompresama",
        "en": "Thai Massage with Hot Herbal Compress",
        "ru": "Тайский массаж с горячими травяными компрессами",
        "th": "นวดไทยพร้อมประคบสมุนไพรร้อน"
    },
    "Aroma sa toplim biljnim kompresama": {
        "sr": "Aroma sa toplim biljnim kompresama",
        "en": "Aromatherapy with Hot Herbal Compress",
        "ru": "Ароматерапия с горячими травяными компрессами",
        "th": "อโรม่าพร้อมประคบสมุนไพรร้อน"
    },
    "Opuštajuća masaža": {
        "sr": "Opuštajuća masaža",
        "en": "Relaxing Massage",
        "ru": "Расслабляющий массаж",
        "th": "นวดผ่อนคลาย"
    },
    "Masaža stopala": {
        "sr": "Masaža stopala",
        "en": "Foot Massage",
        "ru": "Массаж стоп",
        "th": "นวดเท้า"
    },
    "Masaža glave, vrata i ramena": {
        "sr": "Masaža glave, vrata i ramena",
        "en": "Head, Neck and Shoulder Massage",
        "ru": "Массаж головы, шеи и плеч",
        "th": "นวดศีรษะ คอ และไหล่"
    },
    "Masaža leđa": {
        "sr": "Masaža leđa",
        "en": "Back Massage",
        "ru": "Массаж спины",
        "th": "นวดหลัง"
    },
    "Masaža za parove": {
        "sr": "Masaža za parove",
        "en": "Couples Massage",
        "ru": "Массаж для пар",
        "th": "นวดคู่รัก"
    },
    "Deep tissue masaža": {
        "sr": "Deep tissue masaža",
        "en": "Deep Tissue Massage",
        "ru": "Глубокий массаж тканей",
        "th": "นวดเนื้อเยื่อลึก"
    },
    "Sportska masaža": {
        "sr": "Sportska masaža",
        "en": "Sports Massage",
        "ru": "Спортивный массаж",
        "th": "นวดกีฬา"
    }
}


def _translate_service_name(service_name: str, lang: str) -> str:
    """
    🌐 Translate service name to specified language.
    Handles [PAROVI] prefix and duration suffix.
    
    Args:
        service_name: Original service name (e.g., "[PAROVI] Tradicionalna tajlandska masaža - 60 min")
        lang: Target language code (sr, en, ru, th)
    
    Returns:
        Translated service name
    """
    if not service_name:
        return service_name
    
    # Default to Serbian if unknown language
    if lang not in ['sr', 'en', 'ru', 'th']:
        lang = 'sr'
    
    # Remove [PAROVI] prefix if present
    clean_name = service_name
    is_parovi = False
    if clean_name.startswith("[PAROVI] "):
        clean_name = clean_name[9:]
        is_parovi = True
    
    # Extract base name and duration
    base_match = re.match(r'^(.+?)\s*-\s*(\d+)\s*min', clean_name)
    if base_match:
        base_name = base_match.group(1).strip()
        duration = base_match.group(2)
    else:
        base_name = clean_name
        duration = None
    
    # Look up translation
    translations = SERVICE_TRANSLATIONS.get(base_name)
    if translations and lang in translations:
        translated_base = translations[lang]
    else:
        # Fallback to original
        translated_base = base_name
    
    # Build translated prefix
    if is_parovi:
        if lang == "en":
            prefix = "[COUPLES] "
        elif lang == "ru":
            prefix = "[ПАРЫ] "
        elif lang == "th":
            prefix = "[คู่รัก] "
        else:
            prefix = "[PAROVI] "
    else:
        prefix = ""
    
    # Build translated duration suffix
    if duration:
        if lang == "ru":
            suffix = f" - {duration} мин"
        elif lang == "th":
            suffix = f" - {duration} นาที"
        else:
            suffix = f" - {duration} min"
    else:
        suffix = ""
    
    return f"{prefix}{translated_base}{suffix}"


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
    🧖 SPA ADAPTER - Fully localized email based on lang field
    🌐 Supports: sr, en, ru, th
    🔒 Uses resolve_pricing as single source of truth
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # 🌐 LOCALIZATION - Get and normalize language
    from .client_shared import normalize_lang
    raw_lang = appt.get('lang', 'sr')
    lang = normalize_lang(raw_lang)
    
    # 🌐 LOCALIZATION DICTIONARIES FOR SPA
    TRANSLATIONS = {
        'sr': {
            'title': 'Uspešno zakazano!',
            'treatment': 'Tretman',
            'details': 'Detalji',
            'spa_zone': 'SPA zona',
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
            'spa_zone': 'SPA Zone',
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
            'spa_zone': 'СПА зона',
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
            'spa_zone': 'โซนสปา',
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
    
    # Get translations for current language
    if lang not in TRANSLATIONS:
        lang = 'sr'
    t = TRANSLATIONS[lang]
    
    # 🔥 DEBUG LOG
    logger.info(f"📧 BUILD_SPA_EMAIL input: lang={lang} (raw={raw_lang}), pricing={appt.get('pricing')}, original_total={appt.get('original_total')}, final_total={appt.get('final_total')}, has_discount={appt.get('has_discount')}")
    
    full_name = f"{appt.get('client_first_name', '')} {appt.get('client_last_name', '')}".strip()
    
    # 🌐 Translate SPA service name
    service_name_orig = appt.get('service_name') or 'SPA'
    card_id = appt.get('card_id')
    service_name = _translate_spa_service_name(service_name_orig, card_id, lang)
    
    logger.info(f"📧 SPA_SERVICE_TRANSLATED: '{service_name_orig}' -> '{service_name}' (lang={lang}, card_id={card_id})")
    
    items = [
        LineItem("💆", t['treatment'], service_name)
    ]
    
    # Add service description/variant if exists
    if appt.get('service_description'):
        items.append(LineItem("📋", t['details'], appt['service_description']))
    
    # Add SPA zone if exists
    spa_zone = appt.get('spa_zone')
    if spa_zone:
        items.append(LineItem("🧖", t['spa_zone'], spa_zone))
    
    # Add duration if exists
    duration = appt.get('duration_min')
    if duration:
        items.append(LineItem("⏱", t['duration'], f"{duration} {t['minutes']}"))
    
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
        address_line="Abebe Bikile 10A",
        lang=lang  # 🌐 Use normalized language
    )
    
    logger.info(f"📧 SPA_EMAIL_MODEL lang={lang}, title='{t['title']}', treatment_label='{t['treatment']}'")
    
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
    
    # Get service name and translate to selected language
    service_name_orig = appt.get('service_name') or 'Masaža'
    
    # 🌐 TRANSLATE SERVICE NAME - Check if name_i18n is available, otherwise use translation function
    name_i18n = appt.get('name_i18n')
    if name_i18n and lang in name_i18n:
        service_name = name_i18n[lang]
    else:
        service_name = _translate_service_name(service_name_orig, lang)
    
    message = appt.get('message')  # Localized message from frontend
    duration_min = appt.get('duration_min', 0)
    
    logger.info(f"📧 TRANSLATED SERVICE: '{service_name_orig}' -> '{service_name}' (lang={lang})")
    
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
        address_line="Abebe Bikile 10A",
        lang=lang  # 🌐 CRITICAL: Pass lang for greeting translation
    )
    
    logger.info(f"📧 MASSAGE_EMAIL_MODEL lang={lang}, greeting will use: {lang}")
    
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
            dur = svc.get('duration', 0)
            p1_total_duration += dur
            
            # 🌐 TRANSLATE SERVICE NAME
            translated_name = _translate_service_name(name, lang)
            # Remove prefix for cleaner display
            if translated_name.startswith('[PAROVI] '):
                translated_name = translated_name[9:]
            elif translated_name.startswith('[COUPLES] '):
                translated_name = translated_name[10:]
            elif translated_name.startswith('[ПАРЫ] '):
                translated_name = translated_name[7:]
            elif translated_name.startswith('[คู่รัก] '):
                translated_name = translated_name[9:]
            
            # Remove duration suffix if already in name (avoid duplication)
            import re
            translated_name = re.sub(r'\s*-\s*\d+\s*(min|мин|นาที)$', '', translated_name)
            
            p1_parts.append(f"{translated_name} ({dur}{t['minutes']})")
        
        items.append(LineItem("👤", t['person1'], ', '.join(p1_parts)))
    
    # --- PERSON 2 SERVICES ---
    person2_services = appt.get('person2_services_snapshot', [])
    if person2_services:
        # Build person2 services string
        p2_parts = []
        p2_total_duration = 0
        for svc in person2_services:
            name = svc.get('name', 'N/A')
            dur = svc.get('duration', 0)
            p2_total_duration += dur
            
            # 🌐 TRANSLATE SERVICE NAME
            translated_name = _translate_service_name(name, lang)
            # Remove prefix for cleaner display
            if translated_name.startswith('[PAROVI] '):
                translated_name = translated_name[9:]
            elif translated_name.startswith('[COUPLES] '):
                translated_name = translated_name[10:]
            elif translated_name.startswith('[ПАРЫ] '):
                translated_name = translated_name[7:]
            elif translated_name.startswith('[คู่รัก] '):
                translated_name = translated_name[9:]
            
            # Remove duration suffix if already in name (avoid duplication)
            import re
            translated_name = re.sub(r'\s*-\s*\d+\s*(min|мин|นาที)$', '', translated_name)
            
            p2_parts.append(f"{translated_name} ({dur}{t['minutes']})")
        
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
    
    # Add email if available
    client_email = appt.get('client_email')
    if client_email:
        items.append(LineItem("📧", "Email", client_email))
    
    # --- PRICING --- 🔒 USE SAME LOGIC AS MASSAGE
    # Get pricing from appointment data - try multiple sources
    original_total = appt.get('original_total') or appt.get('snapshot_original_price') or 0
    final_total = appt.get('final_total') or appt.get('snapshot_price') or appt.get('discounted_price') or 0
    discount_percent = appt.get('discount_percentage') or appt.get('snapshot_discount_percentage') or 0
    
    # Ensure numeric values
    try:
        original_total = int(float(original_total)) if original_total else 0
        final_total = int(float(final_total)) if final_total else 0
        discount_percent = int(float(discount_percent)) if discount_percent else 0
    except (ValueError, TypeError):
        original_total = 0
        final_total = 0
        discount_percent = 0
    
    has_discount = discount_percent > 0 and final_total < original_total
    
    logger.info(f"📧 COUPLES PRICING: original={original_total}, final={final_total}, discount={discount_percent}%, has_discount={has_discount}")
    
    if has_discount:
        # Show: Cena (orig) precrtano + Popust + Za naplatu - IDENTICAL TO MASSAGE/SPA
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
        address_line="Abebe Bikile 10A",
        lang=lang  # 🌐 CRITICAL: Pass lang for greeting translation
    )
    
    logger.info(f"📧 COUPLES_EMAIL_MODEL lang={lang}, greeting will use: {lang}")
    
    return render_client_shared(m)
