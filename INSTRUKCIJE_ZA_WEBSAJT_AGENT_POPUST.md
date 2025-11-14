# 📋 DETALJNE INSTRUKCIJE - Popust Za Couple Masažu

## 🎯 ŠTA TREBA URADITI:

Websajt trenutno **NE ŠALJE POPUST** kada korisnik rezerviše couple masažu. Zato se u booking sistemu rezervacija prikazuje sa punom cenom umesto diskontovane.

---

## 📍 GDE PROMENITI KOD:

Pronađite funkciju koja šalje booking zahtev za couple masažu. Verovatno se zove:
- `bookCoupleAppointment()`
- `submitCoupleBooking()`
- ili slično

**Fajl je verovatno:**
- `bookingApi.js`
- `api.js`
- `coupleBooking.js`
- `main.js`
- ili slični API fajlovi

---

## 🔍 KORAK 1: Pronađite POST zahtev

Potražite kod koji šalje POST zahtev na:
```
https://spabooking.emergent.host/api/book-couple-appointment
```

**Trenutno izgleda OVAKO:**

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
    discount_couples_massage: 0  // ❌ PROBLEM: Uvek šalje 0!
  };
  
  const response = await fetch(
    'https://spabooking.emergent.host/api/book-couple-appointment',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(bookingData)
    }
  );
  
  return await response.json();
}
```

---

## ✅ KORAK 2: OPCIJA A - Brzo Rešenje (HARDKODOVANO)

Ako je popust **UVEK 15%** dok je aktivan, samo promenite vrednost:

**BEFORE (pogrešno):**
```javascript
discount_couples_massage: 0  // ❌
```

**AFTER (ispravno):**
```javascript
discount_couples_massage: 15.0  // ✅ Dok je popust aktivan
```

**KOMPLETAN KOD:**

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
    discount_couples_massage: 15.0  // ✅ PROMENJENA VREDNOST!
  };
  
  console.log('📤 Šaljem booking sa 15% popustom');  // ✅ Dodaj za debug
  
  const response = await fetch(
    'https://spabooking.emergent.host/api/book-couple-appointment',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(bookingData)
    }
  );
  
  if (!response.ok) {
    console.error('❌ Booking failed:', await response.text());
    throw new Error('Booking failed');
  }
  
  const result = await response.json();
  console.log('✅ Booking uspešan:', result);
  return result;
}
```

**📝 NAPOMENA:** Kada budete deaktivirali popust, promenite na `0`.

---

## 🚀 KORAK 3: OPCIJA B - Pravo Rešenje (DINAMIČKI)

Za automatsku proveru da li je popust aktivan:

### 3.1. Kreirajte funkciju za proveru popusta

**DODAJTE OVU NOVU FUNKCIJU:**

```javascript
/**
 * Proveri da li je couple popust aktivan u booking sistemu
 * @returns {Promise<number>} - Procenat popusta (0 ako nije aktivan)
 */
async function getCoupleDiscountPercentage() {
  try {
    console.log('🔍 Proveravam popust...');
    
    // Pozovi API booking sistema
    const response = await fetch('https://spabooking.emergent.host/api/services');
    
    if (!response.ok) {
      console.warn('⚠️ Ne mogu da proverim popust, koristim 0%');
      return 0;
    }
    
    const services = await response.json();
    
    // Pronađi "Kartica Masaza za parove" ili bilo koji servis sa popustom
    const serviceWithDiscount = services.find(service => {
      const hasCoupleName = service.name && 
        (service.name.toLowerCase().includes('parove') || 
         service.category === 'Kartica Masaza za parove');
      const hasDiscount = service.discount_percentage > 0;
      
      return hasCoupleName && hasDiscount;
    });
    
    if (serviceWithDiscount) {
      const discount = serviceWithDiscount.discount_percentage;
      console.log(`✅ Aktivan popust: ${discount}%`);
      return discount;
    }
    
    console.log('ℹ️ Nema aktivnog popusta');
    return 0;
    
  } catch (error) {
    console.error('❌ Greška pri proveri popusta:', error);
    return 0;  // Ako je greška, bez popusta
  }
}
```

### 3.2. Ažurirajte booking funkciju

**IZMENITE booking funkciju da koristi dinamički popust:**

```javascript
async function bookCoupleAppointment(formData) {
  // ✅ PRVO: Proveri aktivan popust
  const activeDiscount = await getCoupleDiscountPercentage();
  
  const bookingData = {
    client_first_name: formData.firstName,
    client_last_name: formData.lastName,
    client_phone: formData.phone,
    client_email: formData.email,
    start_time: formatToISO(formData.date, formData.time),
    duration_type: getDurationType(formData.selectedService),
    person1_services: [formData.person1ServiceId],
    person2_services: [formData.person2ServiceId],
    discount_couples_massage: activeDiscount  // ✅ DINAMIČKI POPUST!
  };
  
  console.log(`📤 Šaljem booking sa ${activeDiscount}% popustom`);
  console.log('📦 Booking data:', JSON.stringify(bookingData, null, 2));
  
  const response = await fetch(
    'https://spabooking.emergent.host/api/book-couple-appointment',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(bookingData)
    }
  );
  
  if (!response.ok) {
    const errorText = await response.text();
    console.error('❌ Booking failed:', errorText);
    throw new Error(`Booking failed: ${errorText}`);
  }
  
  const result = await response.json();
  console.log('✅ Booking uspešan:', result);
  
  return result;
}
```

