# 🎯 NOVE INSTRUKCIJE ZA WEBSAJT AGENTA - KONAČNO REŠENJE POPUSTA

## 📋 ŠTA SE PROMENILO?

Backend (Booking sistem) sada implementira **potpuno novu logiku za popuste**:

### ✅ Novi Princip: "Jedan Popust Po Masaži"
**Pravilo**: Za svaku masažu, bez obzira u kojoj kategoriji se pojavljuje, sistem automatski primenjuje **SAMO NAJVEĆI POPUST**.

### 🔧 Kako Sada Funkcioniše Backend?

1. **Service Code Sistem**: Svaka masaža ima jedinstveni `service_code` (npr. `MASAZA_STOPALA_60`)
   - Isti `service_code` za istu masažu u različitim kategorijama
   - Primer: "Aroma terapija - 60 min" i "[PAROVI] Aroma terapija - 60 min" dele isti `service_code`

2. **Automatski Izbor Najvećeg Popusta**:
   - Backend automatski pronalazi sve varijante iste masaže
   - Bira varijantu sa najvećim popustom
   - Primenjuje samo taj jedan popust (nikada ne množi popuste)

3. **Backend je Jedini Izvor Istine**:
   - Sve cene i popusti se izračunavaju na backendu
   - Websajt samo **prikazuje** podatke koje dobije od backend API-ja

---

## 🌐 ŠTA WEBSAJT TREBA DA RADI?

### 📡 API Response Format

Kada websajt poziva `/api/services`, dobija sledeći format:

```json
{
  "id": "51ed3e01-857f-497c-8ac3-f7950784a1d5",
  "name": "Masaža stopala - 60 min",
  "service_code": "MASAZA_STOPALA_60",
  "duration": 60,
  "price": 3150.0,
  "discount_percentage": 15.0,
  "final_price": 2677.5,
  "metadata": {
    "original_price": 3150.0
  },
  "category": "Obicne masaze"
}
```

### ✅ Što Websajt Treba Da Uradi:

#### 1. **Prikazivanje Usluga**
```javascript
// ISPRAVNO ✅
const originalPrice = service.metadata.original_price;
const finalPrice = service.final_price;
const discount = service.discount_percentage;

// Prikaz:
// "Masaža stopala - 60 min"
// Originalna cena: 3150 RSD (precrtana)
// Cena sa popustom: 2677.5 RSD (15% popust)
```

#### 2. **Kreiranje Rezervacije**
```javascript
// SAMO pošalji service_id, NE računaj cenu
fetch('/api/appointments', {
  method: 'POST',
  body: JSON.stringify({
    service_id: service.id,  // ← Samo ID, backend radi sve ostalo
    client_first_name: "...",
    // ... ostali podaci
  })
});
```

#### 3. **Couple Appointments (Masaže za Parove)**
```javascript
// Za couple bookings:
fetch('/api/book-couple-appointment', {
  method: 'POST',
  body: JSON.stringify({
    person1_services: [service_id_1],
    person2_services: [service_id_2],
    discount_couples_massage: 0,  // ← POŠALJI 0 ili ne šalji ovaj parametar
    // Backend će automatski naći i primeniti najbolji popust
  })
});
```

**VAŽNO**: 
- **NE** slati `discount_couples_massage` parametar ako ne želite dodatni popust
- Backend će automatski naći najveće popuste za obe masaže i primeniti najbolji

---

## ⚠️ ŠTA WEBSAJT **NE** TREBA DA RADI

### ❌ NE računati cene na frontend-u
```javascript
// POGREŠNO ❌
const finalPrice = service.price * (1 - discount / 100);
```

### ❌ NE slati sopstvene popuste za couple bookings
```javascript
// POGREŠNO ❌
discount_couples_massage: 10  // Ne slati ako nema posebnog popusta
```

### ❌ NE birati service_id na osnovu toga da li ima popust
```javascript
// POGREŠNO ❌
// Biranje [PAROVI] verzije jer ima 10% popust
const serviceId = service.name.includes('[PAROVI]') ? paroviId : obicniId;

// ISPRAVNO ✅
// Koristiš bilo koji service_id, backend će naći najbolji popust
const serviceId = service.id;
```

---

## 📊 Primeri Realnih Slučajeva

### Primer 1: Masaža Stopala 60 min

**Backend Podaci:**
- "Masaža stopala - 60 min" (Obična): 5% popust
- "[PAROVI] Masaža stopala - 60 min": 15% popust

**Kako Backend Radi:**
1. Obe usluge imaju `service_code: "MASAZA_STOPALA_60"`
2. Backend pronalazi da postoje 2 varijante (5% i 15%)
3. Automatski bira i primenjuje **15% popust**

**Što Websajt Treba:**
- Prikazati: "Masaža stopala - 60 min" sa 15% popustom
- Poslati `service_id` bilo koje od te dve varijante
- Backend će primeniti 15% (najveći dostupan)

### Primer 2: Couple Booking

**Scenario:**
- Osoba 1: "Aroma terapija - 90 min" (ima 10% popust)
- Osoba 2: "Masaža stopala - 60 min" (ima 15% popust)

**Kako Backend Radi:**
1. Pronalazi najbolje popuste za obe masaže: [10%, 15%]
2. Bira **maksimalni popust: 15%**
3. Primenjuje 15% na celokupnu cenu (osoba1 + osoba2)

**Što Websajt Treba:**
```javascript
{
  person1_services: ["aroma-90-id"],
  person2_services: ["stopala-60-id"],
  discount_couples_massage: 0  // Backend će sam naći 15%
}
```

---

## ✅ Finalni Checklist Za Websajt Agenta

- [ ] Koristiti `final_price` iz API response za prikaz cena
- [ ] Koristiti `discount_percentage` iz API response za prikaz popusta
- [ ] **NE** računati cene na frontend-u
- [ ] Za single appointments: samo poslati `service_id`
- [ ] Za couple appointments: poslati `discount_couples_massage: 0` (ili izostaviti)
- [ ] Ukloniti bilo koju logiku koja bira različite service_id na osnovu popusta

---

## 🎉 Rezultat

Sa ovim promenama:
✅ Nikada neće biti duplih popusta
✅ Uvek se primenjuje samo najveći dostupan popust
✅ Backend je jedini izvor istine za cene
✅ Websajt samo prikazuje podatke, ne računa ih

---

**Datum:** 2025-01-16
**Backend Version:** Service Code System v1.0
**Kontakt:** Booking sistem je ažuriran i testiran
