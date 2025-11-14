# 🎯 KONAČNO REŠENJE - Couple Booking Fix

## 🔴 IDENTIFIKOVANI PROBLEMI

### Problem 1: Endpoint Ne Postoji
Web sajt poziva: `POST /api/book-couple-appointment`  
**Ovaj endpoint NE POSTOJI** ni na web sajtu ni na booking sistemu!

### Problem 2: Nedostaje `therapist_id`
Payload ne sadrži obavezno `therapist_id` polje koje booking sistem zahteva.

---

## ✅ REŠENJE - Šta Web Sajt Agent Mora Da Uradi

### OPCIJA A: Kreiraj Backend Endpoint (PREPORUČENO)

Web sajt backend (`spa-booking-fix-1`) mora da ima endpoint koji proxy-uje na booking sistem.

#### 1. Kreiraj `/api/book-couple-appointment` endpoint

**Lokacija:** `/app/backend/server.py` (ili gde god je backend web sajta)

```python
from fastapi import APIRouter, HTTPException
import httpx
from pydantic import BaseModel
from typing import List

router = APIRouter()

# Booking sistem URL
BOOKING_SYSTEM_URL = "https://discount-fixer.preview.emergentagent.com"

class CoupleBookingRequest(BaseModel):
    client_first_name: str
    client_last_name: str
    client_phone: str
    client_email: str = None
    duration_type: int  # 60, 90, or 120
    person1_services: List[str]
    person2_services: List[str]
    start_time: str  # ISO format
    discount_couples_massage: float = 15.0

@router.post("/api/book-couple-appointment")
async def book_couple_appointment(booking: CoupleBookingRequest):
    """
    Proxy endpoint za couple booking
    Dodaje therapist_id i prosleđuje na booking sistem
    """
    
    # Učitaj prvog dostupnog terapeuta ili koristi default
    async with httpx.AsyncClient() as client:
        try:
            # Dobavi listu terapeuta
            therapists_response = await client.get(
                f"{BOOKING_SYSTEM_URL}/api/therapists"
            )
            therapists = therapists_response.json()
            
            if not therapists:
                raise HTTPException(status_code=500, detail="Nema dostupnih terapeuta")
            
            # Uzmi prvog terapeuta (ili implementiraj logiku za odabir)
            therapist_id = therapists[0]["id"]
            
            # Pripremi payload za booking sistem
            booking_payload = {
                "client_first_name": booking.client_first_name,
                "client_last_name": booking.client_last_name,
                "client_phone": booking.client_phone,
                "client_email": booking.client_email,
                "therapist_id": therapist_id,
                "duration_type": booking.duration_type,
                "person1_services": booking.person1_services,
                "person2_services": booking.person2_services,
                "start_time": booking.start_time,
                "status": "scheduled",
                "discount_couples_massage": booking.discount_couples_massage
            }
            
            # Pošalji na booking sistem
            response = await client.post(
                f"{BOOKING_SYSTEM_URL}/api/appointments/couple",
                json=booking_payload,
                timeout=30.0
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                error_detail = response.json()
                raise HTTPException(
                    status_code=response.status_code,
                    detail=error_detail
                )
                
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Greška pri komunikaciji sa booking sistemom: {str(e)}"
            )
```

#### 2. Registruj Router

```python
# U main server.py fajlu
from .couple_booking import router as couple_router

app.include_router(couple_router)
```

#### 3. Restart Backend

```bash
# Ako koristite supervisor
sudo supervisorctl restart backend

# Ili ako ručno
# Restart your backend server
```

---

### OPCIJA B: Frontend Direktno Poziva Booking Sistem (BRŽE)

Ako ne želite da pravite backend endpoint, frontend može direktno da poziva booking sistem.

#### Izmeni Frontend Kod

**Pronađi fajl:** Verovatno `booking-form.js` ili `couple-booking.js`

**Trenutni kod (pogrešan):**
```javascript
const response = await fetch('/api/book-couple-appointment', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(formData)
});
```

**Novi kod (ispravan):**
```javascript
// Prvo dobavi listu terapeuta
const therapistsResponse = await fetch(
  'https://discount-fixer.preview.emergentagent.com/api/therapists'
);
const therapists = await therapistsResponse.json();

if (!therapists || therapists.length === 0) {
  alert('Trenutno nema dostupnih terapeuta');
  return;
}

// Uzmi prvog terapeuta
const therapistId = therapists[0].id;

// Pripremi payload
const bookingPayload = {
  client_first_name: formData.firstName,
  client_last_name: formData.lastName,
  client_phone: formData.phone,
  client_email: formData.email || null,
  therapist_id: therapistId,  // DODATO!
  duration_type: parseInt(formData.durationType),
  person1_services: [formData.person1Service],
  person2_services: [formData.person2Service],
  start_time: formData.startTime,
  status: 'scheduled',  // DODATO!
  discount_couples_massage: 15.0
};

// Pošalji na booking sistem
const response = await fetch(
  'https://discount-fixer.preview.emergentagent.com/api/appointments/couple',
  {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(bookingPayload)
  }
);

if (response.ok) {
  const result = await response.json();
  alert('✅ Termin uspešno zakazan!');
  console.log('Created appointment:', result);
} else {
  const error = await response.json();
  alert('❌ Greška: ' + JSON.stringify(error.detail));
  console.error('Booking error:', error);
}
```

