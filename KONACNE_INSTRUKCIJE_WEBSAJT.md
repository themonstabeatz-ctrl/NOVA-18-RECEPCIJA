# 🎯 KONAČNE INSTRUKCIJE - Popust Za Couple Masažu

## ✅ BACKEND JE AŽURIRAN!

**Oba endpointa sada podržavaju popuste:**
- `/api/appointments/couple` (stari endpoint) ✅
- `/api/book-couple-appointment` (novi endpoint) ✅

---

## 📍 KOJI ENDPOINT WEBSAJT KORISTI?

**Proveri svoj kod i pronađi URL:**

```javascript
// Proveri da li koristiš:
'/api/appointments/couple'  // ← STARI
// ili
'/api/book-couple-appointment'  // ← NOVI
```

**OBA RADE SADA!** Samo dodaj `discount_couples_massage` parametar.

---

## ✅ REŠENJE - Dodaj discount_couples_massage

### OPCIJA 1: Hardkodovano (Brzo)

```javascript
const bookingData = {
  client_first_name: formData.firstName,
  client_last_name: formData.lastName,
  client_phone: formData.phone,
  client_email: formData.email,
  therapist_id: formData.therapistId,
  start_time: formatToISO(formData.date, formData.time),
  duration_type: getDurationType(formData.selectedService),
  person1_services: [formData.person1ServiceId],
  person2_services: [formData.person2ServiceId],
  discount_couples_massage: 15.0,  // ✅ DODAJ OVO!
  status: "scheduled"
};

// Šalji na BILO KOJI endpoint:
const response = await fetch(
  'https://spabooking.emergent.host/api/appointments/couple',  // ili '/api/book-couple-appointment'
  {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(bookingData)
  }
);
```

---

### OPCIJA 2: Dinamičko (Pravo rešenje)

```javascript
// Funkcija za proveru popusta
async function getCoupleDiscount() {
  try {
    const response = await fetch('https://spabooking.emergent.host/api/services');
    const services = await response.json();
    
    // Nađi couple servis sa popustom
    const coupleService = services.find(s => 
      (s.name?.includes('parove') || s.category === 'Kartica Masaza za parove') && 
      s.discount_percentage > 0
    );
    
    return coupleService ? coupleService.discount_percentage : 0;
  } catch (error) {
    console.error('Greška pri proveri popusta:', error);
    return 0;
  }
}

// Booking funkcija
async function bookCoupleAppointment(formData) {
  // Prvo proveri popust
  const discount = await getCoupleDiscount();
  console.log(`📊 Aktivan popust: ${discount}%`);
  
  const bookingData = {
    client_first_name: formData.firstName,
    client_last_name: formData.lastName,
    client_phone: formData.phone,
    client_email: formData.email,
    therapist_id: formData.therapistId,
    start_time: formatToISO(formData.date, formData.time),
    duration_type: getDurationType(formData.selectedService),
    person1_services: [formData.person1ServiceId],
    person2_services: [formData.person2ServiceId],
    discount_couples_massage: discount,  // ✅ DINAMIČKI!
    status: "scheduled"
  };
  
  console.log('📤 Šaljem:', JSON.stringify(bookingData, null, 2));
  
  const response = await fetch(
    'https://spabooking.emergent.host/api/appointments/couple',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(bookingData)
    }
  );
  
  if (!response.ok) {
    throw new Error(`Booking failed: ${response.status}`);
  }
  
  return await response.json();
}
```

---

## 🧪 TESTIRANJE

### 1. Dodaj Console Logs

```javascript
console.log('📦 Booking data:', bookingData);
console.log('💸 Discount:', bookingData.discount_couples_massage);
```

### 2. Proveri Network Tab (F12)

- Otvori Developer Tools (F12)
- Idi na "Network" tab
- Napravi rezervaciju
- Pronađi `/appointments/couple` request
- Klikni na njega
- Pogledaj "Payload" ili "Request Payload"
- **PROVERI:**
  ```json
  {
    ...
    "discount_couples_massage": 15.0  // ← OVO MORA BITI TU!
  }
  ```

### 3. Proveri Response

- U istom request-u, idi na "Response" tab
- Proveri da li ima `service_id`
- Kopiraj `service_id`

### 4. Proveri U Booking Sistemu

1. Idi na: https://spabooking.emergent.host
2. Login: `studio149`
3. Idi na Dashboard
4. Proveri poslednju rezervaciju:
   - **SA popustom:** 7,480 RSD (za 2x60 min)
   - **BEZ popusta:** 8,800 RSD

---

## 📊 OČEKIVANE CENE

| Trajanje | Original | Sa 15% | Sa 10% | Sa 20% |
|----------|----------|--------|--------|--------|
| 2x60 min | 8,800 | **7,480** | 7,920 | 7,040 |
| 2x90 min | 11,200 | **9,520** | 10,080 | 8,960 |
| 2x120 min | 13,600 | **11,560** | 12,240 | 10,880 |

---

## ⚠️ ČESTE GREŠKE

### Greška 1: Zaboravio si dodati polje

```javascript
// ❌ POGREŠNO - nedostaje discount_couples_massage
{
  client_first_name: "...",
  client_last_name: "...",
  // discount_couples_massage: 15.0  <- ZABORAVIO!
}

// ✅ ISPRAVNO
{
  client_first_name: "...",
  client_last_name: "...",
  discount_couples_massage: 15.0  // ← DODATO!
}
```

### Greška 2: Pogrešan tip

```javascript
discount_couples_massage: "15"  // ❌ String
discount_couples_massage: 15    // ✅ Number (ok)
discount_couples_massage: 15.0  // ✅ Number (najbolje)
```

### Greška 3: Null ili undefined

```javascript
discount_couples_massage: null       // ❌
discount_couples_massage: undefined  // ❌
discount_couples_massage: 0          // ✅ (ako nema popusta)
discount_couples_massage: 15.0       // ✅ (ako ima popust)
```

---

## 🎯 BRZO - Copy/Paste Rešenje

**Ako imaš ovako nešto:**

```javascript
person2_services: [formData.person2ServiceId]
```

**Dodaj ISPOD:**

```javascript
person2_services: [formData.person2ServiceId],
discount_couples_massage: 15.0  // ← DODAJ SAMO OVU LINIJU!
```

**NE ZABORAVI ZAREZ (`,`) NA PRETHODNOJ LINIJI!**

---

## ✅ CHECKLIST

Proveri da si uradio:
- [ ] Pronašao booking funkciju
- [ ] Dodao `discount_couples_massage: 15.0`
- [ ] Dodao zarez na prethodnoj liniji
- [ ] Dodao console.log za debug
- [ ] Testirano u browser-u
- [ ] Provereno u Network tabu (discount_couples_massage: 15.0)
- [ ] Napravljena test rezervacija
- [ ] Provereno u Dashboard-u (7,480 RSD)

---

## 🚀 SADA RADI!

Backend je potpuno spreman i oba endpointa podržavaju popuste. Samo dodaj `discount_couples_massage` parametar i **BIĆE GOTOVO**! 

Pošalji screenshot iz Network taba (Request Payload) ako i dalje ne radi.
