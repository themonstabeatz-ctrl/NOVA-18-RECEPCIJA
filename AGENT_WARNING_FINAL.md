# ⚠️ FINALNO UPOZORENJE ZA SVE AGENTE

**Datum**: 13. Decembar 2025  
**Za**: Sve agente (Admin, Frontend, Backend, Testing, QA)  
**Od**: Vlasnik Sistema

---

## 🚨 OBAVEZNA PRAVILA - BEZ IZUZETAKA

### ❌ APSOLUTNO ZABRANJENO:

1. **Menjanje booking logike**
   - `POST /api/appointments`
   - `POST /api/book-couple-appointment`
   - Bilo koja logika u `server.py` između 🔒 markera

2. **Menjanje kalkulacije popusta**
   - `discount_percentage`
   - `final_price`
   - `original_price`
   - Bilo koje računanje cena

3. **Menjanje cena**
   - Service cene
   - Appointment cene
   - Discount proračuni

4. **Dodavanje novih endpointa** bez eksplicitnog odobrenja

5. **Menjanje stabilnih zona** označenih sa 🔒🔒🔒

---

## ✅ JEDINO DOZVOLJENO:

### Admin Panel Agent:
- **UI korekcije prikaza** (badge, label, text)
- Koristiti `appointment.snapshot_*` polja
- Dodati uslove za prikaz popusta
- **Fajlovi**: `Appointments.js`, `DashboardNew.js`, `Navbar.js`

### Frontend/Website Agent:
- Slati snapshot vrednosti sa frontenda
- **NIKADA** ne računati cene lokalno
- Koristiti backend response direktno

### Backend Agent:
- **SAMO** bug fix-evi izvan locked zona
- Email konfiguracija
- **NIKADA** menjati discount logiku

### Testing Agent:
- Testiranje postojećih funkcionalnosti
- **NIKADA** menjati kod

---

## 🔐 LOCKED ZONE - NE DIRAJ

```python
# 🔒🔒🔒 LOCKED ZONE START 🔒🔒🔒
# Ove zone NE SMEŠ dirati bez vlasnikovog odobrenja:

1. Single Appointment Booking (server.py linija ~712-832)
2. Couples Appointment Booking (server.py linija ~1051-1277)
3. Discount Logic (server.py linija ~1125-1144)
4. Email Notification (server.py linija ~2180-2303)
```

---

## ⚡ POSLEDICE KRŠENJA PRAVILA

**Svaka izmena izvan dozvoljenih oblasti rezultuje:**

1. **Automatski rollback** - Sve izmene će biti poništene
2. **Prekid saradnje** - Agent gubi pristup projektu
3. **Sistem lock** - Projekat se zaključava do ručne intervencije

---

## 📋 OBAVEZNA PROCEDURA

### Pre BILO KOJE izmene:

1. **Proveri**: Da li je izmena u dozvoljenoj zoni?
2. **Dokumentuj**: Šta menjam i zašto?
3. **Testiraj**: Lokalno pre commit-a
4. **Evidentiraj**: Git commit sa jasnom porukom

### Ako nisi siguran:

**STANI. PITAJ. NE NASTAVLJAJ.**

---

## 🎯 TRENUTNI ZADATAK

**Admin Panel Agent:**
- Ispraviti prikaz popusta
- Koristiti `appointment.snapshot_*` vrednosti
- Videti: `/app/ADMIN_UI_FIX_MANDATORY.md`

**Ostali agenti:**
- ČEKATI
- NE MENJATI ništa dok admin ne završi
- Pratiti uputstva iz LOCKDOWN_RULES.md

---

## ✅ POTVRDA RAZUMEVANJA

Svaki agent MORA da potvrdi da je razumeo ova pravila PRE nego što započne rad.

**Tvoja potvrda:**
```
✅ Razumeo sam da je ZABRANJENO menjati booking logiku
✅ Razumeo sam da je ZABRANJENO menjati popuste i cene
✅ Razumeo sam da su mi DOZVOLJENE samo UI korekcije u navedenim fajlovima
✅ Razumeo sam da svaka druga izmena = rollback i prekid
```

---

**ZABRANJENO je menjati booking logiku, popuste i cene.**  
**Dopuštene su samo UI korekcije prikaza (badge/label) i isključivo u navedenim fajlovima.**  
**Svaka druga izmena = rollback i prekid saradnje.**

---

**KRAJ UPOZORENJA**  
**Dokumentacija**: `/app/LOCKDOWN_RULES.md`, `/app/ADMIN_UI_FIX_MANDATORY.md`
