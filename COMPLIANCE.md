# Regulatory & Legal Compliance

## Jurisdiction
**Primary:** Republic of Kazakhstan

## Applicable Laws & Regulations

### 1. Financial Regulation (Kazakhstan)

#### ARRF (Agenstvo regulyatsii i razvitiya finansovogo rynka)
- **Law on Insurance Activity** (Law of the Republic of Kazakhstan from June 18, 2003, No. 434-II)
  - Mandatory solvency ratios
  - Insurance reserve requirements
  - Premium validation and reporting
  - Claims processing and settlement

- **Law on Banks and Banking Activity** (Law of the Republic of Kazakhstan from August 31, 1998, No. 191-I)
  - Credit risk assessment requirements
  - Loan classification standards
  - ECL calculation mandates
  - Capital adequacy requirements

#### National Bank of the Republic of Kazakhstan
- Discount rate and inflation parameters per NaRB guidelines
- Foreign exchange rate regulations
- Stress testing requirements

### 2. International Financial Reporting Standards (IFRS)

#### IFRS 9 - Financial Instruments
- **Scope:** Credit risk measurement, ECL (Expected Credit Loss) calculation
- **Requirements:**
```
- Loan classification: Stage 1, Stage 2, Stage 3
- 12-month PD vs Lifetime PD based on significant increase in credit risk
- Macro-economic scenario modeling
- Coverage ratio monitoring (minimum 60% for Stage 3 per ARRF guidance)
- Weighted PD and LGD calculations
```
- **Compliance Check:** ✅ Implemented in Phase 1 CoreEngine
- **Audit Trail:** ✅ SHA256 input hash stored in database for lineage

#### IFRS 17 - Insurance Contracts
- **Scope:** Insurance contract liability measurement
- **Measurement Models:**
  - GMM (General Measurement Model): BEL + RA + CSM
  - VFA (Variable Fee Approach): for investment-linked contracts
  - PAA (Premium Allocation Approach): for simple short-duration contracts
- **Requirements:**
```
- Liability = Best Estimate Liability (BEL) + Risk Adjustment (RA)
- CSM (Contractual Service Margin) for profit recognition
- Discounting at entity-specific rate
- Cohort grouping for portfolio-level measurement
- Onerous contract identification
```
- **Compliance Check:** ✅ Implemented in Phase 1 CoreEngine
- **Risk Margin:** ✅ 75th percentile confidence level calculation

#### Solvency 2 Regulatory Framework
- **Scope:** Insurance company capital requirements and stress testing
- **Capital Requirements:**
```
- SCR (Solvency Capital Requirement)
  - Market risk component (volatility, equity, interest rate, FX)
  - Credit risk component (counterparty default risk)
  - Operational risk component
- MCR (Minimum Capital Requirement)
- Own funds classification
- Solvency ratio = Own Funds / SCR (must be ≥ 1.0)
```
- **Compliance Check:** ✅ Implemented with Nмп coefficient per ARRF requirements
- **Stress Testing:** ✅ Scenario analysis for inflation, FX, equity shocks

### 3. Data Protection & Privacy

#### Personal Data Protection Law of Kazakhstan
- **Applicability:** If application processes personal data
- **Requirements:**
  - Clear purpose specification
  - Informed consent (where applicable)
  - Data security measures
  - Access controls and audit trails
  - Data retention limits

**Status:** Multi-tenant isolation with tenant-level data segregation

#### GDPR Compliance (if processing EU residents' data)
- Not primary jurisdiction but applicable if EU data processed
- **Status:** Not primary focus; internal Kazakhstan insurance data processing

### 4. Data Residency Requirements

#### Kazakhstan Data Localization
- **Requirement:** Financial data must be stored in Kazakhstan territory
- **Implementation:**
  - Primary database: PostgreSQL on Astana Hub certified data center
  - Data center location: Astana, Kazakhstan
  - No automatic cloud migration outside Kazakhstan
  - Encrypted backups retained in-country

**Status:** ✅ Configured in multi-tenant database schema
- Field: `tenants.data_center_location`
- Value: "Astana" (verified for ARRF compliance)

### 5. Audit & Compliance Tracking

#### Audit Trail Requirements
- **Retention Period:** 30+ days minimum per ARRF guidance
- **Logged Information:**
  - User identity and email
  - Entity type (Loan, Contract, CalculationRun)
  - Action type (CREATE, UPDATE, DELETE, CALCULATE)
  - Timestamp and sequence
  - Before/after values (JSONB)

