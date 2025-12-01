# 🔒 BuaLuang-BACKEND-STABLE-01

**Datum kreiranja:** $(date +"%Y-%m-%d %H:%M:%S")

## Šta je uključeno:

### Backend API (`/backend`)
- ✅ **Services API** - učitavanje usluga sa metadata.original_price/final_price
- ✅ **Booking endpoints:**
  - `POST /api/appointments` - Obične masaže
  - `POST /api/book-couple-appointment` - Masaže za parove
- ✅ **Therapist assignment logic** - therapist_id je optional
- ✅ **Discount calculation logic** - dupli popust rešen
- ✅ **Metadata mapping** - original_price → root level

### Frontend (Recepcija) (`/frontend`)
- ✅ Admin panel za upravljanje terminima
- ✅ Services management
- ✅ Dashboard sa analizama

### .env Configuration
- ✅ MongoDB konekcija
- ✅ Backend URL konfiguracija
- ✅ Eksterni API parametri

## Stabilne zone (NE MENJATI bez dozvole):

### 1. Metadata Mapping Logic
```python
# U server.py - get_services() endpoint
metadata.original_price → service['price']
metadata.final_price → service['final_price']
discount_percentage → koristeći best discount logic
```

### 2. Booking Endpoints
- `/api/appointments` (single massages)
- `/api/book-couple-appointment` (couple massages)

**Payload polja koja MORAJU ostati:**
- client_first_name
- client_last_name
- client_phone
- client_email
- start_time
- service_id
- duration
- notes
- therapist_id (optional)

### 3. Service Fields
- service_code
- category
- discount_percentage
- metadata.*

## Kako restore-ovati ovaj backup:

```bash
# Zaustavi servise
sudo supervisorctl stop backend frontend

# Restore backend
rm -rf /app/backend
cp -r /app/backups/BuaLuang-BACKEND-STABLE-01/backend /app/

# Restore frontend
rm -rf /app/frontend
cp -r /app/backups/BuaLuang-BACKEND-STABLE-01/frontend /app/

# Restore .env
cp /app/backups/BuaLuang-BACKEND-STABLE-01/backend/.env /app/backend/
cp /app/backups/BuaLuang-BACKEND-STABLE-01/frontend/.env /app/frontend/

# Restart servisi
sudo supervisorctl start backend frontend
```

## Testirane usluge u ovom snapshot-u:

✅ "Aroma sa toplim biljnim kompresama - 90 min" - 6.200 RSD (5% popust)
✅ "Aroma sa toplim biljnim kompresama - 120 min" - 7.200 RSD (5% popust)
✅ Sve couple masaže sa 10% popustom
✅ Booking flow od websajta do recepcije

---

**NAPOMENA:** Ovaj backup je STABILAN i testiran. Ne menjaj logiku u stabilnim zonama bez izričite dozvole!
