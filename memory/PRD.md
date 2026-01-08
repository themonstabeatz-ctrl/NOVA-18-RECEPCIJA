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
│   ├── spa_module.py       # SPA booking logic, SPA_CARDS config
│   └── email_templates/    # Email templates
└── frontend/
    └── src/
        ├── pages/
        │   └── DashboardNew.js  # CEO Dashboard
        └── components/
```

## What's Been Implemented

### December 2024
- [x] CORS lockdown - only `spa-booking-site-1` allowed
- [x] Centralized `resolve_pricing_from_appointment` helper
- [x] CEO Dashboard analytics unified for massage + SPA
- [x] Romantic packages pricing fix (22,000 & 19,000 RSD)
- [x] Service name fix in "Appointments with discount" list
- [x] Couples massage endpoints refactored for consistent logic
- [x] Origin debug logging

## Technical Debt (P0 - CRITICAL)
- [ ] **SPA_CARDS in-memory** → Must migrate to MongoDB (discounts lost on restart!)

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
- `PATCH /api/spa/card-discounts` - Set SPA discounts (in-memory!)

## Credentials
- Dashboard password: `studio149`