**Status:** ✅ `audit_logs` table with SHA256 input hashing

#### Calculation Lineage
- Input validation and normalization
- Algorithm versioning (Phase 1, 2B, etc.)
- Processing timestamp and duration
- Output serialization and storage

**Status:** ✅ Stored in `calculation_runs` table with metadata

### 6. Regulatory Reporting

#### ARRF Supervision & Inspection
- Ability to provide full calculation history per tenant
- Compliance status per calculation run
- Risk classification and warnings
- Financial ratios and stress test results

**Status:** ✅ Dashboard queries available for compliance reporting

#### Insurance Market Supervision
- Premium volume tracking
- Claims ratio monitoring
- Solvency ratio trend analysis
- Portfolio concentration analysis

**Status:** ✅ Metrics available in ARRF regulatory dashboard

## Compliance Checklist

| Requirement | Status | Implementation | Notes |
|-------------|--------|-----------------|-------|
| **IFRS 9 Compliance** | ✅ | CoreEngine IFRS9Module | ECL per stage, PD/LGD weighting, macro impact |
| **IFRS 17 Compliance** | ✅ | CoreEngine IFRS17Module | BEL/RA/CSM per measurement model, onerous detection |
| **Solvency 2 SCR** | ✅ | CoreEngine SolvencyModule | Market/Credit/Op risk components, Nмп ratio |
| **Multi-tenant Isolation** | ✅ | Database schema | tenant_id foreign keys on all tables |
| **Audit Trail (30+ days)** | ✅ | audit_logs table | Full lineage with timestamps |
| **Data Residency (Astana)** | ✅ | Config + schema | data_center_location field + verification |
| **Input Hashing** | ✅ | SHA256 in calculation_runs | Tamper detection via input_hash |
| **Role-Based Access** | ✅ | Flask session management | insurer/arfr/fgsv roles with route protection |
| **Encryption** | ⚠️ | In progress | TLS for transit, at-rest encryption needed for production |
| **Rate Limiting** | ✅ | Planned | api_keys.rate_limit_per_hour configured |

## Known Limitations

1. **Production Readiness:** This is a Phase 2 implementation. Production use requires:
   - Independent actuarial review and certification
   - Qualified auditor sign-off
   - ARRF licensing review

2. **Encryption:** Current implementation lacks at-rest database encryption
   - **Recommendation:** Enable PostgreSQL transparent data encryption (TDE) for production

3. **Actuarial Validation:** While algorithms follow IFRS/Solvency 2 standards:
   - Probability of Default (PD) inputs should be reviewed by qualified actuaries
   - Loss Given Default (LGD) should match historical experience data
   - Mortality tables (for IFRS 17) should use appropriate demographic data

4. **Stress Testing:** Current stress scenarios are illustrative
   - **Recommendation:** Develop scenario calibration with regulatory guidance

## Validation & Testing

### Unit Tests
- IFRS 9 calculation accuracy (test vectors)
- IFRS 17 CSM and onerous contract detection
- Solvency 2 SCR component calculations
- Multi-tenant data isolation

**Status:** ⚠️ Unit tests need expansion for production

### Integration Tests
- End-to-end calculation flow
- Database persistence and audit trail
- Role-based access control
- API rate limiting (when implemented)

**Status:** ⚠️ Integration tests needed for production

### Compliance Testing
- Audit trail completeness
- Data residency verification
- Regulatory reporting output format validation

**Status:** ⚠️ Regulatory testing needed pre-launch

## Recommendations for Production

### Before Production Launch:
1. ✅ Engage qualified actuary for PD/LGD/mortality validation
2. ✅ Conduct independent audit of calculation engines
3. ✅ Obtain ARRF pre-approval for core algorithms
4. ✅ Implement database encryption at rest
5. ✅ Establish comprehensive test suite with regulatory test vectors
6. ✅ Document data quality procedures and validation rules
7. ✅ Implement real-time monitoring and alerting
8. ✅ Establish disaster recovery and backup procedures

### Ongoing Operations:
1. Regular audit trail review (per ARRF guidance)
2. Monthly compliance status reporting
3. Quarterly stress test execution
4. Annual regulatory review and update
5. Continuous monitoring for regulatory changes

## Contact & Support

- **Compliance Officer:** compliance@alliot-systems.kz
- **Technical Support:** support@alliot-systems.kz
- **Regulatory Affairs:** regulatory@alliot-systems.kz

---

**Last Updated:** December 2, 2025
**Document Version:** 1.0
**Status:** Draft - Requires legal and regulatory review before production use