---

## 🧪 KORAK 4: TESTIRANJE

### Test 1: Provera da li kod radi

1. **Otvorite browser console** (F12)
2. **Napravite rezervaciju** za couple masažu
3. **Proverite console logs:**
   ```
   🔍 Proveravam popust...
   ✅ Aktivan popust: 15%
   📤 Šaljem booking sa 15% popustom
   ✅ Booking uspešan: {...}
   ```

### Test 2: Provera u booking sistemu

1. **Ulogujte se** na: https://spabooking.emergent.host
2. **Lozinka:** `studio149`
3. **Idite na Dashboard**
4. **Proverite poslednju rezervaciju:**

**SA POPUSTOM (15%):**
```
Couple masaža - 2x60 min:
Original: 8,800 RSD (precrtano)
Cena: 7,480 RSD [-15%]
```

**SA POPUSTOM (15%):**
```
Couple masaža - 2x90 min:
Original: 11,200 RSD (precrtano)
Cena: 9,520 RSD [-15%]
```

**BEZ POPUSTA (0%):**
```
Couple masaža - 2x60 min:
Cena: 8,800 RSD
```

---

## 📊 MATEMATIKA - Da Proverite Da Li Radi:

| Usluga | Trajanje | Original | Sa 15% | Sa 10% | Sa 20% |
|--------|----------|----------|--------|--------|--------|
| 2x60 min | 60 | 8,800 | 7,480 | 7,920 | 7,040 |
| 2x90 min | 90 | 11,200 | 9,520 | 10,080 | 8,960 |
| 2x120 min | 120 | 13,600 | 11,560 | 12,240 | 10,880 |

---

## ⚠️ ČESTE GREŠKE:

### Greška 1: Pogrešan tip podatka
```javascript
discount_couples_massage: "15"  // ❌ String
discount_couples_massage: 15.0  // ✅ Number
```

### Greška 2: Ne šalje se uopšte
```javascript
// ❌ Nedostaje discount_couples_massage
{
  client_first_name: "...",
  client_last_name: "...",
  // discount_couples_massage: 15.0  <- MORA biti prisutno!
}
```

### Greška 3: Null ili undefined
```javascript
discount_couples_massage: null  // ❌
discount_couples_massage: undefined  // ❌
discount_couples_massage: 0  // ✅ Ako nema popusta
discount_couples_massage: 15.0  // ✅ Ako ima popust
```

---

## 🔧 TROUBLESHOOTING:

### Problem: "I dalje nema popusta u booking sistemu"

**Provere:**

1. **Proveri console logs** - Da li se šalje 15.0?
   ```javascript
   console.log('DISCOUNT:', bookingData.discount_couples_massage);
   ```

2. **Proveri network tab** (F12 → Network):
   - Pronađi `book-couple-appointment` request
   - Klikni na njega
   - Idi na "Payload" ili "Request Payload"
   - Proveri da li je `discount_couples_massage: 15.0`

3. **Proveri response:**
   - U istom request-u, idi na "Response"
   - Proveri `service_id` u odgovoru
   - Proveri u booking sistemu da li taj servis ima popust

### Problem: "Greška pri slanju booking-a"

**Provere:**

1. **Syntax error** - Da li ste dodali zarez (`,`) posle prethodnog polja?
   ```javascript
   person2_services: [formData.person2ServiceId],  // ✅ Zarez!
   discount_couples_massage: 15.0
   ```

2. **URL provera** - Da li je URL tačan?
   ```javascript
   'https://spabooking.emergent.host/api/book-couple-appointment'
   ```

3. **Headers** - Da li su headers tačni?
   ```javascript
   headers: { 'Content-Type': 'application/json' }
   ```

---

## 📞 PODRŠKA:

Ako imate problem, pošaljite:
1. **Console logs** (screenshot ili copy/paste)
2. **Network tab screenshot** (Request Payload)
3. **Kod koji ste izmenili**

---

## ✅ CHECKLIST - Pre nego što završite:

- [ ] Pronađena booking funkcija
- [ ] Dodato `discount_couples_massage: 15.0` (ili dinamička funkcija)
- [ ] Dodati console.log-ovi za debug
- [ ] Testirano u browser-u (console logs)
- [ ] Napravljena test rezervacija
- [ ] Provereno u booking sistemu Dashboard-u
- [ ] Cena je ispravna (7,480 RSD za 2x60 min sa 15%)

---

## 🎉 KRAJNJI REZULTAT:

Kada sve radi kako treba, u booking sistemu ćete videti:

**Dashboard:**
```
📊 Kartica Masaza za parove
   Termini: X
   Zarada: XX,XXX RSD
   💸 Popust Dat: X,XXX RSD  ← OVO će se pojaviti!
```

**Notifikacije:**
```
🔔 Nova rezervacija
   👤 Ime Prezime
   💆 Masaža za parove - 120 min
   
   Original: 8,800 RSD  (precrtano)  ← OVO će se pojaviti!
   💰 Cena: 7,480 RSD [-15%]        ← OVO će se pojaviti!
```

**Listing Rezervacija:**
```
Tabela će prikazivati:
  8,800 RSD (precrtano)  ← OVO će se pojaviti!
  7,480 RSD [-15%]       ← OVO će se pojaviti!
```

---

**Svu sreću! 🚀**
