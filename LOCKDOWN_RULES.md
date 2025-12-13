# 🔒 BUA LUANG SISTEM - FINALNI LOCKDOWN PRAVILA

**Datum kreiranja**: 13. Decembar 2025  
**Status**: LOCKED - Zabranjena izmena bez eksplicitnog odobrenja vlasnika

---

## ⚠️ KRITIČNA PRAVILA

### 1️⃣ FRONTEND NE SME DA RAČUNA CENE ILI POPUSTE

**ZABRANJEN KOD:**
```javascript
// ❌ NIKADA NE RADITI OVO NA FRONTENDU
const finalPrice = originalPrice * (1 - discountPercentage / 100);
const discount = calculateDiscount(price, coupon);
```

**DOZVOLJENO:**
```javascript
// ✅ Frontend SAMO PRIKAZUJE vrednosti sa backenda
const { final_price, discount_percentage } = backendResponse;
```

---

### 2️⃣ BACKEND JE JEDINI IZVOR ISTINE

**Backend endpoints određuju:**
- `final_price` - Finalna cena nakon popusta
- `discount_percentage` - Procenat popusta
- `original_price` - Originalna cena
- `discount_amount` - Iznos popusta u RSD

**Frontend, admin panel i svi agenti MORAJU koristiti ove vrednosti DIREKTNO.**

---

### 3️⃣ COUPLES BOOKING BEZ POPUSTA

**OBAVEZNA PRAVILA:**
```python
# ✅ Kada nema popusta:
discount_percentage = 0
final_price = original_price
discount_amount = 0

# ❌ NIKADA:
discount_percentage = 15  # kada korisnik nije tražio popust
final_price = original_price * 0.85  # automatsko primenjivanje popusta
```

**Implementacija u `/app/backend/server.py` (linija ~1120):**
```python
# 🔒 LOCKED - DO NOT MODIFY
if discount_percentage == 0 or discount_percentage is None:
    discounted_price = original_price
    discount_amount = 0
    discount_percentage = 0
```

---

### 4️⃣ ADMIN PANEL SAMO PRIKAZUJE SNAPSHOT

**Admin panel (Recepcija) SME:**
- ✅ Prikazati `snapshot_original_price`
- ✅ Prikazati `snapshot_discount_percentage`
- ✅ Prikazati `snapshot_price` (finalna cena)
- ✅ Prikazati badge "SA POPUSTOM" ako `discount_percentage > 0`

**Admin panel NE SME:**
- ❌ Računati popust na osnovu service price
- ❌ Primenjivati discount iz service objekta
- ❌ Modifikovati snapshot vrednosti

---

### 5️⃣ PRISTUP BOOKING LOGICI

**KO SME DA MENJA KOD:**
- ✅ Samo backend agent sa eksplicitnim odobrenjem vlasnika

**KO NE SME DA MENJA KOD:**
- ❌ Test agenti
- ❌ QA agenti
- ❌ Website agenti
- ❌ Frontend agenti
- ❌ Pomoćni agenti

---

### 6️⃣ STABILNE ZONE - ZABRANJENE ZA IZMENU

**U fajlu `/app/backend/server.py`:**

#### Zona 1: Single Appointment Booking (linija ~710-825)
```python
# 🔒 LOCKED ZONE - Single Appointment Creation
@api_router.post("/appointments", response_model=Appointment)
async def create_appointment(appointment: AppointmentCreate):
    # ... NE MENJATI BEZ ODOBRENJA
```

#### Zona 2: Couples Appointment Booking (linija ~1050-1230)
```python
# 🔒 LOCKED ZONE - Couples Appointment Creation
@api_router.post("/book-couple-appointment", response_model=Appointment)
async def book_couple_appointment(couple: CoupleBookingRequest):
    # ... NE MENJATI BEZ ODOBRENJA
```

#### Zona 3: Discount Logic (linija ~1113-1126)
```python
# 🔒 LOCKED - Snapshot values from website payload
original_price = couple.original_price
discounted_price = couple.final_price
discount_percentage = couple.discount_percentage
discount_amount = couple.discount_amount

# 🔒 CRITICAL FIX - NO DISCOUNT when requested
if discount_percentage == 0 or discount_percentage is None:
    discounted_price = original_price
    discount_amount = 0
    discount_percentage = 0
```

#### Zona 4: Email Notification (linija ~2116-2250)
```python
# 🔒 LOCKED ZONE - Email Notification Helper
async def send_booking_emails(appointment_data: dict):
    # ... NE MENJATI BEZ ODOBRENJA
```

---

## 🐛 AKO SE POJAVI -15% POPUST BEZ RAZLOGA

**To je BUG i mora se odmah rešiti:**

### Proveri:
1. ✅ Da li frontend šalje `discount_percentage: 0`?
2. ✅ Da li backend log pokazuje `🔒 NO DISCOUNT requested`?
3. ✅ Da li admin panel čita `snapshot_discount_percentage` direktno?

### Bug lokacije:
- **Admin UI** - Ako prikazuje popust a snapshot je 0
- **Frontend** - Ako automatski primenjuje popust
- **Backend** - Ako ignoriše discount_percentage: 0

---

## 📋 PROCEDURA ZA SVAKU IZMENU

1. **Agent mora dobiti eksplicitno odobrenje vlasnika**
2. **Agent mora dokumentovati razlog izmene**
3. **Agent mora testirati pre i posle**
4. **Agent mora ažurirati ovaj dokument**
5. **Agent mora napraviti backup pre izmene**

---

## 🚨 ALARM - Signali da nešto nije u redu

### Ako vidite:
- ❌ Couples booking bez popusta prikazuje -15%
- ❌ Frontend kalkuliše cene
- ❌ Admin panel menja snapshot vrednosti
- ❌ Test agent menja booking logiku
- ❌ Novi endpoint za booking bez konsultacije

### Reakcija:
1. **STOP** - Ne nastaviti sa izmenom
2. **ROLLBACK** - Vratiti na poslednju stabilnu verziju
3. **REPORT** - Obavestiti vlasnika
4. **FIX** - Ispraviti uz odobrenje

---

## ✅ FINALNI CHECKLIST

Pre svakog deployment-a proveriti:

- [ ] Backend je jedini koji računa cene
- [ ] Frontend samo prikazuje snapshot vrednosti
- [ ] Couples booking bez popusta ima discount = 0
- [ ] Admin panel ne računa ništa
- [ ] Email notifikacije rade (ako je SMTP konfigurisan)
- [ ] Stabilne zone nisu modifikovane
- [ ] Svi testovi prolaze
- [ ] CORS je ispravno konfigurisan

---

## 📞 KONTAKT ZA KRITIČNE IZMENE

**Vlasnik sistema**: Mora dati eksplicitno odobrenje za:
- Izmenu booking logike
- Izmenu discount kalkulacija
- Dodavanje novih endpointa
- Modifikaciju stabilnih zona

**Backup lokacija**: `/app/backups/BuaLuang-BACKEND-STABLE-01/`

---

**KRAJ DOKUMENTA**  
**Ova pravila su obavezna za sve agente i developere.**  
**Kršenje ovih pravila može dovesti do nestabilnosti sistema.**
