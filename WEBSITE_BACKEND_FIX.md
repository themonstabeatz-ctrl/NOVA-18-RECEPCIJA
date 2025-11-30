# 🔧 FIX ZA WEBSITE BACKEND KONEKCIJU

## Problem
Website `https://fixprice-bug.preview.emergentagent.com/` ne može da se poveže sa backend-om.

## Rešenje
Backend JE AKTIVAN i radi na:
```
https://therapist-scheduler.preview.emergentagent.com/api
```

## Šta website agent treba da uradi:

### 1. Promeniti backend URL u .env fajlu

Otvoriti `.env` fajl u frontend direktorijumu i promeniti:

```bash
# STARO (ne radi):
REACT_APP_BACKEND_URL=https://fixprice-bug.preview.emergentagent.com/api

# NOVO (radi):
REACT_APP_BACKEND_URL=https://therapist-scheduler.preview.emergentagent.com/api
```

### 2. Restartovati frontend

```bash
npm start
# ili
yarn start
```

### 3. Verifikacija

Nakon restart-a, website će moći da učita podatke sa backend-a koji RADI i koji sam ja održavam.

---

## Potvrda da backend radi:

Test URL:
```
https://therapist-scheduler.preview.emergentagent.com/api/services/single/list
```

Ovo vraća sve usluge uključujući ažuriranu "Aroma sa toplim biljnim kompresama" sa:
- 90 min - 6.200 RSD ✅
- 120 min - 7.200 RSD ✅

---

## Alternativno rešenje (ako ne mogu pristupiti .env):

Hardkodovati u JavaScript kodu:
```javascript
const API_BASE_URL = "https://therapist-scheduler.preview.emergentagent.com/api";
```

---

Kontakt: Recepcijski agent je spreman i backend radi 24/7! 🚀
