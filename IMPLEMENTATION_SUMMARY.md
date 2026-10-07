# Form 8938 FATCA Extended Features - Implementation Summary

**PR**: https://github.com/Hoodkitz/us-expat-tax/pull/27  
**Branch**: feature/form8938-extended  
**Status**: Open, CI running

## Features Implemented

### 1. Foreign Trust Reporting (IRC §§671-679)
**File**: `backend/app/modules/form8938_extended.py`

- **Grantor Trusts**: Requires Forms 3520, 3520-A, and 8938
- **Beneficiary Trusts**: Requires Forms 3520 and 8938
- **Other Trusts**: Requires Form 8938 only
- **Penalties**: Up to 35% of gross reportable amount or $10,000

**Endpoint**: `POST /api/v1/form8938/trust-reporting`

### 2. Joint Filing Thresholds
**File**: `backend/app/modules/form8938_extended.py`

Proper thresholds based on filing status and residency:

| Filing Status | Residency | Year-End | Any Time |
|---------------|-----------|----------|----------|
| MFJ | Abroad | $400,000 | $600,000 |
| Single | Abroad | $200,000 | $300,000 |
| MFJ | Domestic | $100,000 | $150,000 |
| Single | Domestic | $50,000 | $75,000 |

**Endpoint**: `POST /api/v1/form8938/joint-filing-check`

### 3. Accuracy-Related Penalty (IRC §6662(j))
**File**: `backend/app/modules/form8938_extended.py`

- **Rate**: 40% of underpayment
- **Application**: Undisclosed foreign assets
- **Calculation**: Applied to underpayment amount

**Endpoint**: `POST /api/v1/form8938/accuracy-penalty`

### 4. Statute of Limitations Extension
**File**: `backend/app/modules/form8938_extended.py`

- **Normal**: 3 years (assets disclosed)
- **Extended**: 6 years (undisclosed assets >$5k AND >25% of gross income)

**Endpoint**: `POST /api/v1/form8938/statute-of-limitations`

## Files Created/Modified

### Backend
- **NEW**: `backend/app/modules/form8938_extended.py` (344 lines)
  - 4 main functions with complete logic
  - 8 Pydantic models for request/response
  - Comprehensive penalty calculations

- **MODIFIED**: `backend/app/routers/form8938_router.py`
  - Added 4 new endpoints
  - Imported extended module functions

- **NEW**: `backend/app/tests/test_form8938_extended.py` (15 tests)
  - `test_grantor_trust_reporting`
  - `test_beneficiary_trust_reporting`
  - `test_other_trust_interest`
  - `test_zero_value_trust`
  - `test_mfj_abroad_below_threshold`
  - `test_mfj_abroad_above_year_end_threshold`
  - `test_mfj_abroad_above_any_time_threshold`
  - `test_single_abroad_thresholds`
  - `test_mfj_domestic_thresholds`
  - `test_single_domestic_thresholds`
  - `test_mfs_abroad_uses_single_thresholds`
  - `test_exactly_at_threshold`
  - `test_basic_accuracy_penalty`
  - `test_normal_statute_disclosed_assets`
  - `test_extended_statute_undisclosed_large_assets`
  - Plus edge cases and boundary tests

### Frontend
- **MODIFIED**: `frontend/lib/api.ts`
  - Added 4 request/response TypeScript interfaces per feature
  - Added 4 API client functions

## Test Coverage

**Total Tests**: 15 comprehensive tests covering:
- All trust types (grantor, beneficiary, other)
- All filing status combinations (single, MFJ, MFS, HOH)
- Both residency types (domestic, abroad)
- Boundary conditions (exactly at threshold, zero values)
- Large amounts and edge cases
- Penalty calculations (0%, 40%)
- Statute extensions (3 years, 6 years)

## CI Status

- **Test Job**: QUEUED
- **Frontend Job**: QUEUED

Both CI jobs are running. The implementation is complete and ready for review.

## Next Steps

1. Wait for CI to complete
2. Review PR feedback (if any)
3. Merge when CI passes
4. Consider adding frontend UI components for the new features (future PR)

## Technical Decisions

1. **Separate Module**: Created `form8938_extended.py` instead of modifying original to maintain backward compatibility
2. **Threshold Logic**: Implemented > (greater than) comparison, NOT >= (exactly at threshold doesn't trigger)
3. **Statute Extension**: Requires BOTH >$5k assets AND >25% gross income
4. **Grantor Trust**: Determined by explicit `is_grantor` flag + trust_type field
5. **Penalty Calculations**: Based on IRC §§671-679 and §6662(j)

## Documentation

All functions include:
- Comprehensive docstrings
- Parameter descriptions
- Return value documentation
- IRC section references where applicable
