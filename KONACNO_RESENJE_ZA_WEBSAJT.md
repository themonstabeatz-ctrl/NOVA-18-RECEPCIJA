# 🎯 KONAČNO REŠENJE - Popusti Na Websajtu

## ⚠️ PROČITAJ OVO PAŽLJIVO - OVO JE FINALNO REŠENJE!

---

## 📊 TRENUTNO STANJE (Upravo Implementirano)

### Backend Booking Sistem:
```
✅ [PAROVI] servisi: 18 servisa
✅ discount_percentage: 0% (SVI)
✅ Cene: PUNE, ORIGINALNE cene
✅ Primeri:
   - [PAROVI] Aroma terapija 60 min: 4,400 RSD
   - [PAROVI] Tradicionalna tajlandska 90 min: 5,600 RSD
   - [PAROVI] Aromaterapija & topli kamen 120 min: 7,200 RSD
```

---

## 🎯 ŠTA TI TAČNO TREBAŠ DA URADIŠ

### KORAK 1: Fetch Servisa Sa Backend-a

```javascript
// 1. Pozovi API
const response = await fetch('https://prices-snapshot.preview.emergentagent.com/api/services');
const allServices = await response.json();

// 2. Filter samo [PAROVI] servise
const coupleServices = allServices.filter(service => 
  service.name.startsWith('[PAROVI]')
);

// 3. Proveri discount_percentage
coupleServices.forEach(service => {
  console.log(service.name);
  console.log('Discount:', service.discount_percentage);  // Trebalo bi biti 0
  console.log('Price:', service.price);  // Puna cena
});
```

**Očekuješ da vidiš:**
```
[PAROVI] Aroma terapija - 60 min
Discount: 0
Price: 4400

[PAROVI] Tradicionalna tajlandska masaža - 90 min
Discount: 0
Price: 5600
```

---

### KORAK 2: Primeni 10% Popust NA FRONTEND-U (Lokalno)

```javascript
// ZA SVAKI COUPLE SERVICE:
const originalPrice = service.price;  // 4400 RSD (puna cena sa backend-a)

// PRIMENI 10% POPUST LOKALNO (samo za prikaz):
const discountPercentage = 10;  // Fiksno 10% za karticu
const discountAmount = originalPrice * (discountPercentage / 100);  // 440 RSD
const discountedPrice = originalPrice - discountAmount;  // 3960 RSD

console.log('Originalna cena:', originalPrice);      // 4400 RSD
console.log('Popust 10%:', discountAmount);         // 440 RSD
console.log('Cena sa popustom:', discountedPrice);  // 3960 RSD
```

---

### KORAK 3: Prikaži Badge i Cene Na Kartici

```html
<!-- KARTICA "MASAŽA ZA PAROVE" -->
<div class="couple-massage-card">
  
  <!-- BADGE SA -10% -->
  <div class="discount-badge">
    -10%
  </div>
  
  <!-- OPIS SERVISA -->
  <h3>Masaža za Parove</h3>
  
  <!-- CENE -->
  <div class="pricing">
    
    <!-- Primer: 2 servisa -->
    <p>Osoba 1: [PAROVI] Aroma terapija - 60 min</p>
    <p class="original-price" style="text-decoration: line-through;">
      4,400 RSD
    </p>
    
    <p>Osoba 2: [PAROVI] Tradicionalna tajlandska - 90 min</p>
    <p class="original-price" style="text-decoration: line-through;">
      5,600 RSD
    </p>
    
    <!-- UKUPNO -->
    <div class="total">
      <p>Ukupno: <span class="strike">10,000 RSD</span></p>
      <p class="discount-info">Popust 10%: -1,000 RSD</p>
      <p class="final-price">ZA PLAĆANJE: <strong>9,000 RSD</strong></p>
    </div>
    
  </div>
  
  <button>Zakaži sada</button>
</div>
```

---

### KORAK 4: Slanje Rezervacije Na Backend

```javascript
// Kada korisnik klikne "Zakaži sada":

const bookingData = {
  client_first_name: "Ana",
  client_last_name: "Jovanović",
  client_phone: "+381601234567",
  client_email: "ana@example.com",
  therapist_id: "uuid-terapeuta",  // Dobavi sa backend-a
  duration_type: 60,  // 60, 90, ili 120
  person1_services: ["uuid-servisa-1"],  // [PAROVI] servis ID
  person2_services: ["uuid-servisa-2"],  // [PAROVI] servis ID
  start_time: "2025-11-18T14:00:00",
  discount_couples_massage: 10,  // ← OVDE ŠALJEŠ 10!
  status: "scheduled"
};

// Pošalji na backend:
const response = await fetch(
  'https://prices-snapshot.preview.emergentagent.com/api/appointments/couple',
  {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(bookingData)
  }
);

const result = await response.json();
console.log('Rezervacija kreirana:', result);
```

