# 🚨 URGENTNO - Websajt NE Šalje Popust!

## ❌ PROBLEM:

Korisnik je rezervisao couple masažu preko websajta, ali **NEMA POPUSTA** iako je aktivan -15%!

**Šta se dešava:**
- Websajt šalje: `discount_couples_massage: 0` (ili ne šalje)
- Backend prima: 0% popust
- Kreira se rezervacija BEZ popusta
- Cena: 15,600 RSD umesto 7,480 RSD

---

## ✅ REŠENJE:

Websajt **MORA** da pošalje aktivni popust u booking zahtevu!

---

## 📋 KAKO PROVERITI DA LI JE POPUST AKTIVAN:

### **Opcija 1: Hardkodovano (brzo rešenje)**

Ako je popust **UVEK 15%** dok je aktivan:

```javascript
// PRIVREMENO HARDKODOVANO REŠENJE
const ACTIVE_DISCOUNT = 15.0;  // Ili 0 ako nije aktivan

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
    discount_couples_massage: ACTIVE_DISCOUNT  // ✅ 15.0 dok je aktivan!
  };
  
  // ... rest of code
}
```

**Promenite `ACTIVE_DISCOUNT` na:**
- `15.0` - Dok je popust aktivan
- `0` - Kada deaktivirate popust

---

### **Opcija 2: Dinamički (pravo rešenje)**

Proveri sa booking sistema da li je popust aktivan:

```javascript
// 1. FUNKCIJA: Proveri da li je popust aktivan
async function getCoupleDiscount() {
  try {
    // Pozovi booking API da proveri uslugu
    const response = await fetch('https://spabooking.emergent.host/api/services');
    const services = await response.json();
    
    // Nađi "Kartica Masaza za parove" kategoriju
    const coupleService = services.find(s => 
      s.category === 'Kartica Masaza za parove' && 
      s.discount_percentage > 0
    );
    
    // Ako postoji aktivan popust, vrati ga
    if (coupleService && coupleService.discount_percentage > 0) {
      console.log(`✅ Aktivan popust: ${coupleService.discount_percentage}%`);
      return coupleService.discount_percentage;
    }
    
    console.log('❌ Nema aktivnog popusta');
    return 0;
    
  } catch (error) {
    console.error('Greška pri proveri popusta:', error);
    return 0;  // Ako greška, bez popusta
  }
}

// 2. FUNKCIJA: Booking sa dinamičkim popustom
async function bookCoupleAppointment(formData) {
  // Prvo proveri popust
  const activeDiscount = await getCoupleDiscount();
  
  const bookingData = {
    client_first_name: formData.firstName,
    client_last_name: formData.lastName,
    client_phone: formData.phone,
    client_email: formData.email,
    start_time: formatToISO(formData.date, formData.time),
    duration_type: getDurationType(formData.selectedService),
    person1_services: [formData.person1ServiceId],
    person2_services: [formData.person2ServiceId],
    discount_couples_massage: activeDiscount  // ✅ Dinamički!
  };
  
  console.log(`📤 Šaljem booking sa ${activeDiscount}% popustom`);
  
  const response = await fetch(
    'https://spabooking.emergent.host/api/book-couple-appointment',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(bookingData)
    }
  );
  
  // ... rest of code
}
```

---

## 🧪 KAKO TESTIRATI:

### **Test 1: Privremeno Hardkodovano**
1. Postavi `const ACTIVE_DISCOUNT = 15.0;`
2. Zakаži rezervaciju
3. Proveri Dashboard - treba da bude **7,480 RSD**

### **Test 2: Dinamički**
1. Implementiraj `getCoupleDiscount()` funkciju
2. Zakаži rezervaciju
3. Proveri console.log za poruku o popustu
4. Proveri Dashboard

---

## ⚠️ VAŽNO:

**BEZ OVOGA POPUST NE RADI!**

Booking sistem je spreman i radi perfektno, ali **MORA** da primi `discount_couples_massage` parametar sa pravom vrednošću.

**Trenutno stanje:**
```javascript
discount_couples_massage: 0  // ❌ Websajt šalje 0
```

**Treba da bude:**
```javascript
discount_couples_massage: 15.0  // ✅ Šalje aktivan popust
```

---

## 📞 BRZO REŠENJE:

Ako ne možete odmah da implementirate dinamičku proveru, **privremeno hardkodujte 15.0** dok je popust aktivan!

```javascript
discount_couples_massage: 15.0  // Privremeno dok se ne implementira dinamička provera
```

Kasnije možete dodati dinamičku logiku.

---

**Sve je spremno na booking sistemu, samo websajt treba da pošalje ispravan procenat!** 🚀
