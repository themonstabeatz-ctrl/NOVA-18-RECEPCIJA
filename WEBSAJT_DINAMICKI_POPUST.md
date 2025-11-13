# 🎯 VAŽNA ISPRAVKA - UKLONJEN POPUST SA COUPLE APPOINTMENTA

## ✅ ŠTA JE URAĐENO (13.11.2025):

**Backend je izmenjen** - couple appointmenti VIŠE NE PRIMENJUJU nikakav popust!

**Rezultat:**
- ✅ Cena je uvek ORIGINALNA (bez popusta)
- ✅ 2x usluga po 4,400 RSD = 8,800 RSD (ne 7,480 RSD)
- ✅ Dashboard prikazuje tačnu cenu

---

## 💻 ŠTA WEBSAJT TREBA DA ŠALJE:

Websajt treba da:
1. Proveri DA LI izabrane usluge imaju aktivan popust
2. Ako DA - pošalje taj procenat
3. Ako NE - pošalje 0

---

## 💻 KOD KOJI TREBA PROMENITI:

### 1. Funkcija za Kalkulaciju Popusta

```javascript
// NOVA FUNKCIJA - Dodaj ovu funkciju u bookingApi.js ili main.js
function calculateCoupleDiscount(person1ServiceId, person2ServiceId, services) {
  // Pronađi izabrane usluge
  const service1 = services.find(s => s.id === person1ServiceId);
  const service2 = services.find(s => s.id === person2ServiceId);
  
  if (!service1 || !service2) {
    return 0; // Ako nema usluga, nema popusta
  }
  
  // Uzmi discount_percentage iz svake usluge
  const discount1 = service1.discount_percentage || 0;
  const discount2 = service2.discount_percentage || 0;
  
  // Prosečan popust (ili možeš uzeti maksimum)
  const averageDiscount = (discount1 + discount2) / 2;
  
  console.log('🔍 Discount Calculation:');
  console.log('  Service 1:', service1.name, '- Discount:', discount1 + '%');
  console.log('  Service 2:', service2.name, '- Discount:', discount2 + '%');
  console.log('  Final discount:', averageDiscount + '%');
  
  return averageDiscount;
}
```

### 2. Ažuriraj Booking Funkciju

```javascript
// STARO - OBRIŠI OVO:
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
    discount_couples_massage: 15.0  // ❌ HARDKODOVANO
  };
  // ... rest of code
}

// NOVO - KORISTI OVO:
async function bookCoupleAppointment(formData, services) {  // ← Dodaj 'services' parametar
  // Izračunaj dinamički popust
  const dynamicDiscount = calculateCoupleDiscount(
    formData.person1ServiceId,
    formData.person2ServiceId,
    services
  );
  
  const bookingData = {
    client_first_name: formData.firstName,
    client_last_name: formData.lastName,
    client_phone: formData.phone,
    client_email: formData.email,
    start_time: formatToISO(formData.date, formData.time),
    duration_type: getDurationType(formData.selectedService),
    person1_services: [formData.person1ServiceId],
    person2_services: [formData.person2ServiceId],
    discount_couples_massage: dynamicDiscount  // ✅ DINAMIČKI
  };
  
  console.log('📤 Sending booking with discount:', dynamicDiscount + '%');
  
  const response = await fetch(
    'https://spabooking.emergent.host/api/book-couple-appointment',
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

### 3. Prosleđivanje Services Pri Pozivu

```javascript
// U komponenti gde pozivas bookCoupleAppointment:

const handleSubmit = async (e) => {
  e.preventDefault();
  
  try {
    setLoading(true);
    setError(null);
    
    // Učitaj services ako već nisu učitane
    if (!services || services.length === 0) {
      const response = await fetch('https://spabooking.emergent.host/api/services');
      const servicesData = await response.json();
      setServices(servicesData);
    }
    
    // Pozovi booking SA services parametrom
    const appointment = await bookCoupleAppointment(formData, services);  // ← Dodaj 'services'
    
    // Uspešno!
    showBookingConfirmation(appointment);
    
  } catch (error) {
    setError('Došlo je do greške pri zakazivanju.');
  } finally {
    setLoading(false);
  }
};
```

---

## 🧪 TESTIRANJE:

### Test 1: BEZ Aktivnog Popusta
1. Idi u booking sistem: https://spabooking.emergent.host/services
2. Proveri da "Kartica Masaza za parove" NEMA popusta (0%)
3. Zakаži termin sa websajta (2x usluga po 4,400 RSD = 8,800 RSD)
4. Dashboard treba da prikaže: **8,800 RSD** ✅

### Test 2: SA Aktivnim Popustom (15%)
1. Idi u booking sistem: https://spabooking.emergent.host/services
2. Postavi 15% popust na "Kartica Masaza za parove"
3. Zakаži termin sa websajta (2x usluga po 4,400 RSD = 8,800 RSD)
4. Dashboard treba da prikaže: **7,480 RSD** (8,800 - 15%) ✅

---

## 🎯 OČEKIVANI REZULTAT:

✅ **Bez popusta:** Originalna cena (8,800 RSD)
✅ **Sa 15% popustom:** Diskontovana cena (7,480 RSD)
✅ **Sa 10% popustom:** Diskontovana cena (7,920 RSD)
✅ **Sa 5% popustom:** Diskontovana cena (8,360 RSD)

---

## ⚠️ NAPOMENA:

Ako Osoba 1 ima 15% popust, a Osoba 2 ima 10% popust:
- Prosečan popust: (15 + 10) / 2 = **12.5%**

Ili možeš koristiti:
- Maksimum popust: Math.max(15, 10) = **15%**
- Minimum popust: Math.min(15, 10) = **10%**

Trenutno koristi **prosek** (average), ali možeš promeniti u funkciji `calculateCoupleDiscount()`.

---

Pošalji ovu instrukciju websajt agentu! 🚀
