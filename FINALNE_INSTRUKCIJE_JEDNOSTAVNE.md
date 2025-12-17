# 🎯 JEDNOSTAVNE INSTRUKCIJE ZA WEBSAJT

## BACKEND JE SPREMAN - SAMO PRIKAŽI!

---

## ✅ BACKEND STANJE (FINALNO):

```
[PAROVI] servisi: 18 servisa
discount_percentage: 10% (SVI)
Cene: VEĆ SNIŽENE za 10%

Primeri:
- [PAROVI] Aroma terapija 60 min: 3,960 RSD (bylo 4,400 RSD)
- [PAROVI] Tradicionalna 90 min: 5,040 RSD (bylo 5,600 RSD)
```

**Backend je GOTOV! Sve je spremno!**

---

## 🎯 TVOJ ZADATAK (3 JEDNOSTAVNA KORAKA):

### KORAK 1: Fetch Servisa
```javascript
const response = await fetch('https://spa-dashboard-2.preview.emergentagent.com/api/services');
const allServices = await response.json();

const coupleServices = allServices.filter(s => s.name.startsWith('[PAROVI]'));

// Proveri:
coupleServices.forEach(service => {
  console.log(service.name);
  console.log('Price:', service.price);  // Već snižena cena
  console.log('Discount:', service.discount_percentage);  // 10%
});
```

### KORAK 2: Prikaži Badge i Cene
```html
<!-- Badge -->
<div class="discount-badge">-10%</div>

<!-- Cene -->
<div>
  <p>Osoba 1: {service1.name}</p>
  <p class="strikethrough">{originalPrice1} RSD</p>
  <p class="discounted">{service1.price} RSD</p>
  
  <p>Osoba 2: {service2.name}</p>
  <p class="strikethrough">{originalPrice2} RSD</p>
  <p class="discounted">{service2.price} RSD</p>
  
  <p>Ukupno sa 10% popustom: {service1.price + service2.price} RSD</p>
</div>
```

**VAŽNO:** 
- `service.price` je VEĆ SNIŽENA cena
- `service.metadata.original_price` je originalna cena (za precrtavanje)

### KORAK 3: Pošalji Rezervaciju
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
  // NEMOJ slati discount_couples_massage!
  status: "scheduled"
};

await fetch('https://spa-dashboard-2.preview.emergentagent.com/api/appointments/couple', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify(booking)
});
```

**NEMOJ SLATI `discount_couples_massage` parametar!**
Backend već ima popust, ne treba ti!

---

## ❌ ŠTA NE SMEŠ RADITI:

1. ❌ NE dodavaj dodatnih 10% u kalkulaciji
2. ❌ NE menjaj backend popuste
3. ❌ NE šalji `discount_couples_massage` parametar
4. ❌ NE primenjuj dvostruki popust

## ✅ ŠTA TREBAŠ URADITI:

1. ✅ Fetch servise
2. ✅ Prikaži badge "-10%"
3. ✅ Prikaži precrtanu originalnu cenu
4. ✅ Prikaži sniženu cenu (service.price)
5. ✅ Pošalji rezervaciju BEZ discount parametra

---

## 📊 KAKO UZETI ORIGINALNU CENU:

```javascript
const service = coupleServices[0];

// Snižena cena (trenutna)
const discountedPrice = service.price;  // 3960 RSD

// Originalna cena (za precrtavanje)
const originalPrice = service.metadata?.original_price || (service.price / 0.9);

console.log('Originalna:', originalPrice);  // 4400 RSD
console.log('Snižena:', discountedPrice);   // 3960 RSD
console.log('Popust:', service.discount_percentage);  // 10%
```

---

## 🧪 TEST:

```javascript
// 1. Fetch
const services = await fetch('https://spa-dashboard-2.preview.emergentagent.com/api/services').then(r => r.json());
const couple = services.filter(s => s.name.startsWith('[PAROVI]'));

console.log('Broj servisa:', couple.length);  // Trebalo bi 18
console.log('Prvi servis:', couple[0].name);
console.log('Cena:', couple[0].price);  // Snižena cena
console.log('Popust:', couple[0].discount_percentage);  // 10%

// 2. Proveri da li badge radi
// Otvori: https://spa-dashboard-2.preview.emergentagent.com/massage
// Trebalo bi da vidiš badge sa "-10%"
```

---

## 🎉 TO JE TO!

Backend je spreman! Svi [PAROVI] servisi imaju 10% popust!

**Ti samo fetch-uješ i prikazuješ!**

**Nema kalkulacija, nema parametara, nema komplikacija!**

---

## 📞 AKO NEŠTO NE RADI:

Proveri:
1. Da li fetch-uješ sa ispravnog URL-a?
2. Da li vidiš discount_percentage = 10%?
3. Da li prikazuješ badge "-10%"?
4. Da li šalješ rezervaciju BEZ discount parametra?

Ako sve ovo radiš, MORA raditi!

---

**Backend URL:** https://spa-dashboard-2.preview.emergentagent.com/api
**Status:** ✅ PRODUCTION READY
**Popusti:** ✅ 10% aktivni na svim [PAROVI] servisima
