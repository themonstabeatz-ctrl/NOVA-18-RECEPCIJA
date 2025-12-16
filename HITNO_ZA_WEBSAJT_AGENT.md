# 🚨 HITNO: Fix "Masaža za parove" Booking

## ❌ PROBLEM IDENTIFIKOVAN

Web sajt ima **hardcoded** "Masaža za parove" opcije u regularnom dropdown-u:
```
'couplesMassage|60' → 'Masaža za parove - 60 min - 4,900 RSD'
'couplesMassage|90' → 'Masaža za parove - 90 min - 6,000 RSD'
```

**Ove usluge NE POSTOJE u booking sistemu!** Zato dobijate grešku "molimo pokušajte ponovo".

---

## ✅ REŠENJE

### OPCIJA 1: Ukloni "Masaža za parove" iz Regularnog Bookinga (BRZO)

**Ako "Masaža za parove" NIJE IMPLEMENTIRANA kao posebna stranica:**

1. **Ukloni** `couplesMassage` opcije iz dropdown-a
2. **Ne prikazuj** "Masaža za parove" u regularnom booking-u
3. **Dodaj** na stranicu poruku: "Za masažu za parove, molimo kontaktirajte nas direktno"

**Kod za uklanjanje:**
```javascript
// U fajlu gde se kreira dropdown za usluge
const services = [
  // ... sve ostale usluge ...
  // UKLONI ove linije:
  // { value: 'couplesMassage|60', text: 'Masaža za parove - 60 min - 4,900 RSD' },
  // { value: 'couplesMassage|90', text: 'Masaža za parove - 90 min - 6,000 RSD' },
];
```

---

### OPCIJA 2: Implementiraj Couple Booking Pravilno (POTPUNO REŠENJE)

**Ako želite da couple booking radi:**

#### Korak 1: Ukloni iz Regularnog Dropdown-a

Iz fajla koji generiše dropdown opcije, **obriši** sve što se odnosi na `couplesMassage`.

#### Korak 2: Kreiraj Posebnu Stranicu

Kreiraj novu stranicu `/booking/couple` ili poseban modal za couple booking.

#### Korak 3: Implementiraj Couple Booking Formu

