# 🔒 STABLE ZONES - PRAVILA ZA BUA LUANG SPA SISTEM

**Verzija:** BuaLuang-BACKEND-STABLE-01  
**Datum:** $(date +"%Y-%m-%d")

---

## ⚠️ KRITIČNA PRAVILA - OBAVEZNA ZA POŠTOVANJE

### 1️⃣ **STABILNE ZONE - NE MENJATI BEZ DOZVOLE**

Sledeće delove koda **NE SMEŠ MENJATI** bez izričite dozvole korisnika:

#### 📍 **Backend - Metadata & Discount Logic** (`/app/backend/server.py`)

**Endpoint:** `GET /api/services`
- **Linije:** ~463-527
- **Šta radi:** 
  - Učitava usluge iz baze
  - Koristi `metadata.original_price` i `metadata.final_price`
  - Primenjuje `best_discount_percentage` logiku
  - Rešava problem duplog popusta

**🔒 Zabranjeno:**
- Menjati način na koji se čitaju `metadata` polja
- Menjati `discount_percentage` kalkulaciju
- Brisati ili preimenovati `service_code` logiku
- Menjati način primene popusta

**✅ Dozvoljeno:**
- Dodavati nove logove (sa префиксом `[DEBUG]`)
- Dodavati nove filtere ako ne diraju postojeću logiku
- Optimizovati performanse ako ne menja rezultat

---

#### 📍 **Backend - Booking Endpoints** (`/app/backend/server.py`)

##### **A) Single Appointments:**
**Endpoint:** `POST /api/appointments`
- **Linije:** ~666-750
- **Payload polja (NE DIRATI):**
  ```json
  {
    "client_first_name": "string",
    "client_last_name": "string",
    "client_phone": "string",
    "client_email": "string (optional)",
    "start_time": "datetime",
    "service_id": "string",
    "therapist_id": "string (optional - dodeljuje recepcionar)",
    "body_map_gender": "string (optional)",
    "body_map_points": "array (optional)"
  }
  ```

##### **B) Couple Appointments:**
**Endpoint:** `POST /api/book-couple-appointment`
- **Linije:** ~982-1100
- **Payload polja (NE DIRATI):**
  ```json
  {
    "client_first_name": "string",
    "client_last_name": "string",
    "client_phone": "string",
    "client_email": "string (optional)",
    "start_time": "datetime",
    "duration_type": "int (60/90/120)",
    "person1_services": ["service_id1", ...],
    "person2_services": ["service_id2", ...],
    "discount_couples_massage": "float (popust u %)"
  }
  ```

**🔒 Zabranjeno:**
- Brisati ili preimenovati bilo koje od gore navedenih polja
- Menjati način na koji se kreira `appointment` objekat
- Menjati logiku `snapshot` polja (`snapshot_price`, `snapshot_original_price`, `snapshot_discount_percentage`)
- Menjati način na koji se računa `end_time`

**✅ Dozvoljeno:**
- Dodavati nova OPCIONALNA polja
- Dodavati validacije koje ne blokiraju postojeći flow
- Poboljšati error handling bez menjanja success flow-a

---

#### 📍 **Backend - Therapist Assignment** (`/app/backend/server.py`)

**Endpoint:** `PATCH /api/appointments/{appointment_id}/assign-therapist`
- **Linije:** ~1235-1290
- **Šta radi:** Recepcionar manuelno dodeljuje terapeuta terminima

**🔒 Zabranjeno:**
- Automatski dodeljivati terapeuta pri kreiranju termina
- Menjati endpoint signature
- Menjati overlap detection logiku

---

### 2️⃣ **NOVE IZMENE - KAKO RADITI BEZBEDNO**

#### ✅ **Dodavanje novih usluga:**

1. **Kopiraj postojeću uslugu koja RADI**
   ```bash
   # Primer: Kopiraj "Masaža toplim uljem - 90 min"
   ```

2. **Promeni samo ova polja:**
   - `name` - Novi naziv
   - `duration` - Novo trajanje
   - `price` - **ORIGINALNA cena** (ne snižena!)
   - `discount_percentage` - Popust u %
   - `metadata.original_price` - Ista kao `price`
   - `metadata.final_price` - `price * (1 - discount/100)`
   - `service_code` - Jedinstveni kod (npr. `NOVA_USLUGA_120`)

3. **NE DIRATI:**
   - `category` - Mora biti isti kao kod template usluge
   - `is_couple` - Mora biti isti kao kod template usluge

#### ✅ **Dodavanje novih endpointa:**

