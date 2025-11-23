# 🎉 KOMPLETNA INTEGRACIJA - Websajt & Booking Sistem

## ✅ ŠTA JE URAĐENO (Booking Sistem)

### 1. Backend - Novi Analytics Endpoint ✅
- **Endpoint:** `GET /api/analytics/detailed?period=week`
- **Vraća:**
  - Summary (ukupna zarada, popusti, termini)
  - By Category (Obične masaže, Kartica Masaža za parove, SPA, SPA Special kartica)
  - By Discount (0%, 5%, 10%, 15%)
  - Individual appointments with discounts

### 2. Frontend - Novi Dashboard ✅
- **Period buttons:** Danas, Ova Nedelja, Ovaj Mesec, Ova Godina
- **4 Summary Cards:**
  - Ukupna Zarada (sa popustom)
  - Broj Termina
  - Ukupan Popust Dat
  - Termini Sa Popustom
- **4 Category Cards:**
  - Obične masaže
  - Kartica Masaža za parove
  - SPA
  - SPA Special kartica
- **2 Charts:**
  - Bar Chart: Zarada po kategorijama (originalna vs sa popustom)
  - Pie Chart: Distribucija popusta (0%, 5%, 10%, 15%)
- **Tabela:** Individual termini sa popustima (prikazuje se samo ako ima popusta)

### 3. Booking API Endpoint ✅
- **Endpoint:** `POST /api/book-couple-appointment`
- **Status:** Potpuno funkcionalan (testiran sa cURL)

---

## 🎯 ŠTA WEBSAJT AGENT TREBA DA URADI

### RADNA VERZIJA WEBSAJTA:
**URL:** https://backend-pricing.preview.emergentagent.com/

### API ENDPOINT ZA POZIVANJE:
**Base URL:** https://backend-pricing.preview.emergentagent.com/api

---

## 📋 ZADATAK 1: Prikaz Popusta ⭐

### Problem:
Popusti se trenutno prikazuju na SVIM masažama, ali treba da budu vidljivi SAMO u "Masaža za parove" sekciji.

### Rešenje:

#### 1. Promeni API URL
U fajlu gde pozivas API (npr. `bookingApi.js` ili `services.js`):

```javascript
// PROMENI:
const BOOKING_API = 'https://spabooking.emergent.host/api';

// U:
const BOOKING_API = 'https://backend-pricing.preview.emergentagent.com/api';
```

#### 2. Dodaj funkciju za proveru
```javascript
export function shouldShowDiscount(service) {
  const hasDiscount = (service.discount_percentage || 0) > 0;
  const isCoupleCategory = service.category === "Kartica Masaza za parove";
  return hasDiscount && isCoupleCategory;
}
```

#### 3. U običnim masažama (Tradicionalna, Aroma, itd.):
**UVEK prikazuj normalnu cenu - NIKAD popuste!**

```javascript
// NE OVO:
{showDiscount && <img src={badgeUrl} alt="popust" />}
{showDiscount && <p className="old-price">{oldPrice}</p>}

// VEĆ OVO:
<p className="price">{service.price.toLocaleString()} RSD</p>
```

#### 4. U "Masaža za parove" dropdown-u:
**Prikazuj popuste SA značkama!**

```javascript
import { shouldShowDiscount } from './bookingApi';

{services.map(service => {
  const showDiscount = shouldShowDiscount(service); // PROVERI
  const badgeUrl = showDiscount ? getDiscountBadgeUrl(service.discount_percentage) : null;
  
  return (
    <option key={service.id} value={service.id}>
      {service.name} - 
      {showDiscount ? (
        `${calculateDiscountedPrice(service)} RSD (-${service.discount_percentage}%)`
      ) : (
        `${service.price} RSD`
      )}
    </option>
  );
})}

{/* Prikaži značku pored dropdown-a */}
{selectedService && (() => {
  const showDiscount = shouldShowDiscount(selectedService);
  const badgeUrl = showDiscount ? getDiscountBadgeUrl(selectedService.discount_percentage) : null;
  return badgeUrl && <img src={badgeUrl} alt="popust" style={{width: '50px'}} />;
})()}
```

---

## 📋 ZADATAK 2: Booking Funkcionalnost ⭐

### Problem:
Korisnik dobija grešku "Greška! Molimo pokušajte ponovo." pri zakazivanju.

### API Endpoint:
```
POST https://backend-pricing.preview.emergentagent.com/api/book-couple-appointment
```

### Format Podataka:
```json
{
  "client_first_name": "Milos",
  "client_last_name": "Stanić",
  "client_phone": "9843768",
  "client_email": "themonstabenzq@gmail.com",
  "start_time": "2025-11-09T14:00:00",
  "duration_type": 60,
  "person1_services": ["service-id-1"],
  "person2_services": ["service-id-2"],
  "discount_couples_massage": 15.0
}
```

### KLJUČNE IZMENE:

1. **Razdvojeno ime i prezime:**
   - `client_first_name` i `client_last_name` (NE `client_name`!)

2. **ISO format datuma:**
   ```javascript
   function formatToISO(date, time) {
     // date = "09/11/2025" (DD/MM/YYYY)
     // time = "14:00"
     const [day, month, year] = date.split('/');
     const [hours, minutes] = time.split(':');
     return `${year}-${month}-${day}T${hours}:${minutes}:00`;
   }
   ```

