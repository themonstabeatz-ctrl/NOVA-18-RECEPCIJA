# 🏗️ Архитектура Система за Попусте v2.0

## 📋 Преглед

Нови систем за управљање попустима користи `service_code` за идентификацију исте масаже преко различитих категорија и аутоматски примењује **највећи доступни попуст** за сваку резервацију.

---

## 🔑 Кључни Концепти

### 1. Service Code
- **Шта је**: Јединствени идентификатор за сваку масажу независно од категорије
- **Формат**: `{NAZIV_MASAZE}_{DURATION}` (нпр. `MASAZA_STOPALA_60`)
- **Генерисање**: Аутоматски генерисано из имена и трајања услуге
- **Пример**:
  ```
  "Masaža stopala - 60 min"        → MASAZA_STOPALA_60
  "[PAROVI] Masaža stopala - 60min" → MASAZA_STOPALA_60
  ```

### 2. Логика Највећег Попуста
```
За дати service_code:
  1. Пронађи све услуге са тим service_code
  2. Издвој discount_percentage за сваку
  3. Одабери MAX(discount_percentage)
  4. Примени тај попуст на оригиналну цену
```

### 3. Price Snapshotting
- Приликом креирања резервације, систем "замрзне" цену, оригиналну цену и попуст
- Ово осигурава да промене попуста не утичу на постојеће резервације
- Сачувани подаци:
  - `snapshot_price`: Финална цена (са попустом)
  - `snapshot_original_price`: Оригинална цена (без попуста)
  - `snapshot_discount_percentage`: Примењени попуст

---

## 🗄️ База Података

### Services Collection
```json
{
  "id": "uuid",
  "name": "Masaža stopala - 60 min",
  "service_code": "MASAZA_STOPALA_60",  // ← NOVO!
  "duration": 60,
  "price": 3150.0,
  "discount_percentage": 15.0,
  "metadata": {
    "original_price": 3150.0
  },
  "category": "Obicne masaze"
}
```

### Appointments Collection
```json
{
  "id": "uuid",
  "service_id": "...",
  "snapshot_price": 2677.5,              // ← Цена са попустом
  "snapshot_original_price": 3150.0,     // ← Оригинална цена
  "snapshot_discount_percentage": 15.0,  // ← Примењени попуст
  // ... остала поља
}
```

---

## 🔧 Backend Имплементација

### Helper Функције

#### 1. `generate_service_code(name: str, duration: int) -> str`
Генерише `service_code` из имена и трајања услуге.

```python
generate_service_code("Aroma terapija - 60 min", 60)
# Враћа: "AROMA_TERAPIJA_60"

generate_service_code("[PAROVI] Aroma terapija - 60 min", 60)
# Враћа: "AROMA_TERAPIJA_60"  (исти код!)
```

#### 2. `get_best_discount_for_service_code(service_code: str) -> dict`
Проналази највећи попуст за дати `service_code`.

```python
await get_best_discount_for_service_code("MASAZA_STOPALA_60")
# Враћа:
{
  "best_discount_percentage": 15.0,
  "original_price": 3150.0,
  "service_id": "ad1f5ce1-..."
}
```

#### 3. `calculate_discounted_price(service_code: str, base_price: float) -> dict`
Израчунава финалну цену са најбољим попустом.

```python
await calculate_discounted_price("MASAZA_STOPALA_60", 3150.0)
# Враћа:
{
  "final_price": 2677.5,
  "discount_percentage": 15.0,
  "original_price": 3150.0
}
```

---

## 🛣️ API Endpoints

### 1. `GET /api/services`
**Враћа**: Листу свих услуга са **обогаћеним** подацима

```json
{
  "id": "...",
  "name": "Masaža stopala - 60 min",
  "service_code": "MASAZA_STOPALA_60",
  "price": 3150.0,
  "discount_percentage": 15.0,        // ← Највећи попуст
  "final_price": 2677.5,              // ← Аутоматски израчунато
  "metadata": {
    "original_price": 3150.0
  }
}
```

**Логика**:
- За сваку услугу, проналази највећи попуст користећи `service_code`
- Аутоматски израчунава `final_price`

### 2. `POST /api/appointments`
**Креира**: Нову резервацију са snapshot ценом