- Kreiraj NOVE endpointe, ne menjaj postojeće
- Označи nove endpointe sa `# NEW ENDPOINT - {datum}`
- Testiraj novi endpoint ODVOJENO od stabilnih

#### ✅ **Debugging:**

1. Koristi `logger.info()` sa prefiksom `[DEBUG]`
2. Dodaj logove **SAMO NA POČETKU I KRAJU funkcije**, ne u sredinu stabilne logike
3. Format: 
   ```python
   logger.info(f"[DEBUG] {naziv_funkcije} - INPUT: {data}")
   logger.info(f"[DEBUG] {naziv_funkcije} - OUTPUT: {result}")
   ```

---

### 3️⃣ **ŠTA RADITI KADA SE POJAVI PROBLEM**

#### ❌ **NE RADI:**
1. ~~Odmah menjati stabilne zone bez dozvole~~
2. ~~"Pokušavati različite pristupe" na produkciji~~
3. ~~Brisati usluge koje "možda ne trebaju"~~
4. ~~Eksperimentisati sa `service_code` ili `category` polja~~

#### ✅ **RADI:**

1. **Prikupi informacije:**
   ```bash
   # Uzmi JSON problematične usluge
   curl http://localhost:8001/api/services/{id}
   
   # Uzmi backend logove
   tail -50 /var/log/supervisor/backend.err.log
   
   # Uzmi frontend console errors (ako postoje)
   ```

2. **Opiši problem korisniku:**
   - Koja usluga je problematična?
   - Šta je očekivano ponašanje?
   - Šta se dešava?
   - JSON problematične usluge
   - Relevantni logovi

3. **Čekaj odobrenje pre izmene stabilnih zona**

4. **Ako je dozvoljeno, napravi izmenu:**
   - Uredi samo ono što je dozvoljeno
   - Testiraj lokalno sa `curl`
   - Dokumentuj šta si promenio
   - Commit sa jasnom porukom

---

### 4️⃣ **TESTING CHECKLIST PRE BILO KOJE IZMENE**

Ako MORAŠ da menjaš nešto u stabilnim zonama (sa dozvolom):

- [ ] Backup trenutnog stanja (`cp /app/backend/server.py /app/backend/server.py.backup`)
- [ ] Testiraj POSTOJEĆE endpointe sa `curl` BEFORE izmene
- [ ] Uradi izmenu
- [ ] Testiraj ISTE endpointe sa `curl` AFTER izmene
- [ ] Uporedi rezultate - moraju biti identični (osim namerne promene)
- [ ] Ako nešto ne radi, restore backup i javi korisniku

---

### 5️⃣ **GIT COMMIT PRAVILA**

**Format commit poruke:**
```
[TIP] Kratak opis (max 50 karaktera)

Detaljan opis:
- Šta je promenjeno
- Zašto je promenjeno
- Da li je testיrano

Related: BuaLuang-BACKEND-STABLE-01
```

**Tipovi:**
- `[STABLE]` - Izmene u stabilnim zonama (RETKO, sa dozvolom)
- `[FEATURE]` - Nova funkcionalnost
- `[FIX]` - Bug fix koji NE dira stabilne zone
- `[DEBUG]` - Dodavanje logova
- `[BACKUP]` - Kreiranje backup-a

---

## 📋 **QUICK REFERENCE**

### Šta JE dozvoljeno:
✅ Dodavati nove usluge po šablonu  
✅ Dodavati debug logove  
✅ Kreirati nove endpointe  
✅ Optimizovati performanse (bez menjanja rezultata)  
✅ Dodavati nova opcionalna polja  

### Šta NIJE dozvoljeno (bez dozvole):
❌ Menjati metadata.original_price/final_price logiku  
❌ Menjati discount calculation  
❌ Brisati ili preimenovati payload polja u booking endpointima  
❌ Menjati service_code ili category postojećih usluga  
❌ Automatski dodeljivati terapeuta  
❌ Eksperimentisati na stabilnim zonama  

---

## 🆘 **U SLUČAJU PROBLEMA**

1. **STOP** - Ne menjaj ništa odmah
2. **ASSESS** - Prikupi informacije (JSON, logovi, opis problema)
3. **REPORT** - Javi korisniku sa svim detaljima
4. **WAIT** - Čekaj dozvolu ili uputstva
5. **ACT** - Uradi samo ono što je dozvoljeno
6. **TEST** - Testiraj pre commit-a
7. **DOCUMENT** - Zapiši šta si uradio

---

**Poslednje ažuriranje:** $(date +"%Y-%m-%d %H:%M:%S")  
**Verzija:** BuaLuang-BACKEND-STABLE-01  
**Status:** 🔒 ACTIVE - LOCKED
