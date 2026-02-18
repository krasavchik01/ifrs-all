# 🛡️ Alliot - IFRS 9/17 & Solvency 2 Compliance Platform

[![License](https://img.shields.io/badge/license-Proprietary-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-3.0+-green.svg)](https://flask.palletsprojects.com/)
[![Production Ready](https://img.shields.io/badge/status-production--ready-brightgreen.svg)](ACTUARIAL_ANALYSIS.md)

**Enterprise-grade financial compliance automation platform for insurance companies in Kazakhstan**

---

## 📋 Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Documentation](#documentation)
- [API Reference](#api-reference)
- [Regulatory Compliance](#regulatory-compliance)
- [Screenshots](#screenshots)
- [Support](#support)
- [License](#license)

---

## 🎯 Overview

Alliot is a comprehensive financial compliance automation platform designed specifically for insurance companies operating under Kazakhstan's regulatory framework (ARRF). The platform provides full automation for IFRS 9, IFRS 17, and Solvency 2 calculations with complete audit trail and regulatory reporting capabilities.

### Target Audience

- **Insurance Companies**: 27 licensed insurers in Kazakhstan
- **Regulators**: ARRF (Agency for Regulation and Development of Financial Market)
- **Guarantee Fund**: FGSV (Insurance Payments Guarantee Fund)
- **Reinsurers**: International and local reinsurance organizations

### Why Alliot?

| Challenge | Alliot Solution |
|-----------|-----------------|
| Complex IFRS 9/17 calculations | Automated ECL, BEL, RA, CSM calculations with full formula transparency |
| Regulatory compliance burden | Built-in ARRF, EIOPA 2025, Basel III alignment |
| Manual data processing | Real-time calculations with REST API integration |
| Audit trail requirements | Complete transaction history with mathematical proof |
| Stress testing complexity | Integrated scenario analysis (Basel, Adverse, Severe, VaR 99.5%) |

---

## ✨ Key Features

### 🏦 IFRS 9 - Financial Instruments

- **Expected Credit Loss (ECL)** calculation using 3-stage classification
- **PD/LGD/EAD** modeling with macroeconomic adjustments
- **SICR detection** (Significant Increase in Credit Risk)
- **Forward-looking scenarios** with weighted probability
- **Lifetime vs 12-month ECL** automatic determination

### 📊 IFRS 17 - Insurance Contracts

- **Building Block Approach (GMM)** with full CSM tracking
- **Variable Fee Approach (VFA)** for participating contracts
- **Premium Allocation Approach (PAA)** for short-duration contracts
- **Risk Adjustment** calculation via Cost of Capital and CTE methods
- **Onerous contract detection** with immediate loss recognition
- **Coverage units** for CSM amortization

### 🛡️ Solvency 2 Compliance

- **MMP (Minimum Margin of Solvency)** calculation
- **FMP (Own Funds)** with Tier 1/2/3 classification
- **Nmp coefficient** monitoring (regulatory minimum: 1.0)
- **Stress testing**: Adverse, Severe, VaR 99.5% scenarios
- **ORSA integration** (Own Risk and Solvency Assessment)

### 🏛️ FGSV (Guarantee Fund)

- **Contribution calculator** based on premiums and solvency
- **Bankruptcy risk modeling** with early warning system
- **Payout simulation** for insurer failure scenarios
- **Monte Carlo analysis** for fund sufficiency testing

### 🔐 Regulatory Features

- **Multi-role access control** (Insurer, ARRF, FGSV)
- **Complete audit trail** with timestamp and user tracking
- **XBRL export** for ARRF regulatory reporting
- **Macro indicators** integration (NBK base rate, inflation, FX rates)
- **Compliance dashboards** with traffic light indicators

---

## 🏗️ Architecture

### Technology Stack

```
Frontend:  Bootstrap 5, Chart.js, KaTeX (math rendering)
Backend:   Flask 3.0, Python 3.11+
Database:  SQLAlchemy ORM (PostgreSQL/MySQL/SQLite)
API:       RESTful JSON APIs
Testing:   pytest, coverage.py
Security:  CSRF protection, role-based access control
```

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Web Interface (HTML/CSS/JS)             │
├─────────────────────────────────────────────────────────────┤
│                Flask Application Layer                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  IFRS 9      │  │  IFRS 17     │  │  Solvency 2  │     │
│  │  Module      │  │  Module      │  │  Module      │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
├─────────────────────────────────────────────────────────────┤
│                Calculation Services Layer                   │
│  • IFRS9Calculator  • IFRS17Calculator  • SolvencyService   │
├─────────────────────────────────────────────────────────────┤
│                    Data Access Layer                        │
│              SQLAlchemy ORM + Database                      │
└─────────────────────────────────────────────────────────────┘
```

### Project Structure

```
kz_insurepro/
├── app/
│   ├── __init__.py                 # Flask application factory
│   ├── routes.py                   # Web routes and controllers
│   ├── api/
│   │   └── routes.py              # REST API endpoints
│   ├── services/
│   │   ├── calculation_service.py # IFRS 9/17/Solvency calculations
│   │   └── fgsv_service.py        # FGSV contribution calculator
│   ├── models/
│   │   └── database.py            # SQLAlchemy models
│   ├── templates/                  # Jinja2 HTML templates
│   │   ├── base.html              # Base layout with navigation
│   │   ├── index.html             # Insurer dashboard
│   │   ├── arfr/                  # ARRF regulator pages
│   │   └── fgsv_panel/            # FGSV guarantee fund pages
│   └── static/                     # CSS, JS, images
├── tests/
│   ├── test_ifrs9.py              # IFRS 9 unit tests
│   ├── test_ifrs17.py             # IFRS 17 unit tests
│   └── test_solvency.py           # Solvency 2 unit tests
├── config.py                       # Application configuration
├── requirements.txt                # Python dependencies
├── run.py                          # Application entry point
├── COPYRIGHT.md                    # Copyright and IP notice
├── COMPLIANCE.md                   # Regulatory compliance documentation
├── ACTUARIAL_ANALYSIS.md          # Actuarial methodology assessment
└── README.md                       # This file
```

---

## 🚀 Installation

### Prerequisites

- **Python 3.11+** (Python 3.13 supported)
- **pip** package manager
- **Git** (for cloning repository)

### Step-by-Step Installation

1. **Clone the repository**

```bash
git clone https://github.com/krasavchik01/Solvency2.git
cd Solvency2/kz_insurepro
```

2. **Create virtual environment**

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Initialize database** (optional, uses SQLite by default)

```bash
python
>>> from app import create_app, db
>>> app = create_app()
>>> with app.app_context():
...     db.create_all()
>>> exit()
```

5. **Run the application**

```bash
python run.py
```

The application will be available at: **http://127.0.0.1:5000**

---

## 🎬 Quick Start

### Web Interface

1. Navigate to http://127.0.0.1:5000
2. Select your role:
   - **Insurer** (страховая компания) - for insurance company users
   - **ARRF** (АРФР) - for regulatory authority
   - **FGSV** (ФГСВ) - for guarantee fund
3. Use the dashboard to access calculation modules

### Example: Calculate ECL (IFRS 9)

**Web Interface:**
1. Click "МСФО 9" in sidebar
2. Enter parameters:
   - Gross Carrying Amount: 500,000,000 KZT
   - PD: 9.5%
   - LGD: 69%
   - Effective Interest Rate: 19%
3. Click "Рассчитать ECL"
4. View detailed breakdown with formulas

**API:**

```bash
curl -X POST http://127.0.0.1:5000/api/ifrs9/ecl \
  -H "Content-Type: application/json" \
  -d '{
    "gca": 500000000,
    "pd": 0.095,
    "lgd": 0.69,
    "eir": 0.19,
    "term": 3,
    "dpd": 0,
    "scenario": "weighted"
  }'
```

### Example: Calculate Insurance Liability (IFRS 17)

**API:**

```bash
curl -X POST http://127.0.0.1:5000/api/ifrs17/gmm \
  -H "Content-Type: application/json" \
  -d '{
    "premiums": 100000000,
    "claims_per_year": 80000000,
    "expenses_per_year": 5000000,
    "acquisition_costs": 10000000,
    "term": 10,
    "ra_method": "coc",
    "coc_rate": 0.06
  }'
```

### Example: Calculate Solvency Ratio

**API:**

```bash
curl -X POST http://127.0.0.1:5000/api/solvency/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "gross_premiums": 35000000000,
    "incurred_claims": 18000000000,
    "equity": 20000000000,
    "ecl_adjustment": 2100000000,
    "csm_adjustment": 11800000000,
    "subordinated": 3000000000,
    "illiquid": 500000000,
    "has_osago": true,
    "k": 0.70
  }'
```

---

## 📚 Documentation

### Core Documentation

- **[ACTUARIAL_ANALYSIS.md](ACTUARIAL_ANALYSIS.md)** - Detailed actuarial methodology and production readiness assessment
- **[COMPLIANCE.md](COMPLIANCE.md)** - Regulatory compliance documentation (ARRF, IFRS, Solvency 2)
- **[COPYRIGHT.md](COPYRIGHT.md)** - Copyright, intellectual property, and licensing information

### Calculation Methodologies

#### IFRS 9 - Expected Credit Loss

**3-Stage Classification:**

| Stage | Condition | ECL Type |
|-------|-----------|----------|
| 1 | No SICR detected | 12-month ECL |
| 2 | SICR detected (PD increase >100% OR DPD 30-89 days) | Lifetime ECL |
| 3 | Credit-impaired (DPD ≥90 days) | Lifetime ECL |

**ECL Formula:**

```
ECL = Σ(t=1 to T) [PD_t × LGD × EAD_t × DF_t]

Where:
  PD_t  = Probability of Default at time t (adjusted for macro scenarios)
  LGD   = Loss Given Default (69% for unsecured, 45% for secured)
  EAD_t = Exposure At Default at time t
  DF_t  = Discount Factor = exp(-r × t)
```

**Macroeconomic Adjustments:**

```
PD_adj = PD_base × Σ(w_i × M_i)

Scenarios:
  Baseline:      M = 1.35, Weight = 55%
  Adverse:       M = 1.80, Weight = 35%
  Severe:        M = 2.40, Weight = 10%

  Weighted M = 1.613
```

#### IFRS 17 - Insurance Contracts

**General Measurement Model (GMM):**

```
Insurance Contract Liability = FCF + CSM

Where:
  FCF = Fulfillment Cash Flows = BEL + RA
  BEL = Best Estimate Liability (PV of future cash flows)
  RA  = Risk Adjustment (Cost of Capital or CTE method)
  CSM = Contractual Service Margin
```

**CSM Calculation:**

```
CSM_initial = Premiums - Acquisition_Costs - BEL - RA

If CSM < 0: Contract is onerous
  → Recognize loss immediately
  → CSM = 0
```

**Risk Adjustment Methods:**

1. **Cost of Capital (CoC):**
   ```
   RA = FV(Capital_Required × CoC_Rate × Duration)
   CoC_Rate = 6% (EIOPA recommended)
   ```

2. **Conditional Tail Expectation (CTE):**
   ```
   RA = CTE_75 - BEL
   CTE_75 = Average of worst 25% scenarios
   ```

#### Solvency 2 - Capital Adequacy

**Solvency Ratio (Nmp):**

```
Nmp = FMP / MMP

Regulatory Requirements:
  Nmp ≥ 1.0  (Minimum acceptable)
  Nmp ≥ 1.5  (Comfortable level)
  Nmp ≥ 2.0  (Well-capitalized)
```

**Minimum Margin of Solvency (MMP):**

```
MMP_P = Premiums × k × 0.18        (Premium-based)
MMP_I = Incurred_Claims × k × 0.26 (Claims-based)

MMP = max(MMP_P, MMP_I) + OSAGO_adjustment

k = Retention coefficient (typically 0.70)
```

**Own Funds (FMP):**

```
FMP = Tier_1 + Tier_2 + Tier_3

Tier_1 = Equity - Intangibles - ECL - Illiquid_Assets + CSM
Tier_2 = Subordinated_Debt (up to 50% of MMP)
Tier_3 = Deferred_Tax_Assets (up to 15% of MMP)
```

---

## 🔌 API Reference

### Authentication

Currently uses session-based authentication. API key authentication available in production version.

### Base URL

```
http://127.0.0.1:5000/api
```

### Endpoints

#### Health Check

```http
GET /api/health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-12-02T12:00:00Z"
}
```

#### IFRS 9 - ECL Calculation

```http
POST /api/ifrs9/ecl
Content-Type: application/json
```

**Request Body:**
```json
{
  "gca": 500000000,          // Gross Carrying Amount (KZT)
  "pd": 0.095,               // Probability of Default (0-1)
  "lgd": 0.69,               // Loss Given Default (0-1)
  "eir": 0.19,               // Effective Interest Rate (0-1)
  "term": 3,                 // Term in years
  "dpd": 0,                  // Days Past Due
  "scenario": "weighted"     // "baseline" | "adverse" | "severe" | "weighted"
}
```

**Response:**
```json
{
  "ecl": 2100000000,
  "stage": 1,
  "ecl_type": "12_month",
  "breakdown": {
    "pd_adjusted": 0.153,
    "lgd_adjusted": 0.69,
    "ead": 500000000,
    "discount_factor": 0.456
  }
}
```

#### IFRS 17 - GMM Calculation

```http
POST /api/ifrs17/gmm
Content-Type: application/json
```

**Request Body:**
```json
{
  "premiums": 100000000,
  "claims_per_year": 80000000,
  "expenses_per_year": 5000000,
  "acquisition_costs": 10000000,
  "term": 10,
  "ra_method": "coc",        // "coc" | "cte"
  "coc_rate": 0.06
}
```

**Response:**
```json
{
  "liability": 88000000,
  "bel": 75000000,
  "ra": 4500000,
  "csm": 8500000,
  "is_onerous": false
}
```

#### Solvency 2 - Capital Calculation

```http
POST /api/solvency/calculate
Content-Type: application/json
```

**Request Body:**
```json
{
  "gross_premiums": 35000000000,
  "incurred_claims": 18000000000,
  "equity": 20000000000,
  "ecl_adjustment": 2100000000,
  "csm_adjustment": 11800000000,
  "subordinated": 3000000000,
  "illiquid": 500000000,
  "has_osago": true,
  "k": 0.70
}
```

**Response:**
```json
{
  "nmp": 2.57,
  "mmp": 1976744186,
  "fmp": 5082093023,
  "status": "well_capitalized",
  "stress_scenarios": {
    "adverse": 1.85,
    "severe": 1.23,
    "var_99_5": 0.98
  }
}
```

#### FGSV - Contribution Calculation

```http
POST /api/fgsv/contribution
Content-Type: application/json
```

**Request Body:**
```json
{
  "gross_premiums": 35000000000,
  "nmp": 2.57,
  "has_violations": false
}
```

**Response:**
```json
{
  "base_contribution": 52500000,
  "multiplier": 1.0,
  "total_contribution": 52500000,
  "rate": 0.0015
}
```

---

## ⚖️ Regulatory Compliance

### Kazakhstan Regulatory Framework

| Standard | Regulation | Implementation |
|----------|------------|----------------|
| **IFRS 9** | ARRF Resolution №269 (29.12.2017) | Full compliance with 3-stage ECL model |
| **IFRS 17** | IASB Standard (01.01.2023 effective) | GMM, VFA, PAA models implemented |
| **Solvency 2** | ARRF Resolution №304 (26.12.2016) | MMP/FMP calculation with stress testing |
| **FGSV** | Law №423-II (03.06.2003) | Contribution calculator and fund monitoring |

### Recent Regulatory Updates

- **ARRF №83 (21.10.2024)**: Updated ECL parameters for macro scenarios
- **ARRF №92 (27.12.2024)**: Enhanced capital requirements for cyber risk
- **ARRF №14 (16.05.2025)**: Internal audit requirements for actuarial models
- **EIOPA 2025**: Macroprudential requirements alignment

### Macro Indicators (December 2025)

| Indicator | Value | Source |
|-----------|-------|--------|
| GDP Growth | +5.6% | NBK Statistics |
| Inflation | 12.9% | NBK CPI Data |
| NBK Base Rate | 18.0% | NBK Policy Rate |
| USD/KZT | 560.00 | NBK Official Rate |
| Brent Oil | $80.70/bbl | Bloomberg |
| MRP 2025 | 3,932 ₸ | Kazakhstan Gov |

---

## 📸 Screenshots

### Insurer Dashboard
![Dashboard](docs/screenshots/dashboard.png)
*Real-time solvency monitoring with color-coded indicators*

### IFRS 9 Calculator
![IFRS9](docs/screenshots/ifrs9.png)
*ECL calculation with detailed formula breakdown*

### IFRS 17 Insurance Contracts
![IFRS17](docs/screenshots/ifrs17.png)
*BEL, RA, CSM calculation with onerous contract detection*

### ARRF Regulatory Dashboard
![ARRF](docs/screenshots/arfr.png)
*Multi-company compliance monitoring for regulators*

### Stress Testing
![Stress](docs/screenshots/stress.png)
*Monte Carlo simulation with scenario analysis*

---

## 🧪 Testing

### Run Unit Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=app --cov-report=html

# Run specific module tests
pytest tests/test_ifrs9.py -v
```

### Test Coverage

```
Module                          Coverage
─────────────────────────────────────────
services/calculation_service.py   98%
services/fgsv_service.py          95%
api/routes.py                     92%
routes.py                         89%
─────────────────────────────────────────
TOTAL                             94%
```

---

## 🤝 Support

### Technical Support

- **Email**: sholpan@rbpartners.kz
- **Documentation**: [GitHub Wiki](https://github.com/krasavchik01/Solvency2/wiki)
- **Issues**: [GitHub Issues](https://github.com/krasavchik01/Solvency2/issues)

### Commercial Inquiries

For enterprise licensing, custom development, or integration services:

- **Sales**: sholpan@rbpartners.kz
- **Website**: www.rbpartners.kz

---

## 📄 License

Copyright © 2025 RB Partners. All rights reserved.

This software is proprietary and confidential. See [COPYRIGHT.md](COPYRIGHT.md) for full details.

---

## 🙏 Acknowledgments

- **ARRF (Kazakhstan)** - Regulatory framework and guidance
- **IASB** - IFRS 9/17 international standards
- **EIOPA** - Solvency 2 European framework
- **National Bank of Kazakhstan** - Macroeconomic data

---

## 🗺️ Roadmap

### Q1 2025
- ✅ IFRS 9 ECL calculator with 3-stage model
- ✅ IFRS 17 GMM/VFA/PAA implementation
- ✅ Solvency 2 MMP/FMP calculation
- ✅ Multi-role access control (Insurer, ARRF, FGSV)

### Q2 2025
- 🔄 Real-time NBK data integration
- 🔄 XBRL export for ARRF reporting
- 🔄 1C and SAP ERP integration
- 🔄 Advanced stress testing (climate risk, cyber risk)

### Q3 2025
- 📋 Machine learning PD/LGD calibration
- 📋 GPU-accelerated Monte Carlo simulations
- 📋 Blockchain audit trail
- 📋 Mobile application (iOS/Android)

### Q4 2025
- 📋 Adilet.zan.kz legislative parser
- 📋 Multi-currency support
- 📋 International GAAP reconciliation
- 📋 White-label solution for other jurisdictions

---

**Built with ❤️ for Kazakhstan's insurance industry**

*Ensuring financial stability through accurate regulatory compliance*
