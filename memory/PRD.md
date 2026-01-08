# SPA Booking System - PRD

## Current URLs (Source of Truth)
- **Backend**: https://price-analyzer-8.preview.emergentagent.com
- **Frontend (Public)**: https://spa-booking-site-1.preview.emergentagent.com
- **Frontend (Admin)**: http://localhost:3000

## Verified Prices - Romantični Paketi (E2E Tested Jan 8, 2026)
| Package | Duration | Price (RSD) |
|---------|----------|-------------|
| Romantični paket za parove | 210 min | 22,000 |
| Romantični piling paket za parove | 210 min | 19,000 |

**Note: 25,000 RSD phantom price has been completely eliminated!**

## What's Been Implemented

### January 8, 2026
- [x] CORS lockdown - only `spa-booking-site-1` allowed
- [x] **Duration fix in DB**: 180/150 → 210 min for romantic packages
- [x] **Price fix in SPECIAL_PACKAGES**: 25,000 → 22,000/19,000 RSD
- [x] **SPA_CARDS config**: Added `base_price` and `duration_min`
- [x] Added `resolve_spa_display_name` helper
- [x] Added `card_id` and `card_title` storage in SPA appointments
- [x] E2E verification completed with 7 documented proofs

## E2E Test Results (Jan 8, 2026)
All tests passed:
1. ✅ Public frontend shows correct prices (22,000/19,000 with discounts)
2. ✅ Booking modal shows 210 min duration, 22,000 RSD original
3. ✅ CEO Dashboard "Termini Sa Popustom" displays correctly
4. ✅ Admin Usluge shows 210 min, correct prices
5. ✅ Backend logs show correct pricing calculations
6. ✅ Email sent to grujovicsavatije@gmail.com
7. ✅ MongoDB document has correct pricing snapshot

## Technical Debt (P0 - CRITICAL)
- [ ] **SPA_CARDS in-memory** → Must migrate to MongoDB (discounts lost on restart!)

## Architecture
```
/app/backend/
├── server.py          # Main FastAPI, CORS, analytics
│                      # Functions: resolve_pricing_from_appointment, resolve_spa_display_name
├── spa_module.py      # SPA booking logic
│                      # Config: SPA_CARDS (in-memory!), SPECIAL_PACKAGES
└── email_templates/
```

## Key Endpoints
- `GET /api/spa/services` - All SPA services (from DB)
- `POST /api/spa/quote` - Calculate quote with discount
- `POST /api/spa/appointments` - Create booking
- `PATCH /api/spa/cards/{card_id}/discount?discount=X` - Set discount (in-memory!)
- `GET /api/analytics/detailed` - CEO Dashboard data

## Credentials
- Dashboard password: `studio149`
- Test email: `grujovicsavatije@gmail.com`

## Backlog
- [ ] Migrate SPA_CARDS to MongoDB
- [ ] E2E testing of complete booking flow
- [ ] POS/terminal integration
- [ ] Reviews system
- [ ] Loyalty program
