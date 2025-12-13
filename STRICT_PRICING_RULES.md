# 🔒 STRICT PRICING RULES - COUPLES BOOKING

**Datum**: 13. Decembar 2025  
**Status**: OBAVEZNO - Hard Fail Validacije  
**Prioritet**: CRITICAL

---

## ⚠️ OVO NISU PREDLOZI - OVO SU PRAVILA

Ova pravila se primenjuju **bez izuzetaka**. Kršenje pravila rezultuje **400 Error** i **odbijanjem booking-a**.

---

## A) RAZDVAJANJE KATEGORIJA - OBAVEZNO

### Pravilo:
**Couples booking MORA koristiti SAMO [PAROVI] services**

```python
# ✅ ISPRAVNO
final_price = price([PAROVI] Osoba1) + price([PAROVI] Osoba2)

# ❌ ZABRANJENO
final_price = price(Obična masaža Osoba1) + price(Obična masaža Osoba2)
```

### Backend NIKADA ne sme uzeti cenu iz:
- ❌ Običnih masaža (bez [PAROVI] prefiksa)
- ❌ "Master couples package" price
- ❌ Prvog paketa po duration
- ❌ Bilo kakvih "package" tabela
- ❌ Bilo kakvih add-on / room fee
- ❌ Hardcoded cena

### Validacija:
```python
if not service_name.startswith('[PAROVI]'):
    raise HTTPException(400, "Service must have [PAROVI] prefix")
```

---

## B) VALIDACIJA PREFIKSA - HARD FAIL

### Pravilo:
**SVE services za couples booking MORAJU početi sa "[PAROVI]"**

### Provera:
```python
# Person1 services
for service in person1_services:
    if not service.name.startswith('[PAROVI]'):
        → 400 ERROR
        → NE kreirati appointment

# Person2 services
for service in person2_services:
    if not service.name.startswith('[PAROVI]'):
        → 400 ERROR
        → NE kreirati appointment
```

### Error Response:
```json
{
  "detail": {
    "error": "COUPLES_BOOKING_VALIDATION_FAILED",
    "message": "All services for couples booking must have [PAROVI] prefix",
    "validation_errors": [
      "Person1 service 'Tradicionalna tajlandska' does NOT have [PAROVI] prefix"
    ]
  }
}
```

### Test Rezultat:
```
✅ TEST PASSED: Backend correctly rejected booking without [PAROVI] prefix
   Validation Errors:
     - Person1 service 'Tradicionalna tajlandska masaža - 120 min' does NOT have [PAROVI] prefix
     - Person2 service 'Aroma terapija - 120 min' does NOT have [PAROVI] prefix
```

---

## C) VALIDACIJA OKRUGLIH CENA - HARD FAIL

### Pravilo:
**SVE cene MORAJU biti okrugle (završavati na 00)**

Naše cene su:
- ✅ 4400, 5600, 6800, 8000, 13600...
- ❌ 8580, 7870, 5595.5, 6850...

### Provera:
```python
if price % 100 != 0:
    → LOG ERROR
    → 400 response
    → NE kreirati appointment
```

### Razlog:
Ako cena ne završava na 00, to znači:
- Mešanje [PAROVI] i običnih masaža
- Pogrešno računanje
- Korupcija podataka

### Error Response:
```json
{
  "detail": {
    "error": "COUPLES_PRICING_VALIDATION_FAILED",
    "message": "All prices must be round (ending with 00)",
    "validation_errors": [
      "Person1 service has non-round price: 6850 RSD (must end with 00)"
    ]
  }
}
```

---

## D) POPUSTI - TRENUTNO NEMA

### Pravilo:
**discount_percentage MORA biti 0 za couples**

```python
if discount_percentage != 0:
    → 400 ERROR
    → "Couples bookings do not support discounts"
```

### Zabrane:
- ❌ Nikad ne primenjivati popust iz običnih masaža na couples
- ❌ Nikad ne primenjivati default discount iz couples paketa
- ❌ Nikad ne primenjivati kampanje automatski

### Error Response:
```json
{
  "detail": {
    "error": "COUPLES_DISCOUNT_NOT_SUPPORTED",
    "message": "Couples bookings currently do not support discounts",
    "received_discount": 15
  }
}
```

---

## E) DEBUG LOG - OBAVEZAN

