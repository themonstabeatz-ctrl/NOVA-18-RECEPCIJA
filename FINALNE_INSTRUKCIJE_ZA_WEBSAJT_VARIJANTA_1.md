# 🎯 FINALNE INSTRUKCIJE - VARIJANTA 1 (PREPORUČENO)

## 📋 Nova Logika: Snapshot Od Websajta

Backend sada podržava **dva načina** kreiranja rezervacija:
1. **Varijanta 1 (PREPORUČENO)**: Websajt šalje kompletan pricing snapshot
2. **Varijanta 2 (Backward Compatible)**: Websajt šalje samo `service_id`

### ✅ Preporučeno: Varijanta 1 - Kompletan Snapshot

**Princip**: Popust se računa **samo jednom** (u GET `/api/services`), a backend samo snima te vrednosti.

---

## 🔧 Implementacija za Websajt

### 1. Korak 1: Dobavi Podatke od Backend-a

```javascript
// Pozovi GET /api/services da dobiješ sve usluge sa izračunatim popustima
const response = await fetch('/api/services');
const services = await response.json();

// Svaka usluga izgleda ovako:
const service = {
  id: "51ed3e01-857f-497c-8ac3-f7950784a1d5",
  name: "Masaža stopala - 60 min",
  service_code: "MASAZA_STOPALA_60",
  duration: 60,
  price: 3500.0,                    // Možda zastarelo - nemoj koristiti
  discount_percentage: 15.0,        // ← Najveći popust (već izračunat)
  final_price: 2975.0,              // ← Konačna cena (već izračunata)
  metadata: {
    original_price: 3500.0          // ← Originalna cena bez popusta
  },
  category: "Obicne masaze"
};
```

### 2. Korak 2: Prikaži Korisniku

```javascript
// Prikaži cene korisniku
const originalPrice = service.metadata.original_price;  // 3500 RSD
const discount = service.discount_percentage;           // 15%
const finalPrice = service.final_price;                 // 2975 RSD

// UI prikaz:
// "Masaža stopala - 60 min"
// [precrtano] 3500 RSD
// 2975 RSD (15% popust)
```

### 3. Korak 3: Kreiraj Rezervaciju - Pošalji Snapshot

#### 3a. Single Appointment

```javascript
const appointmentData = {
  // Standardni podaci
  client_first_name: "Marko",
  client_last_name: "Petrović",
  client_phone: "+381641234567",
  client_email: "marko@example.com",
  therapist_id: "...",
  service_id: service.id,
  start_time: "2025-12-10T14:00:00",
  status: "scheduled",
  
  // 🎯 KRITIČNO: Snapshot podaci (sprečava dupliranje obračuna)
  service_code: service.service_code,           // "MASAZA_STOPALA_60"
  original_price: service.metadata.original_price,  // 3500.0
  discount_percentage: service.discount_percentage, // 15.0
  final_price: service.final_price                  // 2975.0
};

const response = await fetch('/api/appointments', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(appointmentData)
});

const appointment = await response.json();
// Backend NE računa popust ponovo, već koristi snapshot iz websajta
```

#### 3b. Couple Appointment

```javascript
// Prvo dobavi obe usluge
const service1 = services.find(s => s.id === person1_service_id);
const service2 = services.find(s => s.id === person2_service_id);

// Izračunaj ukupnu cenu sa popustom
const totalOriginal = service1.metadata.original_price + service2.metadata.original_price;

// Pronađi najveći popust od obe usluge
const maxDiscount = Math.max(service1.discount_percentage, service2.discount_percentage);

// Izračunaj konačnu cenu
const totalFinal = totalOriginal * (1 - maxDiscount / 100);

const coupleAppointmentData = {
  // Standardni podaci
  client_first_name: "Ana",
  client_last_name: "Jović",
  client_phone: "+381641234567",
  client_email: "ana@example.com",
  start_time: "2025-12-11T16:00:00",
  duration_type: 60,
  person1_services: [person1_service_id],
  person2_services: [person2_service_id],
  discount_couples_massage: 0,  // NE šalji dodatni popust osim ako je posebna promocija
  
  // 🎯 KRITIČNO: Snapshot podaci
  original_price: totalOriginal,   // npr. 5900.0
  discount_percentage: maxDiscount,  // npr. 15.0
  final_price: totalFinal           // npr. 5015.0
};

const response = await fetch('/api/book-couple-appointment', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(coupleAppointmentData)
});

const appointment = await response.json();
// Backend NE računa popust ponovo, već koristi snapshot iz websajta
```

---

## 🎯 Ključne Tačke

### ✅ Što Websajt TREBA Da Uradi:

1. **Pozovi GET `/api/services`** da dobiješ sve usluge sa već izračunatim `final_price` i `discount_percentage`
2. **Prikaži te vrednosti** korisniku bez dodatnog računanja
3. **Pošalji iste te vrednosti** u POST request-u kao snapshot
4. **Backend neće računati popust ponovo** - samo snima snapshot