3. **Duration Type (per person):**
   ```javascript
   function getDurationType(serviceText) {
     if (serviceText.includes('240 min')) return 120; // 120x2=240
     if (serviceText.includes('180 min')) return 90;  // 90x2=180
     if (serviceText.includes('120 min')) return 60;  // 60x2=120
     return 60; // default
   }
   ```

4. **person1_services i person2_services MORA biti array:**
   ```javascript
   "person1_services": ["service-id-ovde"]  // SA []
   ```

### Kompletna Funkcija:
```javascript
async function bookCoupleAppointment(formData) {
  const bookingData = {
    client_first_name: formData.firstName,
    client_last_name: formData.lastName,
    client_phone: formData.phone,
    client_email: formData.email,
    start_time: formatToISO(formData.date, formData.time),
    duration_type: getDurationType(formData.selectedService),
    person1_services: [formData.person1ServiceId],
    person2_services: [formData.person2ServiceId],
    discount_couples_massage: 15.0
  };
  
  const response = await fetch(
    'https://backend-pricing.preview.emergentagent.com/api/book-couple-appointment',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(bookingData)
    }
  );
  
  if (!response.ok) {
    const error = await response.json();
    console.error('❌ Booking failed:', error);
    throw new Error('Booking failed');
  }
  
  const appointment = await response.json();
  console.log('✅ Booking successful:', appointment);
  return appointment;
}
```

### Integracija u Formu:
```javascript
const handleSubmit = async (e) => {
  e.preventDefault();
  
  try {
    setLoading(true);
    setError(null);
    
    const appointment = await bookCoupleAppointment(formData);
    
    // Uspešno - prikaži korisniku potvrdu
    showBookingConfirmation(appointment);
    
  } catch (error) {
    setError('Došlo je do greške pri zakazivanju. Molimo pokušajte ponovo.');
  } finally {
    setLoading(false);
  }
};
```

---

## 📋 ZADATAK 3: Prikaz Potvrde Korisniku ⭐

```javascript
function showBookingConfirmation(appointment) {
  const message = `
    ✅ Vaš termin je uspešno zakazan!
    
    📅 Datum i vreme: ${appointment.start_time}
    💆 Usluga: ${appointment.service_name}
    💰 Cena: ${appointment.price} RSD
    
    Očekujemo Vas! Za pitanja pozovite: +381 XX XXX XXXX
  `;
  
  // Prikaži u modalu ili alert
  alert(message); // ili koristi modal komponentu
}
```

---

## 🧪 TESTIRANJE

### Test 1: Popusti
1. Otvori booking sistem: https://backend-pricing.preview.emergentagent.com/services
2. Idi na "Kartica Masaza za parove"
3. Postavi 15% popust
4. Refresh websajt
5. **Očekivano:** Popusti vidljivi SAMO u "Masaža za parove" dropdown-u

### Test 2: Booking sa fiksnim podacima
```javascript
async function testBooking() {
  const testData = {
    client_first_name: "Test",
    client_last_name: "Korisnik",
    client_phone: "123456789",
    client_email: "test@test.com",
    start_time: "2025-11-20T14:00:00",
    duration_type: 60,
    person1_services: ["f99bb0aa-7c87-4bef-bca7-afa0a6fd5535"],
    person2_services: ["f99bb0aa-7c87-4bef-bca7-afa0a6fd5535"],
    discount_couples_massage: 15.0
  };
  
  const response = await fetch(
    'https://backend-pricing.preview.emergentagent.com/api/book-couple-appointment',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(testData)
    }
  );
  
  if (response.ok) {
    alert('✅ TEST USPEŠAN! Booking radi!');
  } else {
    const error = await response.json();
    alert('❌ TEST NEUSPEŠAN: ' + JSON.stringify(error));
  }
}
```

### Test 3: Proveri u Dashboard-u
1. Idi na: https://backend-pricing.preview.emergentagent.com/
2. Login sa `studio149`
3. Proveri da li se termin pojavio u "Pregled Po Kategorijama"

---

## ✅ OČEKIVANI REZULTAT

✅ **Popusti:**
- Vidljivi SAMO u "Masaža za parove" dropdown-u
- Sa značkama (-5%, -10%, -15%)
- Prikazuju akcijske cene

✅ **Booking:**
- Korisnik može da zakаže termin
- Dobija potvrdu sa svim detaljima
- Admin vidi termin u booking sistemu Dashboard-u

✅ **Dashboard:**
- Prikazuje termine po kategorijama
- Prikazuje popuste ako su aktivni
- Charts i grafikoni rade
- Period buttons rade (Danas, Ova Nedelja, Ovaj Mesec, Ova Godina)

---

## 📞 DODATNO

Za sve dodatne fajlove i dokumentaciju pogledaj:
- `/app/FINALNA_KOMANDA_WEBSAJT.txt` - Brza komanda
- `/app/WEBSAJT_DEBUGGING.txt` - Debugging instrukcije
- `/app/WEBSAJT_BOOKING_INTEGRACIJA.md` - Detaljna booking integracija
- `/app/ISPRAVKA_WEBSAJT_POPUSTI.md` - Detaljna ispravka popusta

---

Sve je spremno sa booking sistema! Websajt treba samo implementaciju! 🚀
