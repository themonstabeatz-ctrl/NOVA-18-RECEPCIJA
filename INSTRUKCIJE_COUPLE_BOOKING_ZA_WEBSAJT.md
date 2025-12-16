# 🎯 INSTRUKCIJE ZA COUPLE MASSAGE BOOKING NA WEB SAJTU

## ⚠️ VAŽNO: Couple Massage NE POSTOJI U SERVICES

**"Masaža za parove" NE treba da bude u regularnim uslugama!**

Couple massage se **automatski kreira** kada korisnik zakaže preko posebnog endpointa.

---

## 📋 KAKO RADI COUPLE BOOKING

### Proces:
1. **Korisnik bira "Masaža za parove"** na web sajtu
2. **Pojavljuju se 2 dropdown menija:**
   - **Osoba 1:** Bira svoju masažu (npr. Tradicionalna 60 min)
   - **Osoba 2:** Bira svoju masažu (npr. Aroma terapija 90 min)
3. **Web sajt poziva COUPLE ENDPOINT** sa podacima
4. **Backend automatski:**
   - Računa ukupnu cenu (Osoba1 + Osoba2)
   - Primenjuje popust (ako je aktivan)
   - Kreira novu "couple service" uslugu
   - Zakazuje termin

---

## 🔌 API ENDPOINT ZA COUPLE BOOKING

### **POST** `/api/appointments/couple`

**URL:** `https://massage-scheduler-4.preview.emergentagent.com/api/appointments/couple`

### Request Body:
```json
{
  "client_first_name": "Marko",
  "client_last_name": "Petrović",
  "client_phone": "+381601234567",
  "client_email": "marko@example.com",
  "therapist_id": "THERAPIST_ID_FROM_API",
  "duration_type": 60,
  "person1_services": ["SERVICE_ID_1"],
  "person2_services": ["SERVICE_ID_2"],
  "start_time": "2025-02-15T14:00:00",
  "status": "scheduled",
  "discount_couples_massage": 15.0
}
```

### Parametri:

| Parametar | Tip | Opis | Obavezno |
|-----------|-----|------|----------|
| `client_first_name` | string | Ime klijenta | ✅ |
| `client_last_name` | string | Prezime klijenta | ✅ |
| `client_phone` | string | Telefon klijenta | ✅ |
| `client_email` | string | Email klijenta | ❌ |
| `therapist_id` | string | ID terapeuta | ✅ |
| `duration_type` | integer | Trajanje po osobi: **60**, **90**, ili **120** | ✅ |
| `person1_services` | array | Niz sa ID-jem usluge za osobu 1 | ✅ |
| `person2_services` | array | Niz sa ID-jem usluge za osobu 2 | ✅ |
| `start_time` | string | Početak termina (ISO format) | ✅ |
| `status` | string | Status: "scheduled" | ✅ |
| `discount_couples_massage` | float | Popust: 0, 5, 10, ili 15 | ❌ (default: 15) |

---

## ⚙️ KAKO duration_type RADI

**`duration_type` = trajanje PO OSOBI (ne ukupno!)**

| duration_type | Svaka osoba | Ukupno trajanje | Naziv u sistemu |
|---------------|-------------|-----------------|-----------------|
| 60 | 60 min | 120 min | "Masaža za parove - 120 min (2x60 min)" |
| 90 | 90 min | 180 min | "Masaža za parove - 180 min (2x90 min)" |
| 120 | 120 min | 240 min | "Masaža za parove - 240 min (2x120 min)" |

**KRITIČNO:** 
- Ako korisnik bira "2x120 min" → pošalji `duration_type: 120` (NE 60!)
- Ako korisnik bira "2x90 min" → pošalji `duration_type: 90`
- Ako korisnik bira "2x60 min" → pošalji `duration_type: 60`

---

## 💰 KAKO SE RAČUNA CENA

### Formula:
```
1. Cena Osobe 1 = price (iz izabrane usluge)
2. Cena Osobe 2 = price (iz izabrane usluge)
3. Ukupna Cena = Cena1 + Cena2
4. Popust = Ukupna Cena × (discount_couples_massage / 100)
5. FINALNA CENA = Ukupna Cena - Popust
```

### Primer:
```
Osoba 1 bira: Tradicionalna tajlandska masaža 60 min (4400 RSD)
Osoba 2 bira: Aroma terapija 90 min (5600 RSD)
duration_type: 90

Ukupna cena: 4400 + 5600 = 10,000 RSD
Popust 15%: 10,000 × 0.15 = 1,500 RSD
FINALNA CENA: 10,000 - 1,500 = 8,500 RSD

Backend kreira:
  Naziv: "Masaža za parove - 180 min (2x90 min) - 15% popust"
  Cena: 8,500 RSD
  Trajanje: 180 min
```