### Šta se loguje:
```
📋 ===== COUPLES BOOKING COMPLETE BREAKDOWN =====
   Appointment Type: COUPLES / MASAŽA ZA PAROVE
   
   Person1 Services:
     - ID: a22c297b-06d4-4f83-93b4-00a10766e479
       Name: [PAROVI] Aroma terapija - 120 min
       Price: 6800.0 RSD
       [PAROVI] prefix: ✅
   Person1 Subtotal: 6800.0 RSD
   
   Person2 Services:
     - ID: 812b0a80-3627-4328-a562-09290abfbba3
       Name: [PAROVI] Aromaterapija & topli kamen - 120 min
       Price: 7200.0 RSD
       [PAROVI] prefix: ✅
   Person2 Subtotal: 7200.0 RSD
   
   FINAL FORMULA: 6800.0 + 7200.0 = 14000.0 RSD
   Discount: 0.0% (0 - NO DISCOUNT)
   Final Price: 14000.0 RSD
   
   ✅ All validations passed:
      ✅ [PAROVI] prefix on all services
      ✅ Round prices (ending with 00)
      ✅ No discount applied
      ✅ Price calculated from components
📋 ===============================================
```

### Lokacija Loga:
`/var/log/supervisor/backend.err.log`

---

## 📊 TEST REZULTATI

### Test 1: Valid [PAROVI] Services ✅
```
Input:
  Person1: [PAROVI] Aroma terapija - 120 min (6800 RSD)
  Person2: [PAROVI] Aromaterapija & topli kamen - 120 min (7200 RSD)

Result:
  ✅ Booking created successfully
  ✅ Price: 14000 RSD (6800 + 7200)
  ✅ All validations passed
```

### Test 2: Invalid - No [PAROVI] Prefix ❌
```
Input:
  Person1: Tradicionalna tajlandska - 120 min (no prefix)
  Person2: Aroma terapija - 120 min (no prefix)

Result:
  ❌ 400 Error
  ❌ COUPLES_BOOKING_VALIDATION_FAILED
  ✅ Booking rejected (correct behavior)
```

### Test 3: Round Price Validation ✅
```
Scenario:
  If any service has non-round price (e.g., 6850 RSD)

Result:
  ❌ 400 Error
  ❌ COUPLES_PRICING_VALIDATION_FAILED
  ✅ Booking rejected (correct behavior)
```

---

## 🔐 GARANTIJE

### Što Backend Garantuje:

1. ✅ **[PAROVI] prefix** - Svi services moraju imati prefix
2. ✅ **Round prices** - Sve cene završavaju sa 00
3. ✅ **No discount** - discount_percentage = 0
4. ✅ **Component pricing** - Cena = Person1 + Person2
5. ✅ **Hard fail** - Kršenje pravila = 400 Error
6. ✅ **No data corruption** - Odbijanje pre upisa u bazu
7. ✅ **Detailed logs** - Svaki booking ima breakdown

### Što Backend NE Dozvoljava:

- ❌ Mešanje [PAROVI] i običnih services
- ❌ Non-round cene (ne završavaju sa 00)
- ❌ Hardcoded cene iz couples paketa
- ❌ Automatski popusti
- ❌ Add-on fees
- ❌ Room fees
- ❌ "Master package" pricing

---

## 📋 CHECKLIST ZA WEBSITE

Pre slanja couples booking:

- [ ] Proveri da SVI services imaju [PAROVI] prefix
- [ ] Proveri da SVE cene završavaju sa 00
- [ ] Postavi discount_percentage = 0
- [ ] NE šalji hardcoded cenu (backend će izračunati)
- [ ] Testiraj sa pravim [PAROVI] service ID-jevima

---

## 🚨 ŠTA RADITI AKO DOBIJEŠ 400 ERROR

### Error: COUPLES_BOOKING_VALIDATION_FAILED
**Razlog**: Service nema [PAROVI] prefix

**Rešenje**:
1. Proveri service_id koji šalješ
2. Koristi samo services sa [PAROVI] prefiksom
3. Ne koristi obične masaže za couples booking

### Error: COUPLES_PRICING_VALIDATION_FAILED
**Razlog**: Cena ne završava sa 00

**Rešenje**:
1. Proveri da li mešaš [PAROVI] i obične services
2. Proveri da li services u bazi imaju ispravne cene
3. Kontaktiraj backend agenta za DB proveru

### Error: COUPLES_DISCOUNT_NOT_SUPPORTED
**Razlog**: Pokušao si da primiš popust

**Rešenje**:
1. Postavi discount_percentage = 0
2. Ne primenjuj popuste na couples booking
3. Čekaj dok se ne uvedu kampanje

---

**KRAJ DOKUMENTA**  
**Implementacija: Završena ✅**  
**Testiranje: Potvrđeno ✅**  
**Status: PRODUCTION READY 🔒**
