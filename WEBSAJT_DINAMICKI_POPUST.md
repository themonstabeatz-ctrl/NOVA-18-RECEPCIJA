# 🎯 DINAMIČKI POPUST - Couple Masaža

## ✅ AŽURIRANO (13.11.2025 - 23:00):

**Backend SADA PODRŽAVA popuste!** Websajt može da šalje procenat popusta.

**Rezultat:**
- ✅ Ako je popust aktivan (npr. 15%), websajt šalje `discount_couples_massage: 15.0`
- ✅ Backend primenjuje popust i čuva diskontovanu cenu
- ✅ Dashboard, Listing Rezervacija i Notifikacije prikazuju **DISKONTOVANU CENU**
- ✅ Originalna cena se čuva u metadata za referencu

**Primeri:**
- **SA popustom (15%):** 2x 4,400 RSD = 8,800 RSD → 7,480 RSD (prikazana cena)
- **BEZ popusta (0%):** 2x 4,400 RSD = 8,800 RSD (prikazana cena)

---

## 💻 ŠTA WEBSAJT TREBA DA ŠALJE:

**Dinamički popust:**
1. Ako je popust aktivan u booking sistemu → šalji procenat (npr. `15.0`)
2. Ako NEMA popusta → šalji `0`

---

## 💻 KOD ZA WEBSAJT:

```javascript
// AŽURIRAJ BOOKING FUNKCIJU - dinamički popust
async function bookCoupleAppointment(formData, activeDiscount = 0) {
  const bookingData = {
    client_first_name: formData.firstName,
    client_last_name: formData.lastName,
    client_phone: formData.phone,
    client_email: formData.email,
    start_time: formatToISO(formData.date, formData.time),
    duration_type: getDurationType(formData.selectedService),
    person1_services: [formData.person1ServiceId],
    person2_services: [formData.person2ServiceId],
    discount_couples_massage: activeDiscount  // ✅ Dinamički - 0 ili npr. 15.0
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
