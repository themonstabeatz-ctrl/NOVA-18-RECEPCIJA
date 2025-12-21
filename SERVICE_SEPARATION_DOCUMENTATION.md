# 🎯 Раздвајање Single и Couple Услуга - Документација

## 📋 Преглед

Систем сада јасно раздваја **single услуге** ("Obične masaže") и **couple услуге** ("[PAROVI]" из "Kartica Masaza za parove") помоћу `is_couple` marker-а.

---

## 🔧 Имплементација

### 1. Нови Field: `is_couple`

Додато ново поље у `Service` модел:
```python
is_couple: bool = Field(default=False, description="True if this is a couple/[PAROVI] service")
```

**Вредности:**
- `is_couple = True` → Couple услуга из "Kartica Masaza za parove" (са [PAROVI] префиксом)
- `is_couple = False` → Single услуга из "Obične masaže"

---

## 📊 База Података

**После миграције:**
- ✅ **19 couple услуга** (`is_couple=True`) - све из категорије "Kartica Masaza za parove"
- ✅ **101 single услуга** (`is_couple=False`) - све остале ("Obične masaže" + couple техничке)
- ✅ **Укупно**: 120 услуга

**Примери:**

| Име Услуге | Категорија | is_couple |
|-----------|-----------|-----------|
| [PAROVI] Aroma terapija - 60 min | Kartica Masaza za parove | `True` |
| [PAROVI] Thai masaža - 90 min | Kartica Masaza za parove | `True` |
| Aroma terapija - 60 min | Obicne masaze | `False` |
| Tradicionalna tajlandska - 90 min | Obicne masaze | `False` |

---

## 🌐 API Endpoints

### 1️⃣ **GET `/api/services`** (Све услуге са филтром)

**Query параметар:** `service_type` (optional)

**Опције:**
- `?service_type=couple` → Враћа само couple услуге (`is_couple=True`)
- `?service_type=single` → Враћа само single услуге (`is_couple=False`)
- Без параметра → Враћа све услуге

**Примери:**
```bash
# Sve usluge
GET /api/services

# Samo couple usluge (za "Masaža za parove" karticu)
GET /api/services?service_type=couple

# Samo single usluge (za pojedinačne masaže)
GET /api/services?service_type=single
```

---

### 2️⃣ **GET `/api/services/couples/list`** (Специјализован за Couple)

**Намена**: Ekskluzivno за websajt "Masaža za parove" картицу

**Враћа**: Само услуге где `is_couple=True` (све [PAROVI] услуге)

**Response**:
```json
[
  {
    "id": "...",
    "name": "[PAROVI] Aroma terapija - 60 min",
    "is_couple": true,
    "category": "Kartica Masaza za parove",
    "price": 7000,
    "final_price": 5950,
    "discount_percentage": 15,
    "service_code": "AROMA_TERAPIJA_60"
  }
]
```

**Број услуга**: 19

---

### 3️⃣ **GET `/api/services/single/list`** (Специјализован за Single)

**Намена**: Ekskluzivno за websajt "Pojedinačne masaže" картице

**Враћа**: Само услуге где `is_couple=False` (све из "Obične masaže")

**Response**:
```json
[
  {
    "id": "...",
    "name": "Aroma terapija - 60 min",
    "is_couple": false,
    "category": "Obicne masaze",
    "price": 3500,
    "final_price": 2975,
    "discount_percentage": 15,
    "service_code": "AROMA_TERAPIJA_60"
  }
]
```

**Број услуга**: 101

---

## 🎯 Препоруке за Websajt

### За "Masaža za parove" Картицу

**Користити ИСКЉУЧИВО:**
```javascript
// Opcija 1: Specijalizovan endpoint (PREPORUČENO)
fetch('/api/services/couples/list')

// Opcija 2: Query parametar
fetch('/api/services?service_type=couple')
```

**НЕ користити:**
- ❌ `/api/services` (без филтра) - враћа и single и couple
- ❌ `/api/services?service_type=single` - враћа само single

---

### За "Pojedinačne Masaže" Картице

**Користити ИСКЉУЧИВО:**
```javascript
// Opcija 1: Specijalizovan endpoint (PREPORUČENO)
fetch('/api/services/single/list')

// Opcija 2: Query parametar
fetch('/api/services?service_type=single')
```

**НЕ користити:**
- ❌ `/api/services` (без филтра) - враћа и single и couple
- ❌ `/api/services?service_type=couple` - враћа само couple

---

## ✅ Провера Раздвајања

### Тест 1: Couple Endpoint
```bash
curl -X GET "https://price-consistency.preview.emergentagent.com/api/services/couples/list"
```

**Очекивано:**
- ✅ Враћа 19 услуга
- ✅ Све услуге имају `is_couple: true`
- ✅ Сви називи почињу са `[PAROVI]`

---

### Тест 2: Single Endpoint
```bash
curl -X GET "https://price-consistency.preview.emergentagent.com/api/services/single/list"
```

**Очекивано:**
- ✅ Враћа 101 услугу
- ✅ Све услуге имају `is_couple: false`
- ✅ Ниједан назив не почиње са `[PAROVI]`

---

### Тест 3: Провера Мешања
```bash
# Couple lista NE SME imati single usluge
curl -X GET "/api/services/couples/list" | grep -i "tradicional"
# Trebalo bi da vrati PRAZNO (0 rezultata)

# Single lista NE SME imati [PAROVI] usluge
curl -X GET "/api/services/single/list" | grep -i "\[PAROVI\]"
# Trebalo bi da vrati PRAZNO (0 rezultata)
```

---

## 🔄 Логика Попуста

**Остаје иста као пре:**
1. Backend користи `service_code` за идентификацију исте масаже
2. Проналази највећи попуст за дати `service_code`
3. Примењује само један попуст (највећи)

**Разлика:**
- Single и couple услуге се **не мешају**
- Websajт добија **одвојене листе**
- Корисник види **тачно оне услуге** које одговарају картици

---

## 📝 Миграциони Скрипт

Фајл: `/app/backend/migrate_is_couple.py`

**Покретање:**
```bash
cd /app/backend
python3 migrate_is_couple.py
```

**Што ради:**
1. Проналази све услуге у категорији "Kartica Masaza za parove"
2. Означава их као `is_couple=True`
3. Све остале означава као `is_couple=False`

---

## 🎉 Резултат

**Пре:**
- ❌ Websajт враћао све услуге, мешао single и couple
- ❌ "Masaža za parove" картица показивала и обичне масаже

**После:**
- ✅ Websajt може да филтрира по типу
- ✅ "Masaža za parove" картица показује САМО [PAROVI] услуге
- ✅ "Pojedinačne masaže" показују САМО single услуге
- ✅ Нема мешања категорија

---

## 📚 Фајлови Измењени

1. `/app/backend/server.py`:
   - Додат `is_couple` field у `ServiceBase` model
   - Ажуриран `GET /api/services` са `service_type` query параметром
   - Креирани нови endpoint-и: `/api/services/couples/list` и `/api/services/single/list`

2. `/app/backend/migrate_is_couple.py`:
   - Нови миграциони скрипт за постављање `is_couple` field-а

3. `/app/SERVICE_SEPARATION_DOCUMENTATION.md`:
   - Овај документ

---

**Датум**: 2025-11-23  
**Верзија**: 1.0  
**Статус**: ✅ Имплементирано и Тестирано
