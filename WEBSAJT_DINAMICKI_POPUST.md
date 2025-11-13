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
