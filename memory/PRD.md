# SPA Booking System - PRD

## Original Problem Statement
Full-featured SPA booking system with massage services, couples packages, SPA treatments, discounts, and CEO analytics dashboard.

## Current URLs (Source of Truth)
- **Backend**: https://price-analyzer-8.preview.emergentagent.com
- **Frontend**: https://spa-booking-site-1.preview.emergentagent.com

## Core Requirements
1. Booking system for massages (single & couples)
2. SPA treatments with various packages
3. Discount management system
4. CEO Analytics Dashboard
5. Email notifications

## Architecture
```
/app/
├── backend/
│   ├── server.py           # Main FastAPI, CORS, analytics, massage booking
│   │                       # Contains: resolve_pricing_from_appointment, resolve_spa_display_name
│   ├── spa_module.py       # SPA booking logic, SPA_CARDS config, SPECIAL_PACKAGES
│   └── email_templates/    # Email templates
└── frontend/
    └── src/
        ├── pages/
        │   └── DashboardNew.js  # CEO Dashboard
        └── components/
```

## What's Been Implemented

### January 8, 2026
- [x] CORS lockdown - only `spa-booking-site-1` allowed
- [x] **Fix "USLUGA" column** - shows actual service names instead of generic "SPA Tretman"
- [x] **Romantic packages pricing fix** - 22,000 RSD and 19,000 RSD (removed 25,000 phantom price)
- [x] Added `resolve_spa_display_name` helper for proper service name resolution
- [x] Added `card_id` and `card_title` storage in SPA appointments

### Previous Work
- [x] Centralized `resolve_pricing_from_appointment` helper
- [x] CEO Dashboard analytics unified for massage + SPA
- [x] Couples massage endpoints refactored for consistent logic
- [x] Origin debug logging

## Technical Debt (P0 - CRITICAL)
- [ ] **SPA_CARDS in-memory** → Must migrate to MongoDB (discounts lost on restart!)

## Verified Prices (Source of Truth)
| Package | Price (RSD) |
|---------|-------------|
| Romantični paket za parove | 22,000 |
| Romantični piling paket za parove | 19,000 |
| Silky Body Ritual | 9,200 |
| Gentle Touch Ritual | 10,400 |
| Deep Renewal Ritual | 11,600 |

## Backlog
- [ ] E2E testing of complete booking flow
- [ ] POS/terminal integration
- [ ] Reviews system
- [ ] Loyalty program

## Key Endpoints
- `GET /api/health` - Health check
- `GET /api/services` - All services with pricing
- `GET /api/spa/cards` - SPA card configurations
- `POST /api/spa/appointments` - Create SPA booking
- `GET /api/analytics/detailed` - CEO Dashboard data
- `PATCH /api/spa/cards/{card_id}/discount?discount=X` - Set SPA discounts (in-memory!)

## Key Functions
- `resolve_pricing_from_appointment(appt)` - Single source of truth for pricing
- `resolve_spa_display_name(appt)` - Resolves proper service name for display

## Credentials
- Dashboard password: `studio149`
- Test email: `grujovicsavatije@gmail.com`