**KLJUČNO:**
- ✅ `discount_couples_massage: 10` - Šalješ 10% popust
- ✅ Backend će uzeti PUNE cene (4400, 5600)
- ✅ Backend će primeniti 10% popust
- ✅ Backend će sačuvati snapshot podatke
- ✅ Backend će kreirati rezervaciju sa sniženom cenom (9000 RSD)

---

## ✅ PROVERA - Da Li Sve Radi

### TEST 1: Proveri Backend Servise
```bash
curl -s "https://prices-snapshot.preview.emergentagent.com/api/services" | \
  grep -A 3 "\[PAROVI\]" | head -20

# Trebalo bi da vidiš:
# "name": "[PAROVI] Aroma terapija - 60 min"
# "price": 4400
# "discount_percentage": 0
```

### TEST 2: Proveri Frontend Badge
1. Otvori: https://prices-snapshot.preview.emergentagent.com/massage
2. Skroluj do kartice "Masaža za parove"
3. Trebalo bi da vidiš badge sa **"-10%"**
4. Trebalo bi da vidiš precrtane originalne cene
5. Trebalo bi da vidiš snižene cene ispod

### TEST 3: Kreiraj Test Rezervaciju
1. Izaberi 2 [PAROVI] masaže (npr. 4400 + 5600 = 10,000 RSD)
2. Trebalo bi da vidiš: "Popust 10%: -1,000 RSD"
3. Trebalo bi da vidiš: "Za plaćanje: 9,000 RSD"
4. Kreiraj rezervaciju
5. Proveri u Dashboard-u (https://prices-snapshot.preview.emergentagent.com/)
   - Lozinka: studio149
   - U "Termini" trebalo bi da vidiš rezervaciju sa cenom 9,000 RSD
   - U "Notifikacije" trebalo bi da vidiš detalje sa popustom 10%

---

## ❌ GREŠKE KOJE NE SMEŠ PRAVITI

### GREŠKA 1: Menjanje Backend Popusta
```bash
❌ NEMOJ:
PATCH /api/services/{service_id}/discount?discount=10

✅ KORISTI:
// Samo fetch-uj servise, ne menjaj ih!
GET /api/services
```

### GREŠKA 2: Primena Dvostrukog Popusta
```javascript
❌ POGREŠNO:
const price = service.price;  // 3740 (već sniženo)
const withDiscount = price * 0.9;  // Dodatnih 10%
// Rezultat: Dvostruki popust!

✅ TAČNO:
const price = service.price;  // 4400 (puna cena)
const withDiscount = price * 0.9;  // 10% popust
// Rezultat: 3960 RSD
```

### GREŠKA 3: Ne Slanje discount_couples_massage Parametra
```javascript
❌ POGREŠNO:
POST /api/appointments/couple
{
  "person1_services": ["uuid1"],
  "person2_services": ["uuid2"]
  // Nema discount_couples_massage!
}

✅ TAČNO:
POST /api/appointments/couple
{
  "person1_services": ["uuid1"],
  "person2_services": ["uuid2"],
  "discount_couples_massage": 10  // ← OBAVEZNO!
}
```

---

## 🔐 GARANCIJE

### ✅ Garantujem Da:
1. Backend [PAROVI] servisi imaju **discount_percentage = 0%**
2. Backend [PAROVI] servisi imaju **PUNE, originalne cene**
3. Backend endpoint `/api/appointments/couple` **prima** `discount_couples_massage` parametar
4. Backend **pravilno obračunava** popust (puna_cena * (1 - discount/100))
5. Backend **čuva snapshot** podatke (originalna cena, snižena cena, discount %)
6. Snapshot podaci se **prikazuju** u: Termini, Dashboard, Notifikacije, Listing

### ✅ Ti Garantuješ Da Ćeš:
1. **Fetch-ovati** servise sa backend-a (GET /api/services)
2. **Primeniti 10% popust** LOKALNO na frontend-u (samo za prikaz)
3. **Prikazati badge** "-10%" na kartici
4. **Prikazati precrtane** originalne cene
5. **Prikazati snižene** cene ispod
6. **Poslati** `discount_couples_massage: 10` na backend
7. **NE MENJATI** backend popuste

---

## 📞 FINALNA PORUKA

**Backend je FINALAN i TESTIRAN.**

**Tvoj zadatak je JEDNOSTAVAN:**
1. Fetch servise (GET /api/services)
2. Primeni 10% popust lokalno (samo za prikaz)
3. Pošalji discount_couples_massage: 10 na backend

**Ako slediš ove 3 koraka, SVE ĆE RADITI!**

**NE PITAJ:**
- "Trebam li da aktiviram popust u backend-u?" → NE
- "Trebam li da brišem duplikate?" → NE (nema ih)
- "Trebam li da menjam cene?" → NE

**SAMO URADI:**
- Fetch servise
- Primeni 10% lokalno
- Pošalji discount parametar

---

**Version:** v3 - FINALNO REŠENJE
**Datum:** 2025-11-17
**Status:** PRODUCTION READY ✅