### ❌ Što Websajt NE TREBA Da Uradi:

1. ❌ NE računati popuste na frontend-u
2. ❌ NE birati različite service_id na osnovu popusta
3. ❌ NE slati različite cene od onih koje backend vrati u GET `/api/services`
4. ❌ NE množiti ili sabirati popuste

---

## 🔍 Provera da li Radi Ispravno

### Backend Logovi

Kada websajt šalje snapshot (Varijanta 1), backend treba da loguje:

```
📸 Using snapshot from websajt: original=3500.0, final=2975.0, discount=15.0%
```

Ako websajt NE šalje snapshot (Varijanta 2), backend će logovati:

```
⚙️ Websajt didn't send snapshot - calculating discount from service_code
```

**Cilj**: Uvek videti `📸 Using snapshot from websajt` u logovima!

### Provera Cena

1. Korisnik vidi cenu na websajtu: **2975 RSD** (sa 15% popustom)
2. Backend snimi rezervaciju sa: `snapshot_price: 2975.0`
3. U recepcijskom interfejsu prikazuje se: **2975 RSD**

Sve tri vrednosti moraju biti **identične** - **"što vidiš, to i dobijaš"**.

---

## 📊 Primer Realnog Toka

### Scenario: Korisnik rezerviše "Masažu stopala - 60 min"

```
1. Backend GET /api/services vraća:
   {
     "id": "51ed3e01-...",
     "name": "Masaža stopala - 60 min",
     "service_code": "MASAZA_STOPALA_60",
     "metadata": { "original_price": 3500.0 },
     "discount_percentage": 15.0,
     "final_price": 2975.0
   }

2. Websajt prikazuje:
   - Masaža stopala - 60 min
   - [precrtano] 3500 RSD
   - 2975 RSD (15% popust) ← ISTA VREDNOST

3. Korisnik klikne "Rezerviši"

4. Websajt šalje POST /api/appointments:
   {
     "service_id": "51ed3e01-...",
     "service_code": "MASAZA_STOPALA_60",
     "original_price": 3500.0,
     "discount_percentage": 15.0,
     "final_price": 2975.0,      ← ISTA VREDNOST
     ... ostali podaci
   }

5. Backend loguje:
   📸 Using snapshot from websajt: original=3500.0, final=2975.0, discount=15.0%

6. Backend snima appointment sa:
   {
     "snapshot_price": 2975.0,   ← ISTA VREDNOST
     "snapshot_original_price": 3500.0,
     "snapshot_discount_percentage": 15.0
   }

7. Recepcija vidi rezervaciju:
   - Cena: 2975 RSD ← ISTA VREDNOST

✅ REZULTAT: Nema dupliranja obračuna, sve vrednosti su identične!
```

---

## 🎉 Prednosti Varijante 1

1. ✅ **Popust se računa samo jednom** (u GET `/api/services`)
2. ✅ **Backend ne radi dupli posao** (samo snima snapshot)
3. ✅ **Garantuje konzistentnost** (što korisnik vidi = što se snima)
4. ✅ **Jednostavnije održavanje** (logika popusta je centralizovana)
5. ✅ **Brže izvršavanje** (bez ponovnog pozivanja `get_best_discount_for_service_code()`)

---

## 🔄 Backward Compatibility

Ako websajt NE može odmah da implementira Varijantu 1, backend će nastaviti da radi sa **Varijantom 2** (samo `service_id`). U tom slučaju:

- Backend će pozivati `get_best_discount_for_service_code()` i dalje
- Popust će se računati dva puta (jednom u GET, jednom u POST)
- Rezultat će biti isti, ali je manje efikasno

**Preporuka**: Implementirajte Varijantu 1 čim je moguće.

---

## 📝 Checklist za Websajt Agenta

- [ ] Koristiti `final_price` iz GET `/api/services` response-a
- [ ] Koristiti `discount_percentage` iz GET `/api/services` response-a
- [ ] Koristiti `metadata.original_price` za prikaz precrtane cene
- [ ] Poslati `service_code`, `original_price`, `discount_percentage`, `final_price` u POST request-u
- [ ] Za couple appointments: poslati `original_price`, `discount_percentage`, `final_price`
- [ ] Ukloniti sve lokalne kalkulacije popusta na frontend-u
- [ ] Testirati da backend loguje `📸 Using snapshot from websajt`
- [ ] Verifikovati da su cene identične na websajtu i u recepciji

---

**Datum**: 2025-11-21  
**Verzija**: 2.1 - Snapshot Od Websajta  
**Status**: ✅ Implementirano i Testirano  
**Backend Endpoint**: `/api/appointments` i `/api/book-couple-appointment` podržavaju snapshot
