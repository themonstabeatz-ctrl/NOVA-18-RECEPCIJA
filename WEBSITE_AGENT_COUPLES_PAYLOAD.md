# 🔒 WEBSITE AGENT - Couples Booking Payload Specifikacija

**Datum**: 13. Decembar 2025  
**Status**: OBAVEZNO - Mora biti implementirano  
**Za**: Website Agent

---

## ⚠️ KRITIČNO: Couples Booking MORA Slati Discount Intent

Backend sada zahteva **eksplicitnu informaciju** o popustu u couples booking payload-u.

---

## ✅ OBAVEZAN PAYLOAD FORMAT

### Couples Booking BEZ Popusta (Default):

```json
{
  "client_first_name": "Ime",
  "client_last_name": "Prezime",
  "client_phone": "+381...",
  "client_email": "email@example.com",
  "start_time": "2025-12-25T10:00:00",
  "duration_type": 60,
  
  "discount_percentage": 0,
  "original_price": 8800,
  "final_price": 8800,
  "discount_amount": 0,
  
  "person1_services": [...],
  "person2_services": [...],
  "notes": "..."
}
```

**Ključna polja:**
- `discount_percentage: 0` - **OBAVEZNO** kada nema popusta
- `final_price = original_price` - **MORAJU** biti jednaki
- `discount_amount: 0`

---

### Couples Booking SA Popustom (Kampanja):

```json
{
  ...
  "discount_percentage": 15,
  "original_price": 8800,
  "final_price": 7480,
  "discount_amount": 1320,
  ...
}
```

**Ključna polja:**
- `discount_percentage: 15` - Eksplicitno navedeno
- `final_price < original_price` - Primenjuje se popust
- `discount_amount` - Iznos popusta

---

## 🔍 BACKEND LOGIKA (Za Razumevanje)

Backend koristi **PRIORITY SYSTEM**:

### PRIORITET 1: Eksplicitni Discount Intent
```python
# Ako website šalje discount_percentage:
if discount_percentage == 0:
    → FORCE NO DISCOUNT
    → final_price = original_price
    
if discount_percentage > 0:
    → APPLY DISCOUNT
    → final_price = calculated or sent from website
```

### PRIORITET 2: Default (Ako se ne pošalje)
```python
# Ako website NE ŠALJE discount_percentage:
→ DEFAULT = NO DISCOUNT (0%)
→ final_price = original_price
```

---

## 📋 BACKEND LOGOVI (Za Debugging)

### Bez Popusta:
```
🔍 COUPLES DISCOUNT OVERRIDE: request_discount=0.0
🔒 EXPLICIT NO DISCOUNT: applied=0.0, original=8800.0, final=8800.0
✅ FINAL SNAPSHOT: discount=0.0%, original=8800.0, final=8800.0
```

### Sa Popustom:
```
🔍 COUPLES DISCOUNT OVERRIDE: request_discount=15.0
💰 EXPLICIT DISCOUNT: applied=15.0%, original=8800.0, final=7480.0
✅ FINAL SNAPSHOT: discount=15.0%, original=8800.0, final=7480.0
```

---

## ✅ TEST DOKAZ

**Kreiran test appointment:**
```
ID: 1491ed98-f967-460d-97a5-6c0c3556f058
Client: FINALNI TestBezPopusta
Payload: discount_percentage = 0

Backend Response:
✅ snapshot_discount_percentage: 0.0%
✅ snapshot_original_price: 8800.0 RSD
✅ snapshot_price: 8800.0 RSD
```

**Potvrda: Backend vraća tačne vrednosti kada frontend šalje discount_percentage = 0**

---

## 🚨 GREŠKE KOJE WEBSITE MORA IZBEGAVATI

### ❌ POGREŠNO - Ne slati discount_percentage:
```json
{
  "original_price": 8800,
  "final_price": 8800
  // ❌ Fali discount_percentage
}
```

### ❌ POGREŠNO - Slati null:
```json
{
  "discount_percentage": null,  // ❌ Ne null, već 0
  "original_price": 8800,
  "final_price": 8800
}
```

### ✅ ISPRAVNO:
```json
{
  "discount_percentage": 0,  // ✅ Eksplicitno 0
  "original_price": 8800,
  "final_price": 8800,
  "discount_amount": 0
}
```

---

## 📊 TESTIRANJE

### Test 1: Bez Popusta
```bash
POST /api/book-couple-appointment
{
  "discount_percentage": 0,
  "original_price": 8800,
  "final_price": 8800
}

Očekivano u response:
✅ snapshot_discount_percentage: 0
✅ snapshot_price: 8800
✅ snapshot_original_price: 8800
```

### Test 2: Sa Popustom
```bash
POST /api/book-couple-appointment
{
  "discount_percentage": 15,
  "original_price": 8800,
  "final_price": 7480
}

Očekivano u response:
✅ snapshot_discount_percentage: 15
✅ snapshot_price: 7480
✅ snapshot_original_price: 8800
```

---

## ✅ CHECKLIST ZA WEBSITE AGENTA

Pre slanja couples booking request-a:

- [ ] Proveri da li postoji aktivna kampanja
- [ ] Ako NEMA kampanje: set `discount_percentage = 0`
- [ ] Ako IMA kampanja: set `discount_percentage = 15` (ili koliko je aktivan popust)
- [ ] Osiguraj da `final_price` = `original_price` kada je discount = 0
- [ ] Osiguraj da `discount_amount` = 0 kada je discount = 0
- [ ] Testiraj sa backend-om
- [ ] Proveri response da li vraća iste vrednosti

---

## 🔐 ZAKLJUČAK

**Website MORA eksplicitno slati `discount_percentage` u svakom couples booking request-u.**

- **Bez popusta**: `discount_percentage: 0`
- **Sa popustom**: `discount_percentage: 15` (ili trenutni aktivan procenat)

Backend više **NE KORISTI** default discount iz couples paketa u bazi.  
Backend **VERUJE** vrednostima koje website pošalje.

---

**KRAJ DOKUMENTA**  
**Backend implementacija: Završeno ✅**  
**Website implementacija: Pending**
