# new admin customer flow finalization plan

## 1. Goal

Finalize the customer-flow surface for project `9 new admin` so that:

- current working implementation is explicitly owned
- disconnected-customer handling is operationally clear
- refresh steps are canonical and repeatable
- authority can be normalized into `ivwith/admin_new_runtime` without logic drift

## 2. Current Reality

- Current working customer portal: `C:\1POW\projects\ivwith\new_admin\customer_portal.php`
- Current working customer portal API: `C:\1POW\projects\ivwith\new_admin\customer_portal_api.php`
- Current deep flow dashboard: `C:\1POW\projects\ivwith\customer_flow_dashboard.html`
- Current analytics engine:
  - `analyze_customer_flows.py`
  - `build_customer_portal_db.py`
  - `build_customer_flow_dashboard.py`
- Current shared DB: `C:\1POW\projects\ivwith\customer_portal.sqlite`

This means project `9` owns the finalization target, but the live customer-flow implementation still sits in project `4 ivwith legacy`.

## 3. Flow Definitions

### New flow

- main tab: `new`
- portal status pipeline:
  - `신규접수`
  - `가승인`
  - `승인후부재`
  - `자서예정`
  - `자서완료`
  - `기표예정`
  - `기표전부재`
  - `기표완료`
  - `지속관리 2주+`
- re-entry is already computed in the flow engine and must stay visible in the new pipeline

### Renewal flow

- main tab: `renewal`
- segments:
  - `연장유지`
  - `단절`
  - `완전이탈`
  - `지속관리 2주+`

### Disconnected customers

- `단절고객`
  - apartment contract maturity passed
  - no follow-up extension within the gap rule
  - still operationally recoverable in some cases
- `완전이탈`
  - previous chain ended externally
  - no current internal managed continuation
- operationally, `승인후부재` / `기표전부재` are recovery queues, not the same as confirmed churn

## 4. Main Gaps

1. Ownership gap
- project `9` docs say it owns the target
- actual working code is still in `projects/ivwith/new_admin`

2. Refresh gap
- `daily_sync.py` refreshes CRM DB only
- customer-flow outputs are not rebuilt automatically after sync

3. Surface gap
- customer portal and deep flow dashboard are still split
- the portal is summary-first, while deep flow drill-down stays separate

4. Status drift risk
- `customer_status`, `portal_status`, strategy labels, and churn queues are not fully unified in one operational document

## 5. Immediate Work Completed In This Pass

- re-audited actual working files
- documented real ownership and boundary
- created canonical refresh entrypoint: `refresh_customer_flow_assets.py`
- aligned `new admin` handover with the real customer-flow implementation

## 6. Next Execution Phases

### Phase A. Ownership freeze

- keep current working implementation in `projects/ivwith/new_admin`
- treat it as the temporary canonical customer-flow surface
- make project `9 new admin` the owner in docs and migration plan

### Phase B. Refresh stabilization

- use `refresh_customer_flow_assets.py` as canonical local refresh entrypoint
- keep `REFRESH_CUSTOMER_PORTAL.bat` as Windows wrapper
- decide later whether to append this refresh after `daily_sync.py`

### Phase C. Disconnected-customer operations

- separate three concepts in operator language:
  - confirmed churn
  - full exit
  - recovery candidates (`승인후부재`, `기표전부재`)
- keep churn metrics in renewal tab
- keep recovery queues in execution/management queues

### Phase D. Final authority normalization for project 9

- keep the customer-flow surface under `ivwith/admin_new_runtime`
- do not create a new top-level `ivwith-admin-new` worktree for active code
- treat `quarantine/legacy_app_copies/2026-04-10/root_ivwith-admin-new_copy/legacy-php` as the archived legacy snapshot mirror only

## 7. Success Criteria

- project `9` docs no longer pretend the customer-flow tab is already migrated
- operators know where `new`, `renewal`, `churn`, `full exit` are computed
- one canonical refresh command exists
- disconnected-customer handling is explicitly planned, not implicit
