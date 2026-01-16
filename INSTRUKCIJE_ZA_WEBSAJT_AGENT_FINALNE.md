# 🎯 FINALNE INSTRUKCIJE ZA WEBSAJT BOOKING AGENT

## VAŽNO: Pročitaj ovo pažljivo pre nego što počneš bilo šta da radiš!

---

## TRENUTNO STANJE BOOKING SISTEMA (Backend)

Backend booking sistem je **POTPUNO FUNKCIONALAN** i radi sledeće:

### 1. OBIČNE MASAŽE (Regular Services)
- ✅ Imaju aktivne popuste na **backend-u** (5%, 10%, 15%)
- ✅ Cene su već snižene u bazi
- ✅ **TI NE TREBAŠ DA ŠALJEŠ POPUST** - backend ga automatski primenjuje
- ✅ Snapshot mehanizam čuva cenu u trenutku rezervacije

### 2. [PAROVI] MASAŽE (Couple Services)
- ✅ **NEMAJU popuste na backend-u** (discount_percentage = 0%)
- ✅ Cene u bazi su PUNE, ORIGINALNE cene (bez popusta)
- ✅ **TI TREBAŠ DA PRIMENIŠ 10% POPUST NA FRONTEND-U** (na kartici)
- ✅ **TI ŠALJEŠ POPUST NA BACKEND** kao `discount_couples_massage` parametar
- ✅ Backend će izračunati sniženu cenu i sačuvati snapshot

---

## ŠTA TI TAČNO TREBAŠ DA URADIŠ

### SCENARIO A: Rezervacija OBIČNE MASAŽE (bez kartice)

**Endpoint:** `POST /api/appointments`

**Šta radiš:**
1. Korisnik bira uslugu (npr. "Tradicionalna tajlandska masaža - 60 min")
2. Ti fetch-uješ cenu sa API-ja: `GET /api/services`
3. **VAŽNO:** Cena koju dobiješ JE VEĆ SNIŽENA ako postoji popust
4. Prikažeš tu cenu korisniku (već sniženu)
5. Šalješ rezervaciju **BEZ IKAKVOG DODATNOG POPUSTA**

**Primer:**
```json
POST /api/appointments
{
  "client_first_name": "Marko",
  "client_last_name": "Petrović",
  "client_phone": "+381601234567",
  "client_email": "marko@example.com",
  "therapist_id": "uuid-terapeuta",
  "service_id": "uuid-servisa",
  "start_time": "2025-11-18T14:00:00",
  "status": "scheduled"
}
```

**NEMOJ SLATI:**
- ❌ `discount_percentage` parametar
- ❌ Bilo kakvu dodatnu diskontovanu cenu
- ❌ Bilo kakve kalkulacije popusta

**Backend će automatski:**
- ✅ Uzeti cenu iz servisa (koja je već snižena)
- ✅ Sačuvati snapshot podatke (original_price, discount_percentage)
- ✅ Vratiti rezervaciju sa svim podacima

---

### SCENARIO B: Rezervacija MASAŽE ZA PAROVE (sa karticom - 10% popust)

**Endpoint:** `POST /api/appointments/couple`

**Šta radiš:**

#### KORAK 1: Fetch-ovanje Usluga
```javascript
GET /api/services

// Filter: name startsWith "[PAROVI]"
// Ove usluge imaju PUNE cene (discount_percentage = 0%)
```

#### KORAK 2: Prikaz na Frontend-u (KARTICA)
```javascript
// Na kartici prikazuješ 10% popust:
const originalPrice = service.price;  // Puna cena sa backend-a
const discountedPrice = originalPrice * 0.90;  // 10% popust SAMO NA FRONTEND-U

// Prikažeš korisniku:
console.log(`Originalna cena: ${originalPrice} RSD`);
console.log(`Cena sa 10% popustom: ${discountedPrice} RSD`);
console.log(`Ušteda: ${originalPrice - discountedPrice} RSD`);
```

#### KORAK 3: Slanje Rezervacije
```json
POST /api/appointments/couple
{
  "client_first_name": "Marko",
  "client_last_name": "Petrović",
  "client_phone": "+381601234567",
  "client_email": "marko@example.com",
  "therapist_id": "uuid-terapeuta",
  "duration_type": 60,
  "person1_services": ["uuid-servisa-1"],
  "person2_services": ["uuid-servisa-2"],
  "start_time": "2025-11-18T14:00:00",
  "discount_couples_massage": 10,    // ← OVDE ŠALJEŠ 10% POPUST!
  "status": "scheduled"
}
```