---

## 📝 IMPLEMENTACIJA NA WEB SAJTU

### Korak 1: Učitaj Sve Dostupne Usluge

```javascript
// GET all services from booking system
const response = await fetch('https://massage-scheduler-4.preview.emergentagent.com/api/services');
const services = await response.json();

// Filter out couple services (shouldn't be any now, but just in case)
const regularServices = services.filter(s => !s.name.toLowerCase().includes('parove'));
```

### Korak 2: Kreiraj Couple Booking Formu

```html
<form id="coupleBookingForm">
  <!-- Client Info -->
  <input name="client_first_name" placeholder="Ime" required>
  <input name="client_last_name" placeholder="Prezime" required>
  <input name="client_phone" placeholder="Telefon" required>
  <input name="client_email" placeholder="Email (opcionalno)">
  
  <!-- Date & Time -->
  <input type="date" name="date" required>
  <input type="time" name="time" required>
  
  <!-- Duration Type Selection -->
  <label>Izaberite trajanje:</label>
  <select name="duration_type" required>
    <option value="60">2x 60 minuta (ukupno 120 min)</option>
    <option value="90">2x 90 minuta (ukupno 180 min)</option>
    <option value="120">2x 120 minuta (ukupno 240 min)</option>
  </select>
  
  <!-- Person 1 Service Selection -->
  <label>Masaža za osobu 1:</label>
  <select name="person1_service" required>
    {regularServices.map(service => (
      <option value={service.id}>
        {service.name} - {service.price} RSD
      </option>
    ))}
  </select>
  
  <!-- Person 2 Service Selection -->
  <label>Masaža za osobu 2:</label>
  <select name="person2_service" required>
    {regularServices.map(service => (
      <option value={service.id}>
        {service.name} - {service.price} RSD
      </option>
    ))}
  </select>
  
  <!-- Therapist Selection -->
  <select name="therapist_id" required>
    <!-- Load from /api/therapists -->
  </select>
  
  <button type="submit">Zakaži Termin</button>
</form>
```

### Korak 3: Submit Couple Booking

```javascript
async function submitCoupleBooking(event) {
  event.preventDefault();
  
  const formData = new FormData(event.target);
  
  // Combine date and time into ISO format
  const date = formData.get('date');
  const time = formData.get('time');
  const startTime = `${date}T${time}:00`;
  
  const requestBody = {
    client_first_name: formData.get('client_first_name'),
    client_last_name: formData.get('client_last_name'),
    client_phone: formData.get('client_phone'),
    client_email: formData.get('client_email') || null,
    therapist_id: formData.get('therapist_id'),
    duration_type: parseInt(formData.get('duration_type')),
    person1_services: [formData.get('person1_service')],
    person2_services: [formData.get('person2_service')],
    start_time: startTime,
    status: 'scheduled',
    discount_couples_massage: 15.0  // Default discount
  };
  
  try {
    const response = await fetch(
      'https://massage-scheduler-4.preview.emergentagent.com/api/appointments/couple',
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody)
      }
    );
    
    if (response.ok) {
      const result = await response.json();
      alert('✅ Termin uspešno zakazan!');
      console.log('Created appointment:', result);
    } else {
      const error = await response.json();
      alert('❌ Greška: ' + error.detail);
    }
  } catch (error) {
    console.error('Error:', error);
    alert('❌ Greška pri zakazivanju');
  }
}

document.getElementById('coupleBookingForm').addEventListener('submit', submitCoupleBooking);
```

---

## 🧪 TESTIRANJE

### Test Scenario 1: 2x60 minuta
```bash
curl -X POST https://massage-scheduler-4.preview.emergentagent.com/api/appointments/couple \
  -H "Content-Type: application/json" \
  -d '{
    "client_first_name": "Test",
    "client_last_name": "User",
    "client_phone": "+381601234567",
    "client_email": "test@example.com",
    "therapist_id": "VALID_THERAPIST_ID",
    "duration_type": 60,
    "person1_services": ["SERVICE_ID_1"],
    "person2_services": ["SERVICE_ID_2"],
    "start_time": "2025-02-15T14:00:00",
    "status": "scheduled"
  }'
```

**Očekivani rezultat:**
- Status: 200 OK
- Naziv: "Masaža za parove - 120 min (2x60 min) - 15% popust"
- Trajanje: 120 min

---

## ❌ ČESTE GREŠKE I REŠENJA

