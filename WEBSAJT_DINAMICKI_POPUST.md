# 🎯 VAŽNA ISPRAVKA - UKLONJEN POPUST SA COUPLE APPOINTMENTA

## ✅ ŠTA JE URAĐENO (13.11.2025):

**Backend je izmenjen** - couple appointmenti VIŠE NE PRIMENJUJU nikakav popust!

**Rezultat:**
- ✅ Cena je uvek ORIGINALNA (bez popusta)
- ✅ 2x usluga po 4,400 RSD = 8,800 RSD (ne 7,480 RSD)
- ✅ Dashboard prikazuje tačnu cenu

---

## 💻 ŠTA WEBSAJT TREBA DA ŠALJE:

**Jednostavno:**
- Uvek šalji `discount_couples_massage: 0`
- Backend će koristiti originalnu cenu

---

## 💻 KOD ZA WEBSAJT:

```javascript
// AŽURIRAJ BOOKING FUNKCIJU - samo postavi discount na 0
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
    discount_couples_massage: 0  // ✅ UVEK 0 - NEMA POPUSTA
  };
  
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

---

## 🧪 TESTIRANJE:

### Test: Couple Appointment
1. Zakаži termin sa websajta za parove (2x usluga po 4,400 RSD)
2. Dashboard treba da prikaže: **8,800 RSD** ✅ (ORIGINALNA CENA)

---

## 🎯 OČEKIVANI REZULTAT:

✅ **Uvek:** Originalna cena (bez popusta)
✅ **2x 4,400 RSD:** Dashboard prikazuje 8,800 RSD
✅ **2x 5,600 RSD:** Dashboard prikazuje 11,200 RSD

---

## ⚠️ VAŽNO:

- **NEMA više popusta** na couple appointmente
- Websajt treba **UVEK** da šalje `discount_couples_massage: 0`
- Backend će automatski koristiti originalnu cenu

---

Pošalji ovu instrukciju websajt agentu! 🚀