**KLJUČNO:**
- ✅ `discount_couples_massage`: **10** (za 10% popust)
- ✅ Backend će uzeti PUNE cene iz servisa
- ✅ Backend će primeniti 10% popust
- ✅ Backend će sačuvati snapshot podatke
- ✅ Backend će kreirati "couple service" sa svim detaljima

---

## PRIMERI - TAČNO KAKO TREBA

### ✅ PRIMER 1: Obična Masaža (backend već ima popust)

**1. Fetch servisa:**
```javascript
GET /api/services
// Response:
{
  "id": "abc123",
  "name": "Tradicionalna tajlandska masaža - 60 min",
  "price": 4180,  // ← VEĆ SNIŽENA CENA (5% popust primenjen)
  "discount_percentage": 5,
  "metadata": {
    "original_price": 4400
  }
}
```

**2. Prikaz korisniku:**
```
Usluga: Tradicionalna tajlandska masaža - 60 min
Cena: 4,180 RSD  ← Prikažeš ovu cenu
(Originalno: 4,400 RSD, Popust: 5%)
```

**3. Slanje rezervacije:**
```json
POST /api/appointments
{
  "service_id": "abc123",
  ... ostali podaci
}
// NEMOJ slati discount_percentage!
```

---

### ✅ PRIMER 2: Masaža Za Parove (kartica - 10% popust)

**1. Fetch servisa:**
```javascript
GET /api/services
// Response za [PAROVI] servis:
{
  "id": "xyz789",
  "name": "[PAROVI] Tradicionalna tajlandska masaža - 60 min",
  "price": 4400,  // ← PUNA CENA (discount = 0%)
  "discount_percentage": 0,
  "category": "Kartica Masaza za parove"
}
```

**2. Frontend kalkulacija (samo za prikaz):**
```javascript
const service1_price = 4400;  // Osoba 1
const service2_price = 5600;  // Osoba 2
const total = service1_price + service2_price;  // 10,000 RSD

// Primeni 10% popust NA FRONTEND-U:
const discountAmount = total * 0.10;  // 1,000 RSD
const finalPrice = total - discountAmount;  // 9,000 RSD
```

**3. Prikaz na kartici:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  MASAŽA ZA PAROVE - 10% POPUST
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Osoba 1: Tradicionalna tajlandska - 60 min
Cena: 4,400 RSD

Osoba 2: Aroma terapija - 90 min
Cena: 5,600 RSD

Ukupno: 10,000 RSD
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  POPUST 10%: -1,000 RSD
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ZA PLAĆANJE: 9,000 RSD
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**4. Slanje rezervacije:**
```json
POST /api/appointments/couple
{
  "client_first_name": "Ana",
  "client_last_name": "Jovanović",
  "client_phone": "+381601234567",
  "client_email": "ana@example.com",
  "therapist_id": "terapeut-uuid",
  "duration_type": 60,
  "person1_services": ["xyz789"],
  "person2_services": ["abc456"],
  "start_time": "2025-11-18T15:00:00",
  "discount_couples_massage": 10,  // ← OVDE ŠALJEŠ 10!
  "status": "scheduled"
}
```

---

## ❌ GREŠKE KOJE NE SMEŠ PRAVITI

### GREŠKA 1: Slanje popusta za obične masaže
```json
❌ POST /api/appointments
{
  "service_id": "abc123",
  "discount_percentage": 10  // ← NEMOJ OVO!
}

✅ POST /api/appointments
{
  "service_id": "abc123"  // ← SAMO service_id!
}
```

### GREŠKA 2: Primena dvostrukog popusta na couple
```javascript
❌ POGREŠNO:
const service_price = 4400;  // Backend cena (već sa popustom)
const with_10_discount = service_price * 0.90;  // Dodatnih 10%
// Rezultat: DVOSTRUKI POPUST! ❌

✅ TAČNO:
const service_price = 4400;  // Backend cena (puna, bez popusta)
const with_10_discount = service_price * 0.90;  // 10% popust
// Rezultat: 3,960 RSD ✅
```

### GREŠKA 3: Slanje pogrešnog discount parametra
```json
❌ POST /api/appointments/couple
{
  "discount": 10  // ← Pogrešan naziv!
}

✅ POST /api/appointments/couple
{
  "discount_couples_massage": 10  // ← Tačan naziv!
}
```

---

## TESTIRANJE - Kako da proveriš da radi