### Greška 1: "Masaža za parove" se ne može zakazati
**Uzrok:** Web sajt pokušava da koristi regularnu "Masaža za parove" uslugu umesto couple endpointa  
**Rešenje:** Koristi `/api/appointments/couple` endpoint

### Greška 2: 2x120 min kreira termin od 120 min umesto 240 min
**Uzrok:** `duration_type` je postavljen na 60 umesto 120  
**Rešenje:** Za 2x120 min, pošalji `duration_type: 120`

### Greška 3: Cena nije pravilna
**Uzrok:** Backend možda ne primenjuje popust  
**Rešenje:** Proveri da li backend pravilno računa: `(price1 + price2) * (1 - discount/100)`

### Greška 4: Duplirane "Masaža za parove" usluge u dropdown-u
**Uzrok:** Slučajno se učitavaju couple services iz `/api/services`  
**Rešenje:** Filtriraj ih: `services.filter(s => !s.name.includes('parove'))`

---

## 📊 TRENUTNE DOSTUPNE USLUGE (Za Dropdown)

Ove usluge treba prikazati u dropdown menijima za Osobu 1 i Osobu 2:

1. **Tradicionalna tajlandska masaža**
   - 60 min: 4400 RSD
   - 90 min: 5600 RSD
   - 120 min: 6800 RSD

2. **Aroma terapija**
   - 60 min: 4400 RSD
   - 90 min: 5600 RSD
   - 120 min: 6800 RSD

3. **Masaža toplim uljem**
   - 60 min: 4600 RSD
   - 90 min: 5800 RSD

4. **Glava, vrat, ramena i leđa**
   - 30 min: 2400 RSD
   - 45 min: 3200 RSD
   - 60 min: 3900 RSD

5. **Masaža stopala**
   - 30 min: 2400 RSD
   - 45 min: 2900 RSD
   - 60 min: 3500 RSD

6. **Masaža leđa i vrata**
   - 60 min: 2500 RSD
   - 90 min: 3500 RSD
   - 120 min: 4500 RSD

7. **Aroma duboko tkivo**
   - 60 min: 4900 RSD
   - 90 min: 6000 RSD

---

## ✅ PROVERA DA LI JE IMPLEMENTACIJA USPEŠNA

Nakon implementacije:

1. **Web sajt prikazuje "Masaža za parove" opciju**
2. **Korisnik bira trajanje** (2x60, 2x90, 2x120)
3. **Korisnik bira 2 usluge** (jedna za svaku osobu)
4. **Prikazuje se ukupna cena sa popustom**
5. **Submit šalje na `/api/appointments/couple` endpoint**
6. **Termin se kreira u booking sistemu**
7. **Dashboard prikazuje pravilnu akcijsku cenu**

---

## 🎯 KOMANDA ZA WEB SAJT AGENTA

**Kopirajte i pošaljite:**

```
HITNO: Popravi "Masaža za parove" booking.

PROBLEM:
"Masaža za parove" usluge više NE POSTOJE u regularnim services. One se sada automatski kreiraju preko couple endpointa.

REŠENJE:
1. Učitaj sve regularne usluge: GET /api/services
2. Filtriraj da ne prikazuješ "Masaža za parove": services.filter(s => !s.name.includes('parove'))
3. Kreiraj formu sa 2 dropdown menija (Osoba 1, Osoba 2)
4. Svaki dropdown prikazuje SVE regularne usluge (Tradicionalna, Aroma, Toplo ulje, itd.)
5. Dodaj dropdown za trajanje: 60, 90, ili 120 minuta
6. Kada korisnik submituje, pošalji na:
   POST https://massage-scheduler-4.preview.emergentagent.com/api/appointments/couple

Request body:
{
  "client_first_name": "Ime",
  "client_last_name": "Prezime",
  "client_phone": "+381...",
  "client_email": "email@example.com",
  "therapist_id": "ID_terapeuta",
  "duration_type": 60/90/120,  // PO OSOBI, ne ukupno!
  "person1_services": ["service_id_1"],
  "person2_services": ["service_id_2"],
  "start_time": "2025-02-15T14:00:00",
  "status": "scheduled",
  "discount_couples_massage": 15.0
}

VAŽNO:
- duration_type je trajanje PO OSOBI (60, 90, 120)
- Ako korisnik bira "2x120 min", pošalji duration_type: 120
- Ukupno trajanje će biti duration_type × 2
- Backend automatski kreira couple service i računa popust

Testiraj da se termin pravilno kreira!
```

---

**NAPOMENA:** Backend je sada očišćen i spreman. Sve duplirane "Masaža za parove" usluge su obrisane.
