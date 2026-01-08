# 🎯 KOPIRANO SA RADNE VERZIJE - KAKO RADI

## ✅ TRENUTNO STANJE (Identično Radnoj Verziji)

### Backend:
```
[PAROVI] servisi: 17 servisa
discount_percentage: 0% (SVI - kao na radnoj verziji)
Cene: PUNE, ORIGINALNE cene

Primeri (isto kao radna verzija):
- [PAROVI] Aroma terapija 60 min: 4,400 RSD
- [PAROVI] Tradicionalna 90 min: 5,600 RSD
- [PAROVI] Aromaterapija 120 min: 7,200 RSD
```

**Backend je IDENTIČAN kao na: https://price-analyzer-8.preview.emergentagent.com/**

---

## 🎯 WEBSAJT - KAKO RADI NA RADNOJ VERZIJI

**Radna verzija websajta:** Mora također prikazati 10% popust na kartici, ALI backend ima 0% popust!

**Ovo znači:**
1. Websajt fetch-uje servise (discount = 0%)
2. Websajt LOKALNO primenjuje 10% popust (samo za prikaz)
3. Websajt prikazuje badge "-10%"
4. Websajt šalje `discount_couples_massage: 10` na backend
5. Backend prima taj parametar i onda primenjuje 10% popust

---

## 📝 3 JEDNOSTAVNA KORAKA (Kako Radi Radna Verzija)

### KORAK 1: Fetch Servisa
```javascript
const services = await fetch('https://price-analyzer-8.preview.emergentagent.com/api/services')
  .then(r => r.json());

const coupleServices = services.filter(s => 
  s.name.startsWith('[PAROVI]') && 
  s.category === 'Kartica Masaza za parove'
);

// discount_percentage će biti 0!
console.log('Discount:', coupleServices[0].discount_percentage);  // 0%
console.log('Price:', coupleServices[0].price);  // 4400 (puna cena)
```

### KORAK 2: Primeni 10% LOKALNO (Na Frontend-u)
```javascript
// ZA SVAKI SERVIS:
const originalPrice = service.price;  // 4400 (puna cena)
const discountPercentage = 10;  // Fiksno 10% za karticu
const discountedPrice = originalPrice * (1 - discountPercentage / 100);  // 3960

console.log('Original:', originalPrice);      // 4400
console.log('Sa 10% popustom:', discountedPrice);  // 3960
console.log('Ušteda:', originalPrice - discountedPrice);  // 440
```

### KORAK 3: Prikaži Badge i Cene
```html
<div class="couple-card">
  <!-- Badge -->
  <div class="badge">-10%</div>
  
  <!-- Cene -->
  <div>
    <p>Osoba 1: {service1.name}</p>
    <p class="original">{service1.price} RSD</p>
    <p class="discounted">{service1.price * 0.9} RSD</p>
    
    <p>Osoba 2: {service2.name}</p>
    <p class="original">{service2.price} RSD</p>
    <p class="discounted">{service2.price * 0.9} RSD</p>
    
    <p>Ukupno: {(service1.price + service2.price) * 0.9} RSD</p>
  </div>
</div>
```

### KORAK 4: Pošalji Rezervaciju SA discount Parametrom
```javascript
const booking = {
  client_first_name: "Ana",
  client_last_name: "Jovanović",
  client_phone: "+381601234567",
  client_email: "ana@test.com",
  therapist_id: therapist_id,
  duration_type: 60,
  person1_services: [service1.id],
  person2_services: [service2.id],
  start_time: "2025-11-18T15:00:00",
  discount_couples_massage: 10,  // ← KLJUČNO! Šalješ 10!
  status: "scheduled"
};

await fetch('https://price-analyzer-8.preview.emergentagent.com/api/appointments/couple', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify(booking)
});
```

**KLJUČNO:** 
- Backend ima discount = 0%
- Ti primenjuješ 10% na frontend-u
- Ti šalješ `discount_couples_massage: 10`
- Backend prima taj parametar i onda primenjuje popust

---

## ✅ TESTIRANJE

```javascript
// 1. Fetch
const services = await fetch('https://price-analyzer-8.preview.emergentagent.com/api/services')
  .then(r => r.json());

const couple = services.filter(s => s.name.startsWith('[PAROVI]'));

console.log('Broj servisa:', couple.length);  // 17
console.log('Prvi servis:', couple[0].name);
console.log('Cena:', couple[0].price);  // 4400 (puna cena)
console.log('Discount:', couple[0].discount_percentage);  // 0%

// 2. Lokalni popust
const price1 = couple[0].price;  // 4400
const price2 = couple[1].price;  // 5600
const total = price1 + price2;  // 10000
const discount = total * 0.10;  // 1000
const final = total - discount;  // 9000

console.log('Ukupno:', total);  // 10000
console.log('Popust 10%:', discount);  // 1000
console.log('Finalno:', final);  // 9000

// 3. Badge
// Trebalo bi da vidiš "-10%" na kartici
```

---

## 🔐 GARANCIJA

**Backend (100% Identičan Radnoj Verziji):**
- ✅ [PAROVI] servisi: discount_percentage = 0%
- ✅ Cene: PUNE, originalne
- ✅ Endpoint `/api/appointments/couple` prima `discount_couples_massage` parametar
- ✅ Backend primenjuje popust SAMO kada primi taj parametar

**Websajt (Tvoj Zadatak):**
- ✅ Fetch servise (biće discount = 0%)
- ✅ Primeni 10% LOKALNO (service.price * 0.9)
- ✅ Prikaži badge "-10%"
- ✅ Prikaži precrtanu originalnu cenu
- ✅ Prikaži sniženu cenu
- ✅ Pošalji `discount_couples_massage: 10`

---

## 📞 FINALNA PORUKA

**Backend je IDENTIČAN kao radna verzija:**
- https://price-analyzer-8.preview.emergentagent.com/api

**Tvoj websajt treba da radi ISTO kao radna verzija:**
- Fetch servise (discount = 0%)
- Primeni 10% lokalno
- Prikaži badge
- Pošalji discount parametar

**Ako radiš TAČNO kako piše ovde, MORA raditi!**

**Radna verzija RADI - tvoja treba da radi ISTO!**

---

**Status:** ✅ Backend IDENTIČAN radnoj verziji
**Datum:** 2025-11-17
**Verzija:** FINALNA (kopirano sa radne verzije)