### TEST 1: Obična masaža
1. Idi na booking formu
2. Izaberi "Tradicionalna tajlandska masaža - 60 min"
3. Proveri da cena koja se prikazuje je **4,180 RSD** (sa 5% popustom)
4. Kreiraj rezervaciju
5. Proveri u Dashboard-u da rezervacija ima:
   - Cenu: 4,180 RSD
   - Popust: 5%
   - Originalnu cenu: 4,400 RSD

### TEST 2: Masaža za parove (kartica)
1. Idi na karticu "Masaža za parove"
2. Izaberi 2 masaže (npr. 2x 4,400 RSD = 8,800 RSD)
3. Proveri da kartica prikazuje:
   - Ukupno: 8,800 RSD
   - Popust 10%: -880 RSD
   - Za plaćanje: 7,920 RSD
4. Kreiraj rezervaciju
5. Proveri u Dashboard-u da rezervacija ima:
   - Cenu: 7,920 RSD
   - Popust: 10%
   - Originalnu cenu: 8,800 RSD

---

## ENDPOINT REFERENCE

### GET /api/services
**Response:**
```json
[
  {
    "id": "uuid",
    "name": "Service name",
    "price": 4180,  // Snižena cena (ako ima popust)
    "discount_percentage": 5,  // Backend popust
    "duration": 60,
    "category": "Obicne masaze",
    "metadata": {
      "original_price": 4400  // Originalna cena
    }
  },
  {
    "id": "uuid",
    "name": "[PAROVI] Service name",
    "price": 4400,  // Puna cena (nema backend popusta)
    "discount_percentage": 0,  // Nema backend popusta
    "duration": 60,
    "category": "Kartica Masaza za parove",
    "metadata": null
  }
]
```

### POST /api/appointments (Obična masaža)
**Request:**
```json
{
  "client_first_name": "string",
  "client_last_name": "string",
  "client_phone": "string",
  "client_email": "string",
  "therapist_id": "uuid",
  "service_id": "uuid",  // ID obične masaže
  "start_time": "2025-11-18T14:00:00",
  "status": "scheduled"
}
```

### POST /api/appointments/couple (Masaža za parove)
**Request:**
```json
{
  "client_first_name": "string",
  "client_last_name": "string",
  "client_phone": "string",
  "client_email": "string",
  "therapist_id": "uuid",
  "duration_type": 60,  // 60, 90, ili 120
  "person1_services": ["uuid"],  // [PAROVI] service IDs
  "person2_services": ["uuid"],  // [PAROVI] service IDs
  "start_time": "2025-11-18T14:00:00",
  "discount_couples_massage": 10,  // 0, 5, 10, ili 15
  "status": "scheduled"
}
```

---

## SAŽETAK - 3 KLJUČNE TAČKE

### 1️⃣ OBIČNE MASAŽE
- Backend već ima popust
- Ti samo fetch-uješ i prikažeš cenu
- NE šalješ nikakav popust parametar

### 2️⃣ COUPLE MASAŽE (KARTICA)
- Backend NEMA popust (price = puna cena)
- Ti primenjuješ 10% popust NA FRONTEND-U (samo za prikaz)
- Šalješ `discount_couples_massage: 10` na backend

### 3️⃣ SNAPSHOT MEHANIZAM
- Backend automatski čuva cenu u trenutku rezervacije
- Ti NE TREBAŠ da brineš o tome
- Rezervacije će imati tačne cene zauvek

---

## KONTAKT ZA POMOĆ

Ako imaš bilo kakvih pitanja ili probleme:
1. Proveri ove instrukcije ponovo
2. Testiraj sa malim rezervacijama prvo
3. Proveri u Dashboard-u da li se podaci prikazuju tačno

**Booking sistem Backend URL:**
```
https://multilingfix.preview.emergentagent.com/api
```

**Dashboard URL:**
```
https://multilingfix.preview.emergentagent.com/
Lozinka: studio149
```

---

## FINALNA PORUKA

**ZAPAMTI:**
- Backend je potpuno funkcionalan ✅
- Ti samo trebaš da pravilno pozoveš endpointe ✅
- Popusti za obične masaže su AUTOMATSKI ✅
- Popusti za couple masaže šalješ kao parametar ✅

**Ako slediš ove instrukcije, SVE ĆE RADITI SAVRŠENO!** 🎉

---

## VERSION INFO
- Datum: 2025-11-17
- Backend API verzija: v2
- Status: PRODUCTION READY ✅
