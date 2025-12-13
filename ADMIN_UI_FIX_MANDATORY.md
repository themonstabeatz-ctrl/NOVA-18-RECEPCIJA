# 🚨 KRITIČNO: Admin Panel NE SME Da Računa Popust iz Service

**Datum**: 13. Decembar 2025  
**Prioritet**: CRITICAL - MORA BITI ISPRAVLJENO ODMAH  
**Status**: BUG U ADMIN UI - Backend radi ispravno

---

## ⚠️ PROBLEM

Admin panel prikazuje **lažni popust od -15%** čak i kada appointment NEMA popust.

### DOKAZ IZ BAZE:

```json
{
  "id": "10aadf56-5b01-411b-bbc0-8bf0a3e7f45d",
  "category": "couple",
  "snapshot_discount_percentage": 0.0,
  "snapshot_original_price": 8800.0,
  "snapshot_price": 8800.0,
  "client_first_name": "AdminUI",
  "client_last_name": "TestBezPopusta"
}
```

**Backend vraća:**
- `discount_percentage = 0`
- `final_price = original_price`
- **NEMA POPUSTA**

**Admin panel pokazuje:**
- ❌ Badge "-15%"
- ❌ Precrtanu cenu
- ❌ Pogrešan popust

---

## 🔍 UZROK PROBLEMA

Admin panel koristi **POGREŠAN IZVOR** za prikaz popusta:

### ❌ ZABRANJENO (Ovo admin panel trenutno radi):
```javascript
// Admin panel greška - koristi service umesto appointmenta
const discount = service.discount_percentage;  // POGREŠNO!
const finalPrice = service.price * (1 - discount / 100);  // POGREŠNO!

// Ili koristi "default" couples discount
const discount = 15;  // NIKADA HARDCODE!
```

### ✅ ISPRAVNO (Ovo admin panel MORA da radi):
```javascript
// Koristiti SAMO appointment snapshot vrednosti
const discount = appointment.snapshot_discount_percentage;
const originalPrice = appointment.snapshot_original_price;
const finalPrice = appointment.snapshot_price;

// Provera da li postoji popust:
const hasDiscount = discount > 0 && finalPrice < originalPrice;
```

---

## 🔧 OBAVEZNA ISPRAVKA

### Korak 1: Pronaći fajlove koji prikazuju appointmente

Mogući fajlovi (PRIMER):
- `/app/frontend/src/pages/Appointments.js`
- `/app/frontend/src/pages/DashboardNew.js`
- `/app/frontend/src/components/Navbar.js`
- `/app/frontend/src/components/AppointmentCard.js`

### Korak 2: Ispraviti logiku prikaza popusta

**ZABRANJENO:**
```javascript
// ❌ NE RADITI OVO
{service.discount_percentage > 0 && (
  <Badge>-{service.discount_percentage}%</Badge>
)}

// ❌ NE RADITI OVO
const finalPrice = calculateDiscount(service.price, service.discount);
```

**OBAVEZNO:**
```javascript
// ✅ ISPRAVNO
{appointment.snapshot_discount_percentage > 0 && 
 appointment.snapshot_price < appointment.snapshot_original_price && (
  <Badge>-{appointment.snapshot_discount_percentage}%</Badge>
)}

// ✅ ISPRAVNO - prikaz cene
<div>
  {appointment.snapshot_discount_percentage > 0 ? (
    <>
      <span className="line-through text-gray-500">
        {appointment.snapshot_original_price} RSD
      </span>
      <span className="text-green-600 font-bold">
        {appointment.snapshot_price} RSD
      </span>
    </>
  ) : (
    <span className="font-bold">
      {appointment.snapshot_price} RSD
    </span>
  )}
</div>
```

### Korak 3: Uslov za prikaz badge-a

**KRITIČNO PRAVILO:**
```javascript
// Badge se prikazuje SAMO ako su SVI uslovi ispunjeni:
const shouldShowDiscount = (
  appointment.snapshot_discount_percentage > 0 &&
  appointment.snapshot_price < appointment.snapshot_original_price &&
  appointment.snapshot_original_price > 0
);

{shouldShowDiscount && (
  <Badge className="bg-green-500">
    -{appointment.snapshot_discount_percentage}%
  </Badge>
)}
```

---

## 📋 CHECKLIST ZA AGENTA

### Pre Izmene:
- [ ] Pronaći SVE fajlove koji prikazuju appointmente
- [ ] Identifikovati gde se prikazuje badge popusta
- [ ] Identifikovati gde se prikazuje cena

### Tokom Izmene:
- [ ] Zameniti `service.discount_percentage` sa `appointment.snapshot_discount_percentage`
- [ ] Zameniti `service.price` sa `appointment.snapshot_price`
- [ ] Dodati uslov: `discount > 0 && final < original`
- [ ] Ukloniti sve kalkulacije cena u UI-u

### Posle Izmene:
- [ ] Testirati sa appointmentom ID: `10aadf56-5b01-411b-bbc0-8bf0a3e7f45d`
- [ ] Potvrditi da se NE prikazuje -15% badge
- [ ] Potvrditi da se prikazuje samo: `8.800 RSD` (bez precrtane cene)
- [ ] Screenshot rezultata

---

## 🚨 UPOZORENJE ZA AGENTA

### ✅ DOZVOLJENO:
- Menjati SAMO UI prikaz (badge, label, text)
- Koristiti `appointment.snapshot_*` polja
- Dodavati uslove za prikaz

### ❌ ZABRANJENO:
- Menjati booking logiku u backendu
- Menjati kalkulaciju popusta
- Menjati cene
- Dodavati nove endpointe
- Menjati `server.py` locked zone
- Menjati discount logiku

**ZABRANJENO je menjati booking logiku, popuste i cene. Dopuštene su samo UI korekcije prikaza (badge/label) i isključivo u navedenim fajlovima. Svaka druga izmena = rollback i prekid saradnje.**

---

## 📸 POTVRDA ISPRAVKE

Nakon ispravke, agent MORA da dostavi:

1. **Screenshot appointmenta gde se vidi:**
   - Ime: "AdminUI TestBezPopusta"
   - Cena: 8.800 RSD (bez precrtane cene)
   - **NEMA** badge-a "-15%"

2. **Git diff izmena** (samo UI fajlova)

3. **Potvrdu:**
   ```
   ✅ Admin panel sada prikazuje snapshot vrednosti
   ✅ Nema lažnog popusta kada je discount = 0
   ✅ Badge se prikazuje SAMO kada discount > 0
   ```

---

## 🔍 KAKO TESTIRATI

### Test 1: Appointment BEZ popusta
```bash
GET /api/appointments
# Pronaći: ID = 10aadf56-5b01-411b-bbc0-8bf0a3e7f45d
# Očekivano u admin panelu:
# ✅ Cena: 8.800 RSD
# ✅ NEMA badge-a
# ✅ NEMA precrtane cene
```

### Test 2: Appointment SA popustom
```bash
GET /api/appointments
# Pronaći appointment sa discount > 0
# Očekivano u admin panelu:
# ✅ Badge "-15%"
# ✅ Precrtana originalna cena
# ✅ Zelena finalna cena
```

---

## ⚡ HITNO

Ova ispravka je **KRITIČNA** i mora biti urađena **PRE** bilo kakvih drugih izmena.

**Rok**: ODMAH  
**Prioritet**: P0 - Blocking sve ostalo  
**Odgovoran**: Admin Panel Agent

---

**KRAJ DOKUMENTA**  
**Vlasnik sistema: Sva prava zadržana**
