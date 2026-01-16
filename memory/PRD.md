# SPA Booking System - PRD

## Current URLs (Source of Truth)
- **Backend**: https://multilingfix.preview.emergentagent.com
- **Frontend (Public)**: https://spabook-upgrade.preview.emergentagent.com
- **Frontend (Admin)**: https://multilingfix.preview.emergentagent.com

## Verified Prices - Romantični Paketi (E2E Tested Jan 8, 2026)
| Package | Duration | Price (RSD) |
|---------|----------|-------------|
| Romantični paket za parove | 210 min | 22,000 |
| Romantični piling paket za parove | 210 min | 19,000 |

**Note: 25,000 RSD phantom price has been completely eliminated!**

## What's Been Implemented

### January 16, 2026 - VIŠEJEZIČNI EMAIL POZDRAVI
- [x] **Email greeting lokalizacija** - Pozdrav u emailu se sada prevodi prema `lang` parametru rezervacije
- [x] **Normalizacija jezika** - "en-US" → "en", "ru_RU" → "ru", prazno → "sr"
- [x] **Podržani jezici**:
  - `sr`: "Poštovani/a {ime},"
  - `en`: "Dear {ime},"
  - `ru`: "Уважаемый/ая {ime},"
  - `th`: "เรียนคุณ {ime},"
- [x] **SPA model update** - Dodato `lang` polje u `SpaAppointmentCreate` i `SpaAppointment`
- [x] **Adapters update** - `build_client_email_for_massage` i `build_client_email_for_couples` sada prosleđuju `lang` u `ClientEmailModel`
- [x] **CORS update** - Dodat `spabook-upgrade.preview.emergentagent.com` u allowed origins

### January 8, 2026
- [x] CORS lockdown - only allowed origins
- [x] **Duration fix in DB**: 180/150 → 210 min for romantic packages
- [x] **Price fix in SPECIAL_PACKAGES**: 25,000 → 22,000/19,000 RSD
- [x] **SPA_CARDS config**: Added `base_price` and `duration_min`
- [x] Added `resolve_spa_display_name` helper
- [x] Added `card_id` and `card_title` storage in SPA appointments
- [x] E2E verification completed with 7 documented proofs

## Technical Debt (P0 - CRITICAL)
- [ ] **SPA_CARDS in-memory** → Must migrate to MongoDB (discounts lost on restart!)

## Architecture
```
/app/backend/
├── server.py              # Main FastAPI, CORS, analytics
│                          # Functions: resolve_pricing_from_appointment, resolve_spa_display_name
├── spa_module.py          # SPA booking logic
│                          # Config: SPA_CARDS (in-memory!), SPECIAL_PACKAGES
│                          # NEW: normalize_lang() helper, lang field in models
└── email_templates/
    ├── client_shared.py   # GREETINGS dict, get_greeting(), normalize_lang()
    └── adapters.py        # build_client_email_for_spa/massage/couples - all pass lang
```

## Key Endpoints
- `POST /api/appointments` - Massage booking (supports `lang`)
- `POST /api/spa/appointments` - SPA booking (supports `lang`)
- `GET /api/analytics/detailed` - CEO Dashboard data
- `PUT /api/appointments/{id}` - Update appointment

## Email Localization Flow
```
1. Frontend sends: { "lang": "en" } in booking request
2. Backend normalizes: normalize_lang("en-US") → "en"
3. Saves to DB: doc['lang'] = "en"
4. Email adapter: build_client_email_for_spa({ lang: "en" })
5. ClientEmailModel: lang="en"
6. render_client_shared: get_greeting(name, "en") → "Dear {name},"
```

## Backlog / Future Tasks
1. **P0**: Migrate SPA_CARDS to MongoDB (prevents discount reset on server restart)
2. E2E testing of complete booking flow
3. POS/kasa integration
4. Reviews system
5. Loyalty program