**Request**:
```json
{
  "service_id": "51ed3e01-...",
  "client_first_name": "Marko",
  // ... остали подаци
}
```

**Логика**:
1. Проналази услугу по `service_id`
2. Добија `service_code` за ту услугу
3. Проналази **највећи попуст** за тај `service_code`
4. Чува snapshot са тим попустом

**Response**:
```json
{
  "id": "...",
  "service_id": "51ed3e01-...",
  "snapshot_price": 2677.5,
  "snapshot_original_price": 3150.0,
  "snapshot_discount_percentage": 15.0
}
```

### 3. `POST /api/book-couple-appointment`
**Креира**: Couple резервацију са најбољим попустом

**Request**:
```json
{
  "person1_services": ["service-id-1"],
  "person2_services": ["service-id-2"],
  "discount_couples_massage": 0  // Opciono, backend pronalazi najbolji
}
```

**Логика**:
1. За сваку услугу (person1 и person2), проналази `service_code`
2. За сваки `service_code`, проналази највећи попуст
3. Сакупља све попусте у листу: `[discount1, discount2, couple_discount]`
4. Бира **MAX** из листе
5. Примењује само тај један попуст на укупну цену

**Пример**:
```
Person 1: Aroma 90min → service_code=AROMA_TERAPIJA_90 → best_discount=10%
Person 2: Stopala 60min → service_code=MASAZA_STOPALA_60 → best_discount=15%
Couple discount (from request): 0%

all_discounts = [10%, 15%, 0%]
APPLYING_BEST = MAX(all_discounts) = 15%

original_price = 5600 + 3150 = 8750 RSD
final_price = 8750 * (1 - 0.15) = 7437.5 RSD
```

---

## 📊 Примери Тестирања

### Тест 1: Single Appointment са Највећим Попустом
```bash
# Креирај appointment за "Masaža stopala 60min" (користећи ID обичне са 5%)
# Систем треба да примени 15% (највећи доступан)

Expected:
- snapshot_original_price: 3150
- snapshot_discount_percentage: 15
- snapshot_price: 2677.5
```

### Тест 2: Couple Appointment са Различитим Попустима
```bash
# Person 1: Aroma 90 (10% discount)
# Person 2: Stopala 60 (15% discount)
# Couple discount: 0%

Expected:
- snapshot_discount_percentage: 15 (highest)
- snapshot_price: total * 0.85
```

### Тест 3: Провера да се Попусти НЕ Дуплирају
```bash
# Старо понашање (погрешно):
# final = price * (1 - 0.10) * (1 - 0.15) = 76.5% од оригиналне

# Ново понашање (исправно):
# final = price * (1 - 0.15) = 85% од оригиналне
```

---

## 🎯 Предности Новог Система

### ✅ Једноставност
- Један попуст по резервацији
- Нема множења попуста
- Backend је једини извор истине

### ✅ Конзистентност
- Иста масажа има исти попуст у свим категоријама
- Увек се бира највећи доступан попуст
- Нема конфузије око категорија

### ✅ Историјска Тачност
- Snapshot-овање чува тачне податке
- Промене попуста не утичу на прошле резервације
- Аналитика увек показује тачне податке

### ✅ Лака Интеграција са Websajтом
- Websajт само приказује податке
- Не мора да познаје логику попуста
- Нема ризика од грешака у израчунавању

---

## 🔍 Debugging

### Провера service_code за Услугу
```bash
mongosh test_database --eval "db.services.find({name: /stopala/i}, {name: 1, service_code: 1, discount_percentage: 1, _id: 0})"
```

### Провера Snapshot Података у Appointment
```bash
mongosh test_database --eval "db.appointments.find({id: 'appointment-id'}, {snapshot_price: 1, snapshot_original_price: 1, snapshot_discount_percentage: 1, _id: 0})"
```

### Backend Логови за Couple Booking
```bash
tail -f /var/log/supervisor/backend.err.log | grep "💰 Price Calculation"
```

---

## 📝 Закључак

Нови систем решава све проблеме са дуплим попустима и обезбеђује конзистентно, предвидиво понашање. Backend је једини који управља логиком попуста, што смањује ризик од грешака и олакшава одржавање система.

**Датум имплементације**: 2025-01-16
**Верзија**: 2.0
**Статус**: ✅ Имплементирано и тестирано
