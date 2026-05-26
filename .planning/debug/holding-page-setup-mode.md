# Debug: Holding page vs setup mode

**UAT Test:** 8  
**Symptom:** Without admin env defined, non-admin sees populated browse instead of holding page.

## Root Cause

Test conflated `setup_mode` (admin env unset) with `libraries_scoped=false`. Libraries were scoped in prior UAT steps; D-04 allows browse when scoped even in setup mode.

## Fix Direction

Re-test with zero scoped libraries. Optional setup_mode banner for clarity.