```javascript
// couple-booking-form.js

import { useState, useEffect } from 'react';

export default function CoupleBookingForm() {
  const [services, setServices] = useState([]);
  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    phone: '',
    email: '',
    date: '',
    time: '',
    durationType: 60, // 60, 90, or 120
    person1Service: '',
    person2Service: ''
  });

  // Učitaj sve regularne usluge iz API-ja
  useEffect(() => {
    fetch('https://massage-scheduler-4.preview.emergentagent.com/api/services')
      .then(res => res.json())
      .then(data => {
        // Filtriraj da ne prikazuješ "parove" usluge (ne bi trebalo da ih ima)
        const regular = data.filter(s => !s.name.toLowerCase().includes('parove'));
        setServices(regular);
      });
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();

    // Kombinuj datum i vreme u ISO format
    const startTime = `${formData.date}T${formData.time}:00`;

    const requestBody = {
      client_first_name: formData.firstName,
      client_last_name: formData.lastName,
      client_phone: formData.phone,
      client_email: formData.email || null,
      therapist_id: "VALID_THERAPIST_ID", // Učitaj iz /api/therapists
      duration_type: parseInt(formData.durationType),
      person1_services: [formData.person1Service],
      person2_services: [formData.person2Service],
      start_time: startTime,
      status: 'scheduled',
      discount_couples_massage: 15.0
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
        alert('✅ Termin uspešno zakazan!');
        // Redirect ili prikaži success page
      } else {
        const error = await response.json();
        alert('❌ Greška: ' + JSON.stringify(error));
      }
    } catch (error) {
      console.error('Error:', error);
      alert('❌ Greška pri zakazivanju');
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <h2>Masaža za Parove</h2>

      {/* Client Info */}
      <input 
        type="text"
        placeholder="Ime"
        value={formData.firstName}
        onChange={(e) => setFormData({...formData, firstName: e.target.value})}
        required
      />

      <input 
        type="text"
        placeholder="Prezime"
        value={formData.lastName}
        onChange={(e) => setFormData({...formData, lastName: e.target.value})}
        required
      />

      <input 
        type="tel"
        placeholder="Telefon"
        value={formData.phone}
        onChange={(e) => setFormData({...formData, phone: e.target.value})}
        required
      />

      <input 
        type="email"
        placeholder="Email (opcionalno)"
        value={formData.email}
        onChange={(e) => setFormData({...formData, email: e.target.value})}
      />

      {/* Date & Time */}
      <input 
        type="date"
        value={formData.date}
        onChange={(e) => setFormData({...formData, date: e.target.value})}
        required
      />

      <input 
        type="time"
        value={formData.time}
        onChange={(e) => setFormData({...formData, time: e.target.value})}
        required
      />

      {/* Duration Type */}
      <label>Trajanje (po osobi):</label>
      <select 
        value={formData.durationType}
        onChange={(e) => setFormData({...formData, durationType: e.target.value})}
        required
      >
        <option value="60">60 minuta (ukupno 120 min)</option>
        <option value="90">90 minuta (ukupno 180 min)</option>
        <option value="120">120 minuta (ukupno 240 min)</option>
      </select>

      {/* Person 1 Service */}
      <label>Masaža za osobu 1:</label>
      <select 
        value={formData.person1Service}
        onChange={(e) => setFormData({...formData, person1Service: e.target.value})}
        required
      >
        <option value="">-- Izaberite uslugu --</option>
        {services.map(service => (
          <option key={service.id} value={service.id}>
            {service.name} - {service.price} RSD
          </option>
        ))}
      </select>

      {/* Person 2 Service */}
      <label>Masaža za osobu 2:</label>
      <select 
        value={formData.person2Service}
        onChange={(e) => setFormData({...formData, person2Service: e.target.value})}
        required
      >
        <option value="">-- Izaberite uslugu --</option>
        {services.map(service => (
          <option key={service.id} value={service.id}>
            {service.name} - {service.price} RSD
          </option>
        ))}
      </select>

      <button type="submit">Zakaži Termin</button>
    </form>
  );
}
```

---

## 🎯 HITNA AKCIJA - Šta da Uradiš Odmah?

**MINIMALNA POPRAVKA (5 minuta):**

1. Pronađi fajl gde se kreira dropdown sa uslugama
2. **OBRIŠI** linije koje dodaju `couplesMassage` opcije
3. Deploy
4. **Greška će nestati** jer više ne pokušavate da zakazete nepostojeću uslugu

**NAKON TOGA:**
- Odluči da li želiš da implementiraš couple booking pravilno (sa 2 dropdown menija)
- Ili ostaviš samo kontakt formu za couple massage

---

## 📝 Fajlovi Koje Treba Proveriti

Potraži u web sajt kodu:

```bash
# Pretraži sve fajlove za "couplesMassage"
grep -r "couplesMassage" .

# Ili
grep -r "Masaža za parove" .
```

Verovatno ćeš naći nešto kao:

```javascript
// U booking page komponenti ili constants fajlu
const services = [
  // ...
  { value: 'couplesMassage|60', text: 'Masaža za parove - 60 min - 4,900 RSD' },
  { value: 'couplesMassage|90', text: 'Masaža za parove - 90 min - 6,000 RSD' },
  // ...
];
```

**OBRIŠI TE LINIJE!**

---

## ✅ Provera da Li Je Popravljeno

Nakon što obrišeš `couplesMassage` opcije:

1. Refreshuj web sajt
2. Idi na BOOKING stranicu
3. Otvori dropdown "Izaberite uslugu"
4. **"Masaža za parove" više ne bi trebalo da bude tu**
5. Ostale usluge treba da rade normalno

---

## 🆘 Ako I Dalje Ne Radi

Javi booking sistemu agentu:
- Tačnu poruku greške
- Screenshot problema
- Console log errora (F12 → Console tab)

---

**ZAKLJUČAK:** Web sajt pokušava da zakaže uslugu koja ne postoji u bazi. Ukloni je iz dropdown-a i greška će nestati! 🎯