---

## 🧪 TESTIRANJE

Nakon implementacije bilo koje opcije, testiranje:

### 1. Test Couple Booking Form

1. Idi na: https://discount-fixer.preview.emergentagent.com/
2. Klikni BOOKING
3. Izaberi "Masaža za parove"
4. Popuni formu
5. Klikni "Pošaljite"

### 2. Očekivani Rezultat

- ✅ Success poruka: "Termin uspešno zakazan"
- ✅ U Network tab-u: `200 OK` (zeleno)
- ✅ U booking sistemu: Novi termin kreiran

### 3. Provera u Booking Sistemu

Idi na: https://discount-fixer.preview.emergentagent.com/appointments  
(Password: studio149)

Trebalo bi da vidiš novi couple appointment sa:
- Naziv: "Masaža za parove - 240 min (2x120 min) - 15% popust"
- Trajanje: 240 min
- Cena sa popustom

---

## 📋 PAYLOAD REFERENCA

**Ono što web sajt trenutno šalje (NEPOTPUNO):**
```json
{
  "client_first_name": "Milos",
  "client_last_name": "Stojojevic",
  "client_email": "themonstabeat2@gmail.com",
  "client_phone": "9843758",
  "discount_couples_massage": 15,
  "duration_type": 120,
  "person1_services": ["f3c55c37-5366-4be2-a473-123..."],
  "person2_services": ["5dc65aee-8a6f-4cc3-b91a-44b..."],
  "start_time": "2025-11-07T18:00:00"
}
```

**Ono što booking sistem ZAHTEVA (POTPUNO):**
```json
{
  "client_first_name": "Milos",
  "client_last_name": "Stojojevic",
  "client_email": "themonstabeat2@gmail.com",
  "client_phone": "9843758",
  "therapist_id": "THERAPIST_ID_HERE",  // ⚠️ NEDOSTAJE!
  "duration_type": 120,
  "person1_services": ["f3c55c37-5366-4be2-a473-123..."],
  "person2_services": ["5dc65aee-8a6f-4cc3-b91a-44b..."],
  "start_time": "2025-11-07T18:00:00",
  "status": "scheduled",  // ⚠️ NEDOSTAJE!
  "discount_couples_massage": 15.0
}
```

---

## 🎯 KOMANDA ZA WEB SAJT AGENTA

**Kopiraj i pošalji:**

```
HITNO FIX: /api/book-couple-appointment endpoint NE POSTOJI!

PROBLEM:
Web sajt pokušava da pozove POST /api/book-couple-appointment ali taj endpoint ne postoji.
Takođe, nedostaju obavezna polja: therapist_id i status.

REŠENJE - Izaberi jedno:

OPCIJA A (Backend Fix):
Kreiraj endpoint /api/book-couple-appointment u backend-u koji:
1. Dobavi therapist_id iz GET https://discount-fixer.preview.emergentagent.com/api/therapists
2. Dodaj therapist_id i status: "scheduled" u payload
3. Proxy-uj na: POST https://discount-fixer.preview.emergentagent.com/api/appointments/couple

OPCIJA B (Frontend Fix - BRŽE):
U frontend kodu, izmeni fetch poziv da DIREKTNO poziva:
- URL: https://discount-fixer.preview.emergentagent.com/api/appointments/couple
- Dodaj therapist_id (dobavi iz /api/therapists)
- Dodaj status: "scheduled"

TRENUTNI PAYLOAD (NEPOTPUN):
{
  "client_first_name": "Milos",
  "duration_type": 120,
  "person1_services": ["..."],
  "person2_services": ["..."],
  "start_time": "2025-11-07T18:00:00"
}

POTREBAN PAYLOAD:
{
  "client_first_name": "Milos",
  "therapist_id": "ID_OD_API",  // DODAJ!
  "duration_type": 120,
  "person1_services": ["..."],
  "person2_services": ["..."],
  "start_time": "2025-11-07T18:00:00",
  "status": "scheduled"  // DODAJ!
}

Pogledaj /app/KONACNO_RESENJE_ZA_WEBSAJT.md za detaljan kod!
```

---

## ✅ PROVERA USPEŠNOSTI

Nakon implementacije:

1. ✅ Network tab pokazuje: `200 OK` (zeleno)
2. ✅ Success poruka se prikazuje
3. ✅ Termin se pojavljuje u booking sistemu
4. ✅ Dashboard prikazuje pravilnu akcijsku cenu

---

**NAPOMENA:** Booking sistem (`therapist-booking-2`) radi savršeno. Problem je **SAMO** na web sajtu (`spa-booking-fix-1`) koji poziva pogrešan endpoint i ne šalje sve potrebne podatke.
