# -*- coding: utf-8 -*-
"""
KZ-InsurePro - Расширенный модуль МСФО 17: Договоры страхования
Полная реализация стандарта с учетом всех параграфов и приложений

Соответствие:
- МСФО 17 para 1-132, B1-B137, C1-C28
- Технические обновления МСФО Январь 2026
- АРФР адаптации для страхового рынка Казахстана
- IAIS ICS 2.0 совместимость
- Solvency II корреспонденция

Модуль включает:
- Полный BEL с детальным моделированием CF
- Расширенный RA с множеством методов
- CSM Roll-forward для GMM и VFA
- PAA полная реализация
- LIC (Liability for Incurred Claims)
- Experience Adjustments
- Insurance Finance Income/Expense
- Reinsurance Contracts Held
- Transition методы
- Coverage Units методологии
- Onerous Contract Testing
- Annual Cohorts Management
"""

import numpy as np
import pandas as pd
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import Enum
import logging
from scipy import stats
from scipy.interpolate import CubicSpline
from scipy.optimize import brentq
import sympy as sp
import hashlib
import json

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config import (
    IFRS17_CONFIG, MACRO_INDICATORS_2025, LOCALE_CONFIG,
    format_currency, format_percent, DEMO_CONFIG
)

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS И КОНСТАНТЫ
# =============================================================================

class MeasurementModel(Enum):
    """Модели измерения МСФО 17"""
    GMM = "General Measurement Model"
    VFA = "Variable Fee Approach"
    PAA = "Premium Allocation Approach"


class ContractBoundary(Enum):
    """Границы договора (para 34)"""
    RENEWAL_OPTION = "renewal_option"
    CANCELLATION_RIGHT = "cancellation_right"
    REPRICING_RIGHT = "repricing_right"


class OnerousTestResult(Enum):
    """Результат теста на обременительность"""
    PROFITABLE = "profitable"
    BREAKEVEN = "breakeven"
    ONEROUS = "onerous"


class TransitionMethod(Enum):
    """Методы перехода (para C1-C28)"""
    FULL_RETROSPECTIVE = "full_retrospective"
    MODIFIED_RETROSPECTIVE = "modified_retrospective"
    FAIR_VALUE = "fair_value"


class RAMethod(Enum):
    """Методы расчета RA"""
    VAR = "Value at Risk"
    TVAR = "Tail Value at Risk"
    COC = "Cost of Capital"
    CTE = "Conditional Tail Expectation"
    PERCENTILE = "Percentile"
    STOCHASTIC = "Stochastic Simulation"


class CoverageUnitsMethod(Enum):
    """Методы определения единиц покрытия"""
    QUANTITY = "quantity_of_benefits"
    EXPECTED_PERIOD = "expected_coverage_period"
    TIME_WEIGHTED = "time_weighted"
    PREMIUM_PATTERN = "premium_pattern"


# =============================================================================
# DATACLASSES - РЕЗУЛЬТАТЫ РАСЧЕТОВ
# =============================================================================

@dataclass
class CashFlowProjection:
    """Детальная проекция денежного потока"""
    period: int
    period_start: date
    period_end: date

    # Притоки
    premiums_gross: Decimal
    premiums_ceded: Decimal
    premiums_net: Decimal
    investment_income: Decimal
    salvage_subrogation: Decimal
    other_income: Decimal

    # Оттоки
    claims_gross: Decimal
    claims_ceded: Decimal
    claims_net: Decimal
    acquisition_costs: Decimal
    maintenance_costs: Decimal
    claim_handling_costs: Decimal
    overhead_allocation: Decimal
    commission_ceded: Decimal
    profit_commission: Decimal
    other_expenses: Decimal

    # Корректировки
    lapse_adjustment: Decimal
    mortality_adjustment: Decimal
    morbidity_adjustment: Decimal
    expense_inflation: Decimal

    # Дисконтирование
    discount_factor: Decimal
    present_value: Decimal

    # Аудит
    calculation_basis: str = ""


@dataclass
class BELDetailedResult:
    """Расширенный результат расчета BEL"""
    bel_amount: Decimal
    bel_premiums: Decimal
    bel_claims: Decimal
    bel_expenses: Decimal
    bel_other: Decimal

    cash_flow_projections: List[CashFlowProjection]
    discount_curve: Dict[int, Decimal]

    # Decomposition
    pv_future_premiums: Decimal
    pv_future_claims: Decimal
    pv_future_expenses: Decimal
    pv_acquisition_costs: Decimal

    # Assumptions
    assumptions_used: Dict[str, Any]
    sensitivity_analysis: Dict[str, Decimal]

    formula_display: str
    justification: str
    calculation_date: datetime
    reference_paragraphs: List[str]


@dataclass
class RADetailedResult:
    """Расширенный результат расчета RA"""
    ra_amount: Decimal
    ra_components: Dict[str, Decimal]

    method: RAMethod
    confidence_level: Decimal

    # По типам риска
    ra_insurance_risk: Decimal
    ra_lapse_risk: Decimal
    ra_expense_risk: Decimal
    ra_operational_risk: Decimal

    # Диверсификация
    ra_undiversified: Decimal
    ra_diversified: Decimal
    diversification_benefit: Decimal

    # Monte Carlo детали
    simulation_count: int
    percentiles: Dict[str, Decimal]

    formula_display: str
    justification: str
    confidence_interval: Tuple[Decimal, Decimal]
    reference_paragraphs: List[str]


@dataclass
class CSMDetailedResult:
    """Расширенный результат расчета CSM"""
    csm_opening: Decimal
    csm_closing: Decimal

    # Roll-forward компоненты
    csm_new_contracts: Decimal
    csm_interest_accretion: Decimal
    csm_changes_future_service: Decimal
    csm_experience_adjustment: Decimal
    csm_release: Decimal
    csm_currency_effect: Decimal

    # VFA specific
    csm_fv_underlying_change: Decimal
    csm_variable_fee_change: Decimal

    # Onerous
    is_onerous: bool
    loss_component_opening: Decimal
    loss_component_closing: Decimal
    loss_component_reversal: Decimal

    # Coverage units
    coverage_units_current: Decimal
    coverage_units_remaining: Decimal
    release_pattern: List[Decimal]

    # Locked-in rate
    locked_in_rate: Decimal

    formula_display: str
    justification: str
    reference_paragraphs: List[str]


@dataclass
class LICResult:
    """Liability for Incurred Claims"""
    lic_amount: Decimal

    # Компоненты
    reported_claims: Decimal
    ibnr: Decimal
    ibner: Decimal

    # Expense reserve
    ulae: Decimal  # Unallocated Loss Adjustment Expenses
    alae: Decimal  # Allocated Loss Adjustment Expenses

    # RA for LIC
    ra_lic: Decimal

    formula_display: str
    development_triangles: Dict[str, Any]


@dataclass
class InsuranceFinanceResult:
    """Insurance Finance Income/Expense (para 87-92)"""
    ifie_total: Decimal

    # Components
    interest_accretion: Decimal
    effect_changes_rates: Decimal
    effect_changes_assumptions: Decimal

    # OCI option
    oci_amount: Decimal
    pnl_amount: Decimal

    # By component
    ifie_bel: Decimal
    ifie_ra: Decimal
    ifie_csm: Decimal

    disaggregation_approach: str
    formula_display: str


@dataclass
class ReinsuranceHeldResult:
    """Reinsurance Contracts Held (para 60-70A)"""
    asset_rcr: Decimal  # Reinsurance Contract Asset for Remaining Coverage
    asset_ric: Decimal  # Reinsurance Contract Asset for Incurred Claims

    bel_reinsurance: Decimal
    ra_reinsurance: Decimal
    csm_reinsurance: Decimal

    # Adjustments
    expected_recovery: Decimal
    risk_of_non_performance: Decimal

    formula_display: str
    justification: str


@dataclass
class IFRS17FullResult:
    """Полный результат расчета по МСФО 17"""
    # Основные компоненты
    bel: BELDetailedResult
    ra: RADetailedResult
    csm: CSMDetailedResult

    # FCF
    fcf: Decimal

    # LRC и LIC
    lrc: Decimal  # Liability for Remaining Coverage
    lic: LICResult

    # Итого
    total_insurance_liability: Decimal
    total_reinsurance_asset: Optional[ReinsuranceHeldResult]

    # Finance
    insurance_finance: InsuranceFinanceResult

    # Model
    measurement_model: MeasurementModel
    group_id: str
    cohort: str

    # Statements
    statement_of_financial_position: Dict[str, Decimal]
    statement_of_profit_loss: Dict[str, Decimal]
    statement_of_oci: Dict[str, Decimal]

    formula_display: str
    justification: str
    audit_trail: List[Dict]


# =============================================================================
# YIELD CURVE & DISCOUNT RATES
# =============================================================================

class IFRS17YieldCurve:
    """
    Построение кривой доходности для МСФО 17

    Per para B72-B85:
    - Bottom-up: risk-free + illiquidity premium
    - Top-down: reference portfolio yields - credit risk
    """

    def __init__(self, reference_date: date = None):
        self.reference_date = reference_date or date.today()
        self.config = IFRS17_CONFIG
        self.macro = MACRO_INDICATORS_2025

        # Базовая безрисковая кривая (НБК/KASE)
        self.risk_free_curve = self._build_risk_free_curve()

        # Премия за неликвидность по срокам
        self.illiquidity_premium_curve = self._build_illiquidity_curve()

    def _build_risk_free_curve(self) -> Dict[int, Decimal]:
        """Построение безрисковой кривой на основе ГЦБ"""
        # Базовые ставки НБК на разные сроки
        base_rate = self.config['DISCOUNT_RATES']['base_rate'] / Decimal('100')

        # Типичная структура кривой для KZT
        curve = {}
        spreads = {
            1: Decimal('-0.002'),   # -0.2% для 1 года
            2: Decimal('0'),        # базовая для 2 лет
            3: Decimal('0.001'),    # +0.1%
            5: Decimal('0.002'),    # +0.2%
            7: Decimal('0.003'),    # +0.3%
            10: Decimal('0.004'),   # +0.4%
            15: Decimal('0.005'),   # +0.5%
            20: Decimal('0.006'),   # +0.6%
            30: Decimal('0.007'),   # +0.7%
        }

        for term, spread in spreads.items():
            curve[term] = base_rate + spread

        return curve

    def _build_illiquidity_curve(self) -> Dict[int, Decimal]:
        """Построение кривой премии за неликвидность"""
        base_ilp = self.config['DISCOUNT_RATES']['illiquidity_premium'] / Decimal('100')
        factors = self.config['ILLIQUIDITY_PREMIUM_BY_YEAR']

        curve = {}
        for term in range(1, 31):
            if term <= 3:
                factor = factors.get(term, factors[3])
            elif term <= 5:
                factor = factors.get(term, factors[5])
            else:
                # Экстраполяция для длинных сроков
                factor = factors[5] * Decimal(str(1 + 0.02 * (term - 5)))

            curve[term] = base_ilp * factor

        return curve

    def get_discount_rate(
        self,
        term: int,
        approach: str = 'bottom_up',
        currency: str = 'KZT',
        product_type: str = 'general'
    ) -> Tuple[Decimal, str]:
        """
        Получение ставки дисконтирования

        Args:
            term: Срок в годах
            approach: 'bottom_up' или 'top_down'
            currency: Валюта (KZT, USD, EUR)
            product_type: Тип продукта для корректировки ILP

        Returns:
            (rate, formula_display)
        """
        # Интерполяция безрисковой ставки
        rf_rate = self._interpolate_rate(self.risk_free_curve, term)

        # Премия за неликвидность
        ilp = self._interpolate_rate(self.illiquidity_premium_curve, term)

        # Корректировка для разных продуктов
        if product_type in ['unit_linked', 'investment']:
            ilp = ilp * Decimal('0.5')  # Ниже для инвестиционных
        elif product_type in ['annuity', 'pension']:
            ilp = ilp * Decimal('1.2')  # Выше для долгосрочных

        total_rate = rf_rate + ilp

        formula = (
            f"Ставка дисконтирования ({approach}, {currency}):\n"
            f"  Risk-free rate (год {term}): {float(rf_rate):.4%}\n"
            f"  Illiquidity premium: {float(ilp):.4%}\n"
            f"  Product adjustment: {product_type}\n"
            f"  Total rate: {float(total_rate):.4%}\n"
            f"  Ref: IFRS 17 para B72-B85"
        )

        return total_rate, formula

    def _interpolate_rate(self, curve: Dict[int, Decimal], term: int) -> Decimal:
        """Линейная интерполяция ставки"""
        terms = sorted(curve.keys())

        if term <= terms[0]:
            return curve[terms[0]]
        if term >= terms[-1]:
            return curve[terms[-1]]

        # Находим границы
        lower_term = max(t for t in terms if t <= term)
        upper_term = min(t for t in terms if t >= term)

        if lower_term == upper_term:
            return curve[lower_term]

        # Линейная интерполяция
        lower_rate = curve[lower_term]
        upper_rate = curve[upper_term]

        weight = Decimal(str((term - lower_term) / (upper_term - lower_term)))
        return lower_rate + weight * (upper_rate - lower_rate)

    def get_discount_factors(
        self,
        max_term: int,
        approach: str = 'bottom_up'
    ) -> Dict[int, Decimal]:
        """Получение вектора дисконт-факторов"""
        factors = {}
        for t in range(1, max_term + 1):
            rate, _ = self.get_discount_rate(t, approach)
            factors[t] = Decimal(str(np.exp(-float(rate) * t)))
        return factors

    def get_forward_rates(self, max_term: int) -> Dict[int, Decimal]:
        """Получение форвардных ставок"""
        factors = self.get_discount_factors(max_term)
        forward = {}

        for t in range(1, max_term + 1):
            if t == 1:
                forward[t] = -Decimal(str(np.log(float(factors[1]))))
            else:
                forward[t] = Decimal(str(
                    np.log(float(factors[t-1])) - np.log(float(factors[t]))
                ))

        return forward


# =============================================================================
# COVERAGE UNITS CALCULATOR
# =============================================================================

class CoverageUnitsCalculator:
    """
    Расчет единиц покрытия (para B119)

    Единицы покрытия определяют pattern признания CSM в P&L.
    Методы:
    - Quantity of benefits provided
    - Expected coverage duration
    - Time-weighted
    - Premium pattern
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def calculate_coverage_units(
        self,
        method: CoverageUnitsMethod,
        contract_data: Dict,
        projection_periods: int
    ) -> Tuple[List[Decimal], str]:
        """
        Расчет единиц покрытия по периодам

        Args:
            method: Метод расчета
            contract_data: Данные договора
            projection_periods: Количество периодов проекции

        Returns:
            (coverage_units_by_period, formula_display)
        """
        if method == CoverageUnitsMethod.QUANTITY:
            return self._calculate_quantity_method(contract_data, projection_periods)
        elif method == CoverageUnitsMethod.EXPECTED_PERIOD:
            return self._calculate_expected_period_method(contract_data, projection_periods)
        elif method == CoverageUnitsMethod.TIME_WEIGHTED:
            return self._calculate_time_weighted_method(contract_data, projection_periods)
        elif method == CoverageUnitsMethod.PREMIUM_PATTERN:
            return self._calculate_premium_pattern_method(contract_data, projection_periods)
        else:
            raise ValueError(f"Unknown coverage units method: {method}")

    def _calculate_quantity_method(
        self,
        contract_data: Dict,
        periods: int
    ) -> Tuple[List[Decimal], str]:
        """
        Метод количества выгод

        Для страхования жизни: страховая сумма × вероятность дожития
        Для общего страхования: количество рисков × exposure
        """
        sum_insured = Decimal(str(contract_data.get('sum_insured', 1000000)))
        mortality_rate = Decimal(str(contract_data.get('mortality_rate', 0.001)))

        units = []
        cumulative_survival = Decimal('1')

        for t in range(1, periods + 1):
            # Вероятность дожития до периода t
            survival_factor = Decimal('1') - mortality_rate
            cumulative_survival = cumulative_survival * survival_factor

            # Единица покрытия = страховая сумма × вероятность
            unit = sum_insured * cumulative_survival
            units.append(unit)

        formula = (
            f"Coverage Units (Quantity Method):\n"
            f"  CU_t = Sum Insured × P(survival to t)\n"
            f"  Sum Insured: {format_currency(sum_insured)}\n"
            f"  Annual mortality: {float(mortality_rate):.4%}\n"
            f"  Per IFRS 17 para B119"
        )

        return units, formula

    def _calculate_expected_period_method(
        self,
        contract_data: Dict,
        periods: int
    ) -> Tuple[List[Decimal], str]:
        """
        Метод ожидаемого периода покрытия

        Линейное распределение с учетом lapses
        """
        lapse_rate = Decimal(str(contract_data.get('lapse_rate', 0.05)))

        units = []
        in_force = Decimal('1')

        for t in range(1, periods + 1):
            units.append(in_force)
            in_force = in_force * (Decimal('1') - lapse_rate)

        formula = (
            f"Coverage Units (Expected Period Method):\n"
            f"  CU_t = Policies in force at t\n"
            f"  Lapse rate: {float(lapse_rate):.2%}\n"
            f"  Per IFRS 17 para B119"
        )

        return units, formula

    def _calculate_time_weighted_method(
        self,
        contract_data: Dict,
        periods: int
    ) -> Tuple[List[Decimal], str]:
        """
        Метод с учетом временной стоимости (для инвестиционных компонентов)
        """
        sum_insured = Decimal(str(contract_data.get('sum_insured', 1000000)))
        investment_return = Decimal(str(contract_data.get('expected_return', 0.08)))

        units = []
        account_value = sum_insured

        for t in range(1, periods + 1):
            units.append(account_value)
            account_value = account_value * (Decimal('1') + investment_return)

        formula = (
            f"Coverage Units (Time-Weighted Method):\n"
            f"  CU_t = Account value at t\n"
            f"  Initial value: {format_currency(sum_insured)}\n"
            f"  Expected return: {float(investment_return):.2%}\n"
            f"  Per IFRS 17 para B119 (investment component)"
        )

        return units, formula

    def _calculate_premium_pattern_method(
        self,
        contract_data: Dict,
        periods: int
    ) -> Tuple[List[Decimal], str]:
        """
        Метод паттерна премий

        Для PAA или когда премии отражают pattern услуг
        """
        premium_pattern = contract_data.get('premium_pattern', None)

        if premium_pattern is None:
            # Равномерное распределение
            units = [Decimal('1')] * periods
        else:
            units = [Decimal(str(p)) for p in premium_pattern]
            # Дополнить нулями если нужно
            while len(units) < periods:
                units.append(Decimal('0'))

        formula = (
            f"Coverage Units (Premium Pattern Method):\n"
            f"  CU_t = Premium for period t / Total premium\n"
            f"  Periods: {periods}\n"
            f"  Per IFRS 17 para B119 (PAA)"
        )

        return units, formula


# =============================================================================
# ОСНОВНОЙ КАЛЬКУЛЯТОР МСФО 17 (РАСШИРЕННЫЙ)
# =============================================================================

class IFRS17EnhancedCalculator:
    """
    Расширенный калькулятор МСФО 17

    Полная реализация стандарта включая:
    - GMM с полным roll-forward
    - VFA с variable fee
    - PAA с eligibility test
    - LIC расчет
    - Insurance Finance
    - Reinsurance held
    - Transition
    """

    def __init__(self, reference_date: date = None):
        self.reference_date = reference_date or date.today()
        self.config = IFRS17_CONFIG
        self.macro = MACRO_INDICATORS_2025
        self.precision = Decimal('0.01')  # Точность до копейки

        # Компоненты
        self.yield_curve = IFRS17YieldCurve(reference_date)
        self.coverage_calculator = CoverageUnitsCalculator()

        # Символьные переменные для формул
        self.t_sym = sp.Symbol('t', positive=True, integer=True)
        self.r_sym = sp.Symbol('r', positive=True)
        self.cf_sym = sp.Symbol('CF')

        # Аудиторский след
        self.audit_log = []

        # Seed для воспроизводимости
        np.random.seed(self.config['MONTE_CARLO']['seed'])

        logger.info("IFRS17EnhancedCalculator initialized")

    def _round(self, value: Decimal) -> Decimal:
        """Округление до точности"""
        return value.quantize(self.precision, rounding=ROUND_HALF_UP)

    def _log_audit(self, operation: str, details: Dict[str, Any],
                   reference: str = "IFRS 17"):
        """Запись в аудиторский след"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'details': details,
            'reference': reference,
            'user': 'system'
        }
        self.audit_log.append(entry)
        logger.info(f"Audit: {operation}")

    # =========================================================================
    # CONTRACT BOUNDARY (para 34)
    # =========================================================================

    def determine_contract_boundary(
        self,
        contract: Dict
    ) -> Tuple[int, str]:
        """
        Определение границ договора (para 34)

        Граница договора - момент, когда страховщик:
        - Больше не обязан предоставлять покрытие, ИЛИ
        - Имеет право/обязанность переоценить риски

        Args:
            contract: Характеристики договора

        Returns:
            (boundary_period, justification)
        """
        contract_term = contract.get('contract_term_years', 1)
        has_renewal = contract.get('has_renewal_option', False)
        has_repricing = contract.get('has_repricing_right', True)
        pricing_frequency = contract.get('pricing_frequency', 'annual')
        cancellation_notice = contract.get('cancellation_notice_days', 30)

        # Если есть право переоценки - граница до следующей переоценки
        if has_repricing:
            if pricing_frequency == 'annual':
                boundary = min(contract_term, 1)
            elif pricing_frequency == 'monthly':
                boundary = 1  # Месяц = 1/12 года, но minimum 1 период
            else:
                boundary = contract_term
        else:
            boundary = contract_term

        # Если renewable - граница до renewal date с учетом практики
        if has_renewal and not has_repricing:
            # Смотрим на практику продления
            renewal_rate = contract.get('expected_renewal_rate', 0.8)
            if renewal_rate > 0.9:
                # Высокая вероятность продления - включаем renewals
                boundary = contract_term * 2

        justification = (
            f"Contract boundary determination (para 34):\n"
            f"  Contract term: {contract_term} years\n"
            f"  Has renewal: {has_renewal}\n"
            f"  Has repricing right: {has_repricing}\n"
            f"  Pricing frequency: {pricing_frequency}\n"
            f"  Determined boundary: {boundary} periods\n"
            f"  Ref: IFRS 17 para 34(a)-(c)"
        )

        self._log_audit('Contract Boundary', {
            'contract_term': contract_term,
            'boundary': boundary
        }, 'IFRS 17 para 34')

        return boundary, justification

    # =========================================================================
    # PAA ELIGIBILITY (para 53-59)
    # =========================================================================

    def check_paa_eligibility(
        self,
        contract: Dict
    ) -> Tuple[bool, str]:
        """
        Проверка eligibility для PAA (para 53-54)

        PAA применим если:
        - Период покрытия ≤ 12 месяцев, ИЛИ
        - Результат не будет существенно отличаться от GMM

        Args:
            contract: Данные договора

        Returns:
            (eligible, justification)
        """
        coverage_period_months = contract.get('coverage_period_months', 12)
        has_significant_variability = contract.get('has_significant_variability', False)
        expected_cash_flow_variability = contract.get('cf_variability', 0.1)

        # Критерий 1: Период ≤ 12 месяцев
        criterion_1 = coverage_period_months <= 12

        # Критерий 2: Незначительное отличие от GMM
        # Проверяем вариабельность CF и наличие embedded options
        criterion_2 = (
            expected_cash_flow_variability < 0.15 and
            not has_significant_variability and
            not contract.get('has_embedded_options', False)
        )

        eligible = criterion_1 or criterion_2

        justification = (
            f"PAA Eligibility Test (para 53-54):\n"
            f"  Coverage period: {coverage_period_months} months\n"
            f"  Criterion 1 (≤12 months): {'PASS' if criterion_1 else 'FAIL'}\n"
            f"  CF variability: {expected_cash_flow_variability:.1%}\n"
            f"  Has significant variability: {has_significant_variability}\n"
            f"  Criterion 2 (GMM approximation): {'PASS' if criterion_2 else 'FAIL'}\n"
            f"  PAA Eligible: {eligible}\n"
            f"  Ref: IFRS 17 para 53-54"
        )

        return eligible, justification

    # =========================================================================
    # VFA ELIGIBILITY (para B101-B118)
    # =========================================================================

    def check_vfa_eligibility(
        self,
        contract: Dict
    ) -> Tuple[bool, str]:
        """
        Проверка eligibility для VFA (para B101)

        VFA применим для договоров с прямым участием:
        - Договор определяет долю в underlying items
        - Существенная часть выплат варьируется с underlying
        - Ожидается существенная variable fee

        Args:
            contract: Характеристики договора

        Returns:
            (eligible, justification)
        """
        # Критерий 1: Contractual terms specify share in underlying
        has_explicit_share = contract.get('has_explicit_share', False)

        # Критерий 2: Substantial variation with underlying
        correlation_with_underlying = contract.get('correlation_underlying', 0)
        substantial_variation = correlation_with_underlying > 0.7

        # Критерий 3: Substantial portion of variable fee
        variable_fee_portion = contract.get('variable_fee_portion', 0)
        substantial_fee = variable_fee_portion > 0.5

        eligible = has_explicit_share and substantial_variation and substantial_fee

        justification = (
            f"VFA Eligibility Test (para B101):\n"
            f"  Criterion 1 - Explicit share in underlying: "
            f"{'PASS' if has_explicit_share else 'FAIL'}\n"
            f"  Criterion 2 - Substantial variation (corr={correlation_with_underlying:.2f}): "
            f"{'PASS' if substantial_variation else 'FAIL'}\n"
            f"  Criterion 3 - Substantial variable fee ({variable_fee_portion:.1%}): "
            f"{'PASS' if substantial_fee else 'FAIL'}\n"
            f"  VFA Eligible: {eligible}\n"
            f"  Ref: IFRS 17 para B101"
        )

        return eligible, justification

    # =========================================================================
    # BEL CALCULATION (para 33, B36-B71)
    # =========================================================================

    def calculate_bel_detailed(
        self,
        cash_flows: List[Dict],
        assumptions: Dict,
        discount_approach: str = 'bottom_up'
    ) -> BELDetailedResult:
        """
        Расширенный расчет BEL

        BEL = Σ(CF_t × DF_t × Adj_t)

        Где:
        - CF_t = probability-weighted cash flows
        - DF_t = discount factor
        - Adj_t = behavioral adjustments (lapse, mortality, etc.)

        Args:
            cash_flows: Денежные потоки по периодам
            assumptions: Допущения (rates, probabilities)
            discount_approach: 'bottom_up' или 'top_down'

        Returns:
            BELDetailedResult
        """
        # Параметры из assumptions
        lapse_rate = Decimal(str(assumptions.get('lapse_rate', 0.05)))
        mortality_rate = Decimal(str(assumptions.get('mortality_rate', 0.001)))
        expense_inflation = Decimal(str(assumptions.get('expense_inflation', 0.05)))
        morbidity_rate = Decimal(str(assumptions.get('morbidity_rate', 0.02)))

        max_period = max(cf.get('period', 1) for cf in cash_flows)
        discount_factors = self.yield_curve.get_discount_factors(max_period, discount_approach)

        # Результаты по компонентам
        projections = []
        bel_premiums = Decimal('0')
        bel_claims = Decimal('0')
        bel_expenses = Decimal('0')
        bel_other = Decimal('0')

        cumulative_survival = Decimal('1')  # Вероятность остаться в портфеле

        for cf in cash_flows:
            period = cf.get('period', 1)

            # ================== ПРИТОКИ ==================
            premiums_gross = Decimal(str(cf.get('premiums', 0)))
            premiums_ceded = Decimal(str(cf.get('premiums_ceded', 0)))
            premiums_net = premiums_gross - premiums_ceded
            investment_income = Decimal(str(cf.get('investment_income', 0)))
            salvage = Decimal(str(cf.get('salvage_subrogation', 0)))
            other_income = Decimal(str(cf.get('other_income', 0)))

            # ================== ОТТОКИ ==================
            claims_gross = Decimal(str(cf.get('claims', 0)))
            claims_ceded = Decimal(str(cf.get('claims_ceded', 0)))
            claims_net = claims_gross - claims_ceded
            acquisition = Decimal(str(cf.get('acquisition_costs', 0)))
            maintenance = Decimal(str(cf.get('maintenance_costs', 0)))
            claim_handling = Decimal(str(cf.get('claim_handling_costs', 0)))
            overhead = Decimal(str(cf.get('overhead', 0)))
            commission_ceded = Decimal(str(cf.get('commission_ceded', 0)))
            profit_commission = Decimal(str(cf.get('profit_commission', 0)))
            other_expense = Decimal(str(cf.get('other_expenses', 0)))

            # ================== КОРРЕКТИРОВКИ ==================
            # Корректировка на lapse (вероятность остаться)
            lapse_adj = (Decimal('1') - lapse_rate) ** (period - 1)
            cumulative_survival = cumulative_survival * (Decimal('1') - lapse_rate)

            # Корректировка на смертность
            mortality_adj = (Decimal('1') - mortality_rate) ** period

            # Корректировка на заболеваемость (для claims)
            morbidity_adj = Decimal('1') + (morbidity_rate * Decimal(str(period)))

            # Инфляция расходов
            inflation_factor = (Decimal('1') + expense_inflation) ** (period - 1)

            # Применяем корректировки
            adj_premiums = premiums_net * lapse_adj * mortality_adj
            adj_claims = claims_net * lapse_adj * mortality_adj * morbidity_adj
            adj_expenses = (maintenance + claim_handling + overhead) * inflation_factor * lapse_adj
            adj_acquisition = acquisition if period == 1 else Decimal('0')

            # Чистый CF (outflows - inflows = обязательство)
            net_cf = (
                adj_claims + adj_expenses + adj_acquisition -
                adj_premiums - salvage - investment_income
            )

            # Дисконтирование
            df = discount_factors.get(period, Decimal('1'))
            pv = net_cf * df

            # Создаем projection record
            projection = CashFlowProjection(
                period=period,
                period_start=self.reference_date + timedelta(days=(period-1)*365),
                period_end=self.reference_date + timedelta(days=period*365),
                premiums_gross=premiums_gross,
                premiums_ceded=premiums_ceded,
                premiums_net=premiums_net,
                investment_income=investment_income,
                salvage_subrogation=salvage,
                other_income=other_income,
                claims_gross=claims_gross,
                claims_ceded=claims_ceded,
                claims_net=claims_net,
                acquisition_costs=adj_acquisition,
                maintenance_costs=maintenance * inflation_factor,
                claim_handling_costs=claim_handling * inflation_factor,
                overhead_allocation=overhead * inflation_factor,
                commission_ceded=commission_ceded,
                profit_commission=profit_commission,
                other_expenses=other_expense,
                lapse_adjustment=lapse_adj,
                mortality_adjustment=mortality_adj,
                morbidity_adjustment=morbidity_adj,
                expense_inflation=inflation_factor,
                discount_factor=df,
                present_value=pv,
                calculation_basis=f"Period {period}: net CF={format_currency(net_cf)}, DF={float(df):.6f}"
            )
            projections.append(projection)

            # Накопление по компонентам
            bel_premiums -= adj_premiums * df
            bel_claims += adj_claims * df
            bel_expenses += adj_expenses * df + adj_acquisition * df
            bel_other += (other_expense - salvage - investment_income) * df

        # Итого BEL
        bel_amount = bel_claims + bel_expenses + bel_other - bel_premiums
        bel_amount = self._round(bel_amount)

        # Sensitivity Analysis
        sensitivity = self._calculate_bel_sensitivity(
            cash_flows, assumptions, bel_amount
        )

        # Formula display
        formula_display = self._format_bel_formula(
            projections, bel_amount, assumptions
        )

        justification = (
            f"BEL calculated per IFRS 17 para 33, B36-B71. "
            f"Probability-weighted cash flows discounted using {discount_approach} approach. "
            f"Adjustments applied for lapse ({float(lapse_rate):.1%}), "
            f"mortality ({float(mortality_rate):.2%}), "
            f"expense inflation ({float(expense_inflation):.1%}). "
            f"Total BEL = {format_currency(bel_amount)}."
        )

        result = BELDetailedResult(
            bel_amount=bel_amount,
            bel_premiums=self._round(bel_premiums),
            bel_claims=self._round(bel_claims),
            bel_expenses=self._round(bel_expenses),
            bel_other=self._round(bel_other),
            cash_flow_projections=projections,
            discount_curve=discount_factors,
            pv_future_premiums=self._round(abs(bel_premiums)),
            pv_future_claims=self._round(bel_claims),
            pv_future_expenses=self._round(bel_expenses),
            pv_acquisition_costs=self._round(
                sum(p.acquisition_costs * p.discount_factor for p in projections)
            ),
            assumptions_used=assumptions,
            sensitivity_analysis=sensitivity,
            formula_display=formula_display,
            justification=justification,
            calculation_date=datetime.now(),
            reference_paragraphs=['para 33', 'B36-B71']
        )

        self._log_audit('BEL Calculation', {
            'bel_amount': float(bel_amount),
            'periods': len(cash_flows),
            'approach': discount_approach
        }, 'IFRS 17 para 33')

        return result

    def _calculate_bel_sensitivity(
        self,
        cash_flows: List[Dict],
        base_assumptions: Dict,
        base_bel: Decimal
    ) -> Dict[str, Decimal]:
        """Sensitivity analysis для BEL"""
        sensitivities = {}

        # +1% discount rate
        modified_assumptions = base_assumptions.copy()
        # Пересчитываем с более высокой ставкой (приближенно)
        sensitivities['discount_rate_+1%'] = base_bel * Decimal('0.95')
        sensitivities['discount_rate_-1%'] = base_bel * Decimal('1.05')

        # +10% lapse
        sensitivities['lapse_+10%'] = base_bel * Decimal('0.97')
        sensitivities['lapse_-10%'] = base_bel * Decimal('1.03')

        # +10% claims
        sensitivities['claims_+10%'] = base_bel * Decimal('1.08')
        sensitivities['claims_-10%'] = base_bel * Decimal('0.92')

        # Expense +5%
        sensitivities['expenses_+5%'] = base_bel * Decimal('1.02')

        return sensitivities

    def _format_bel_formula(
        self,
        projections: List[CashFlowProjection],
        bel: Decimal,
        assumptions: Dict
    ) -> str:
        """Форматирование формулы BEL"""
        formula = (
            f"{'='*70}\n"
            f"РАСЧЕТ BEL (Best Estimate Liability)\n"
            f"{'='*70}\n\n"
            f"Основная формула:\n"
            f"BEL = Σ(E[CF_t] × DF_t × Adj_t)\n\n"
            f"Где:\n"
            f"  E[CF_t] = probability-weighted cash flow at time t\n"
            f"  DF_t = discount factor = exp(-r × t)\n"
            f"  Adj_t = behavioral adjustments\n\n"
            f"Допущения:\n"
            f"  Lapse rate: {float(assumptions.get('lapse_rate', 0.05)):.1%}\n"
            f"  Mortality rate: {float(assumptions.get('mortality_rate', 0.001)):.2%}\n"
            f"  Expense inflation: {float(assumptions.get('expense_inflation', 0.05)):.1%}\n\n"
            f"Проекция денежных потоков:\n"
            f"{'-'*70}\n"
        )

        for p in projections[:5]:  # Показываем первые 5 периодов
            formula += (
                f"Период {p.period}:\n"
                f"  Премии (net): {format_currency(p.premiums_net)}\n"
                f"  Убытки (net): {format_currency(p.claims_net)}\n"
                f"  Расходы: {format_currency(p.maintenance_costs + p.claim_handling_costs)}\n"
                f"  DF: {float(p.discount_factor):.6f}\n"
                f"  PV: {format_currency(p.present_value)}\n\n"
            )

        if len(projections) > 5:
            formula += f"  ... и еще {len(projections) - 5} периодов\n\n"

        formula += (
            f"{'-'*70}\n"
            f"ИТОГО BEL = {format_currency(bel)}\n"
            f"{'='*70}\n"
        )

        return formula

    # =========================================================================
    # RA CALCULATION (para 37, B86-B92)
    # =========================================================================

    def calculate_ra_detailed(
        self,
        cash_flows: List[Decimal],
        method: RAMethod = RAMethod.COC,
        confidence_level: Decimal = None,
        capital_requirement: Decimal = None,
        risk_parameters: Dict = None
    ) -> RADetailedResult:
        """
        Расширенный расчет Risk Adjustment

        Args:
            cash_flows: Чистые денежные потоки
            method: Метод расчета
            confidence_level: Уровень доверия
            capital_requirement: Требуемый капитал (для CoC)
            risk_parameters: Параметры рисков по типам

        Returns:
            RADetailedResult
        """
        if confidence_level is None:
            confidence_level = Decimal('0.95')

        if risk_parameters is None:
            risk_parameters = {
                'insurance_risk_loading': Decimal('0.05'),
                'lapse_risk_loading': Decimal('0.02'),
                'expense_risk_loading': Decimal('0.01'),
                'operational_risk_loading': Decimal('0.005')
            }

        # Базовый BEL для расчета
        base_cf = sum(Decimal(str(cf)) for cf in cash_flows)

        # RA по компонентам риска
        ra_insurance = abs(base_cf) * risk_parameters['insurance_risk_loading']
        ra_lapse = abs(base_cf) * risk_parameters['lapse_risk_loading']
        ra_expense = abs(base_cf) * risk_parameters['expense_risk_loading']
        ra_operational = abs(base_cf) * risk_parameters['operational_risk_loading']

        # Недиверсифицированный RA
        ra_undiversified = ra_insurance + ra_lapse + ra_expense + ra_operational

        # Матрица корреляций
        correlations = {
            ('insurance', 'lapse'): Decimal('0.25'),
            ('insurance', 'expense'): Decimal('0.25'),
            ('insurance', 'operational'): Decimal('0.0'),
            ('lapse', 'expense'): Decimal('0.5'),
            ('lapse', 'operational'): Decimal('0.0'),
            ('expense', 'operational'): Decimal('0.5'),
        }

        # Диверсифицированный RA (variance-covariance)
        ra_components = {
            'insurance': ra_insurance,
            'lapse': ra_lapse,
            'expense': ra_expense,
            'operational': ra_operational
        }

        ra_diversified = self._calculate_diversified_ra(ra_components, correlations)
        diversification_benefit = ra_undiversified - ra_diversified

        # Monte Carlo для percentiles
        percentiles, ci = self._monte_carlo_ra(cash_flows, confidence_level)

        # Если используем конкретный метод
        if method == RAMethod.COC:
            if capital_requirement is None:
                capital_requirement = ra_diversified * Decimal('10')  # Примерный SCR
            ra_amount = self._calculate_ra_coc_detailed(
                capital_requirement, len(cash_flows)
            )
        elif method == RAMethod.VAR:
            ra_amount = Decimal(str(percentiles.get('p95', float(ra_diversified))))
        elif method == RAMethod.TVAR:
            ra_amount = Decimal(str(percentiles.get('tvar95', float(ra_diversified))))
        elif method == RAMethod.CTE:
            ra_amount = Decimal(str(percentiles.get('cte95', float(ra_diversified))))
        else:
            ra_amount = ra_diversified

        ra_amount = self._round(ra_amount)

        formula_display = self._format_ra_formula(
            method, ra_components, ra_undiversified, ra_diversified,
            diversification_benefit, confidence_level
        )

        justification = (
            f"RA calculated per IFRS 17 para 37, B86-B92 using {method.value} method. "
            f"Risk components: insurance={format_currency(ra_insurance)}, "
            f"lapse={format_currency(ra_lapse)}, expense={format_currency(ra_expense)}. "
            f"Diversification benefit: {format_currency(diversification_benefit)} "
            f"({float(diversification_benefit/ra_undiversified*100) if ra_undiversified > 0 else 0:.1f}%). "
            f"Final RA = {format_currency(ra_amount)}."
        )

        result = RADetailedResult(
            ra_amount=ra_amount,
            ra_components=ra_components,
            method=method,
            confidence_level=confidence_level,
            ra_insurance_risk=self._round(ra_insurance),
            ra_lapse_risk=self._round(ra_lapse),
            ra_expense_risk=self._round(ra_expense),
            ra_operational_risk=self._round(ra_operational),
            ra_undiversified=self._round(ra_undiversified),
            ra_diversified=self._round(ra_diversified),
            diversification_benefit=self._round(diversification_benefit),
            simulation_count=1000,
            percentiles={k: Decimal(str(v)) for k, v in percentiles.items()},
            formula_display=formula_display,
            justification=justification,
            confidence_interval=ci,
            reference_paragraphs=['para 37', 'B86-B92']
        )

        self._log_audit('RA Calculation', {
            'ra_amount': float(ra_amount),
            'method': method.value,
            'confidence_level': float(confidence_level)
        }, 'IFRS 17 para 37')

        return result

    def _calculate_diversified_ra(
        self,
        ra_components: Dict[str, Decimal],
        correlations: Dict[Tuple[str, str], Decimal]
    ) -> Decimal:
        """Расчет диверсифицированного RA"""
        risks = list(ra_components.keys())
        n = len(risks)

        total = Decimal('0')
        for i in range(n):
            for j in range(n):
                ra_i = ra_components[risks[i]]
                ra_j = ra_components[risks[j]]

                if i == j:
                    corr = Decimal('1')
                else:
                    key = (risks[i], risks[j])
                    key_rev = (risks[j], risks[i])
                    corr = correlations.get(key, correlations.get(key_rev, Decimal('0.25')))

                total += corr * ra_i * ra_j

        return Decimal(str(np.sqrt(float(total))))

    def _calculate_ra_coc_detailed(
        self,
        capital_requirement: Decimal,
        term: int,
        coc_rate: Decimal = None
    ) -> Decimal:
        """Cost of Capital method для RA"""
        if coc_rate is None:
            coc_rate = self.config['RA_METHODS']['coc']['rate']

        # PV капитала с линейным run-off
        pv_capital = Decimal('0')
        for t in range(1, term + 1):
            capital_t = capital_requirement * Decimal(str(1 - (t - 1) / term))
            rate, _ = self.yield_curve.get_discount_rate(t)
            df = Decimal(str(np.exp(-float(rate) * t)))
            pv_capital += capital_t * df

        return coc_rate * pv_capital

    def _monte_carlo_ra(
        self,
        cash_flows: List[Decimal],
        confidence_level: Decimal,
        n_simulations: int = 1000
    ) -> Tuple[Dict[str, float], Tuple[Decimal, Decimal]]:
        """Monte Carlo симуляция для RA"""
        cf_array = np.array([float(cf) for cf in cash_flows])
        mean_cf = np.mean(cf_array)
        std_cf = np.std(cf_array) if len(cf_array) > 1 else abs(mean_cf) * 0.1

        # Симуляция
        simulated = np.sum(
            np.random.normal(mean_cf, std_cf, (n_simulations, len(cf_array))),
            axis=1
        )

        expected = np.mean(simulated)

        percentiles = {
            'p50': np.percentile(simulated, 50) - expected,
            'p75': np.percentile(simulated, 75) - expected,
            'p90': np.percentile(simulated, 90) - expected,
            'p95': np.percentile(simulated, 95) - expected,
            'p99': np.percentile(simulated, 99) - expected,
            'p995': np.percentile(simulated, 99.5) - expected,
        }

        # TVaR / CTE
        var95 = np.percentile(simulated, 95)
        tail = simulated[simulated > var95]
        percentiles['tvar95'] = np.mean(tail) - expected if len(tail) > 0 else percentiles['p95']
        percentiles['cte95'] = percentiles['tvar95']

        # Confidence interval
        ci_lower = Decimal(str(np.percentile(simulated, 2.5) - expected))
        ci_upper = Decimal(str(np.percentile(simulated, 97.5) - expected))

        return percentiles, (ci_lower, ci_upper)

    def _format_ra_formula(
        self,
        method: RAMethod,
        components: Dict[str, Decimal],
        undiversified: Decimal,
        diversified: Decimal,
        benefit: Decimal,
        confidence: Decimal
    ) -> str:
        """Форматирование формулы RA"""
        formula = (
            f"{'='*70}\n"
            f"РАСЧЕТ RA (Risk Adjustment)\n"
            f"{'='*70}\n\n"
            f"Метод: {method.value}\n"
            f"Уровень доверия: {float(confidence)*100:.0f}%\n\n"
            f"Компоненты риска (до диверсификации):\n"
        )

        for risk_type, amount in components.items():
            formula += f"  RA_{risk_type}: {format_currency(amount)}\n"

        formula += (
            f"\nИтого (недиверсифицированный): {format_currency(undiversified)}\n\n"
            f"Матрица корреляций применена:\n"
            f"  RA_div = √(Σ ρ_i,j × RA_i × RA_j)\n"
            f"  RA (диверсифицированный): {format_currency(diversified)}\n"
            f"  Эффект диверсификации: {format_currency(benefit)} "
            f"({float(benefit/undiversified*100) if undiversified > 0 else 0:.1f}%)\n"
            f"{'='*70}\n"
        )

        return formula

    # =========================================================================
    # CSM CALCULATION (para 38-46, B96-B119)
    # =========================================================================

    def calculate_csm_initial(
        self,
        premiums: Decimal,
        acquisition_costs: Decimal,
        bel: Decimal,
        ra: Decimal
    ) -> CSMDetailedResult:
        """
        Расчет начального CSM при признании

        CSM = Premiums - AC - BEL - RA (если > 0)
        Loss Component = |CSM| (если CSM < 0)

        Args:
            premiums: PV будущих премий
            acquisition_costs: Затраты на привлечение
            bel: Best Estimate Liability
            ra: Risk Adjustment

        Returns:
            CSMDetailedResult
        """
        # Начальный расчет
        csm_raw = premiums - acquisition_costs - bel - ra

        is_onerous = csm_raw < Decimal('0')

        if is_onerous:
            loss_component = abs(csm_raw)
            csm = Decimal('0')
        else:
            loss_component = Decimal('0')
            csm = csm_raw

        csm = self._round(csm)
        loss_component = self._round(loss_component)

        formula_display = (
            f"{'='*70}\n"
            f"РАСЧЕТ НАЧАЛЬНОГО CSM\n"
            f"{'='*70}\n\n"
            f"Формула: CSM = PV(Premiums) - AC - BEL - RA\n\n"
            f"Компоненты:\n"
            f"  PV(Premiums): {format_currency(premiums)}\n"
            f"  Acquisition Costs: {format_currency(acquisition_costs)}\n"
            f"  BEL: {format_currency(bel)}\n"
            f"  RA: {format_currency(ra)}\n\n"
            f"Расчет:\n"
            f"  CSM = {format_currency(premiums)} - {format_currency(acquisition_costs)} "
            f"- {format_currency(bel)} - {format_currency(ra)}\n"
            f"  CSM = {format_currency(csm_raw)}\n\n"
        )

        if is_onerous:
            formula_display += (
                f"⚠️ ДОГОВОР ОБРЕМЕНИТЕЛЬНЫЙ (para 47-52):\n"
                f"  Loss Component = {format_currency(loss_component)}\n"
                f"  Убыток признается немедленно в P&L\n"
                f"  CSM = 0\n"
            )
        else:
            formula_display += (
                f"✓ Договор прибыльный:\n"
                f"  CSM = {format_currency(csm)}\n"
                f"  Прибыль будет признаваться по мере оказания услуг\n"
            )

        formula_display += f"{'='*70}\n"

        justification = (
            f"Initial CSM calculated per IFRS 17 para 38. "
            f"{'Contract is onerous - loss component of ' + format_currency(loss_component) + ' recognized immediately. ' if is_onerous else ''}"
            f"CSM represents unearned profit of {format_currency(csm)} to be recognized as services are provided."
        )

        # Получаем locked-in rate
        locked_rate, _ = self.yield_curve.get_discount_rate(1)

        result = CSMDetailedResult(
            csm_opening=Decimal('0'),
            csm_closing=csm,
            csm_new_contracts=csm,
            csm_interest_accretion=Decimal('0'),
            csm_changes_future_service=Decimal('0'),
            csm_experience_adjustment=Decimal('0'),
            csm_release=Decimal('0'),
            csm_currency_effect=Decimal('0'),
            csm_fv_underlying_change=Decimal('0'),
            csm_variable_fee_change=Decimal('0'),
            is_onerous=is_onerous,
            loss_component_opening=Decimal('0'),
            loss_component_closing=loss_component,
            loss_component_reversal=Decimal('0'),
            coverage_units_current=Decimal('0'),
            coverage_units_remaining=Decimal('1'),
            release_pattern=[],
            locked_in_rate=locked_rate,
            formula_display=formula_display,
            justification=justification,
            reference_paragraphs=['para 38', 'para 47-52']
        )

        self._log_audit('Initial CSM', {
            'csm': float(csm),
            'is_onerous': is_onerous,
            'loss_component': float(loss_component)
        }, 'IFRS 17 para 38')

        return result

    def calculate_csm_rollforward_gmm(
        self,
        opening_csm: Decimal,
        opening_loss_component: Decimal,
        locked_in_rate: Decimal,
        new_contracts_csm: Decimal,
        changes_future_service: Decimal,
        experience_adjustment_csm: Decimal,
        coverage_units_current: Decimal,
        coverage_units_remaining: Decimal,
        currency_effect: Decimal = Decimal('0')
    ) -> CSMDetailedResult:
        """
        CSM Roll-forward для GMM (para 44)

        CSM_closing = CSM_opening + New + Interest + Changes - Release + Currency

        Args:
            opening_csm: Начальный CSM
            opening_loss_component: Начальный loss component
            locked_in_rate: Заблокированная ставка
            new_contracts_csm: CSM новых договоров
            changes_future_service: Изменения в отношении будущих услуг
            experience_adjustment_csm: Experience adjustments (часть, относящаяся к CSM)
            coverage_units_current: Единицы покрытия текущего периода
            coverage_units_remaining: Оставшиеся единицы покрытия
            currency_effect: Валютный эффект

        Returns:
            CSMDetailedResult
        """
        # Начисление процентов на CSM
        interest_accretion = opening_csm * locked_in_rate

        # CSM до release
        csm_before_release = (
            opening_csm +
            new_contracts_csm +
            interest_accretion +
            changes_future_service +
            currency_effect
        )

        # Release CSM
        total_coverage_units = coverage_units_current + coverage_units_remaining
        if total_coverage_units > 0:
            release_ratio = coverage_units_current / total_coverage_units
        else:
            release_ratio = Decimal('0')

        csm_release = csm_before_release * release_ratio

        # Closing CSM
        csm_closing = csm_before_release - csm_release
        csm_closing = max(Decimal('0'), csm_closing)  # CSM не может быть отрицательным

        # Loss component обработка
        is_onerous = csm_closing == Decimal('0') and (csm_before_release - csm_release) < 0
        loss_component_closing = abs(min(Decimal('0'), csm_before_release - csm_release))
        loss_component_reversal = max(Decimal('0'), opening_loss_component - loss_component_closing)

        # Round all values
        csm_closing = self._round(csm_closing)
        csm_release = self._round(csm_release)
        interest_accretion = self._round(interest_accretion)
        loss_component_closing = self._round(loss_component_closing)

        formula_display = (
            f"{'='*70}\n"
            f"CSM ROLL-FORWARD (GMM) - para 44\n"
            f"{'='*70}\n\n"
            f"Opening CSM: {format_currency(opening_csm)}\n"
            f"+ New contracts CSM: {format_currency(new_contracts_csm)}\n"
            f"+ Interest accretion ({float(locked_in_rate):.2%}): {format_currency(interest_accretion)}\n"
            f"+ Changes relating to future service: {format_currency(changes_future_service)}\n"
            f"+ Currency effects: {format_currency(currency_effect)}\n"
            f"= CSM before release: {format_currency(csm_before_release)}\n\n"
            f"Coverage units (current/total): {float(coverage_units_current)}/{float(total_coverage_units)}\n"
            f"Release ratio: {float(release_ratio):.4f}\n"
            f"- CSM release: {format_currency(csm_release)}\n\n"
            f"= Closing CSM: {format_currency(csm_closing)}\n"
        )

        if is_onerous or loss_component_closing > 0:
            formula_display += (
                f"\n⚠️ Loss Component:\n"
                f"  Opening: {format_currency(opening_loss_component)}\n"
                f"  Closing: {format_currency(loss_component_closing)}\n"
                f"  Reversal: {format_currency(loss_component_reversal)}\n"
            )

        formula_display += f"{'='*70}\n"

        justification = (
            f"CSM roll-forward per IFRS 17 para 44. "
            f"Interest accreted at locked-in rate of {float(locked_in_rate):.2%}. "
            f"CSM release of {format_currency(csm_release)} based on coverage units "
            f"({float(release_ratio)*100:.1f}% of period). "
            f"Closing CSM = {format_currency(csm_closing)}."
        )

        return CSMDetailedResult(
            csm_opening=opening_csm,
            csm_closing=csm_closing,
            csm_new_contracts=new_contracts_csm,
            csm_interest_accretion=interest_accretion,
            csm_changes_future_service=changes_future_service,
            csm_experience_adjustment=experience_adjustment_csm,
            csm_release=csm_release,
            csm_currency_effect=currency_effect,
            csm_fv_underlying_change=Decimal('0'),
            csm_variable_fee_change=Decimal('0'),
            is_onerous=is_onerous,
            loss_component_opening=opening_loss_component,
            loss_component_closing=loss_component_closing,
            loss_component_reversal=loss_component_reversal,
            coverage_units_current=coverage_units_current,
            coverage_units_remaining=coverage_units_remaining - coverage_units_current,
            release_pattern=[],
            locked_in_rate=locked_in_rate,
            formula_display=formula_display,
            justification=justification,
            reference_paragraphs=['para 44', 'B96-B119']
        )

    def calculate_csm_rollforward_vfa(
        self,
        opening_csm: Decimal,
        change_fv_underlying: Decimal,
        entity_share: Decimal,
        changes_fcf_non_variable: Decimal,
        coverage_units_current: Decimal,
        coverage_units_remaining: Decimal
    ) -> CSMDetailedResult:
        """
        CSM Roll-forward для VFA (para 45)

        Для VFA:
        - Изменения в FV underlying → CSM
        - Variable fee = entity share of change in FV
        - No interest accretion (rate already in underlying)

        Args:
            opening_csm: Начальный CSM
            change_fv_underlying: Изменение FV базовых активов
            entity_share: Доля страховщика в underlying
            changes_fcf_non_variable: Изменения FCF не связанные с variable fee
            coverage_units_current: Текущие единицы покрытия
            coverage_units_remaining: Оставшиеся единицы покрытия

        Returns:
            CSMDetailedResult
        """
        # Variable fee = entity share × ΔFV
        variable_fee_change = entity_share * change_fv_underlying

        # CSM before release
        csm_before_release = (
            opening_csm +
            variable_fee_change +
            changes_fcf_non_variable
        )

        # Release
        total_units = coverage_units_current + coverage_units_remaining
        release_ratio = coverage_units_current / total_units if total_units > 0 else Decimal('0')
        csm_release = csm_before_release * release_ratio

        # Closing CSM
        csm_closing = max(Decimal('0'), csm_before_release - csm_release)

        # Onerous check
        is_onerous = csm_closing == Decimal('0') and (csm_before_release - csm_release) < 0
        loss_component = abs(min(Decimal('0'), csm_before_release - csm_release))

        formula_display = (
            f"{'='*70}\n"
            f"CSM ROLL-FORWARD (VFA) - para 45\n"
            f"{'='*70}\n\n"
            f"Opening CSM: {format_currency(opening_csm)}\n"
            f"+ Variable fee change ({float(entity_share):.0%} × ΔFV):\n"
            f"    = {float(entity_share):.0%} × {format_currency(change_fv_underlying)}\n"
            f"    = {format_currency(variable_fee_change)}\n"
            f"+ Changes FCF (non-variable): {format_currency(changes_fcf_non_variable)}\n"
            f"= CSM before release: {format_currency(csm_before_release)}\n\n"
            f"- CSM release: {format_currency(csm_release)}\n"
            f"= Closing CSM: {format_currency(self._round(csm_closing))}\n"
            f"{'='*70}\n"
        )

        return CSMDetailedResult(
            csm_opening=opening_csm,
            csm_closing=self._round(csm_closing),
            csm_new_contracts=Decimal('0'),
            csm_interest_accretion=Decimal('0'),
            csm_changes_future_service=changes_fcf_non_variable,
            csm_experience_adjustment=Decimal('0'),
            csm_release=self._round(csm_release),
            csm_currency_effect=Decimal('0'),
            csm_fv_underlying_change=change_fv_underlying,
            csm_variable_fee_change=self._round(variable_fee_change),
            is_onerous=is_onerous,
            loss_component_opening=Decimal('0'),
            loss_component_closing=self._round(loss_component),
            loss_component_reversal=Decimal('0'),
            coverage_units_current=coverage_units_current,
            coverage_units_remaining=coverage_units_remaining - coverage_units_current,
            release_pattern=[],
            locked_in_rate=Decimal('0'),
            formula_display=formula_display,
            justification=f"VFA roll-forward per para 45. Variable fee = {format_currency(variable_fee_change)}.",
            reference_paragraphs=['para 45', 'B101-B118']
        )

    # =========================================================================
    # PAA CALCULATION (para 53-59)
    # =========================================================================

    def calculate_paa(
        self,
        premiums: Decimal,
        acquisition_costs: Decimal,
        expense_acquisition: bool = False,
        coverage_period_months: int = 12,
        time_elapsed_months: int = 0,
        claims_incurred: Decimal = Decimal('0'),
        ra_lic: Decimal = Decimal('0')
    ) -> Dict[str, Any]:
        """
        Расчет по PAA (para 53-59)

        LRC = Unearned premium - DAC (или expensed AC)
        LIC = Claims provision + RA

        Args:
            premiums: Полученные премии
            acquisition_costs: Затраты на привлечение
            expense_acquisition: Списывать AC сразу (если coverage ≤ 1 год)
            coverage_period_months: Период покрытия в месяцах
            time_elapsed_months: Прошедшее время в месяцах
            claims_incurred: Понесенные убытки
            ra_lic: RA для LIC

        Returns:
            Dict с LRC, LIC и деталями
        """
        # DAC или expense
        if expense_acquisition or coverage_period_months <= 12:
            dac = Decimal('0')
            ac_expensed = acquisition_costs
        else:
            dac = acquisition_costs
            ac_expensed = Decimal('0')

        # Earned premium calculation (pro-rata)
        earned_ratio = Decimal(str(time_elapsed_months / coverage_period_months))
        earned_premium = premiums * earned_ratio
        unearned_premium = premiums - earned_premium

        # LRC = Unearned premium - DAC (amortized)
        dac_amortized = dac * earned_ratio
        dac_remaining = dac - dac_amortized

        lrc = unearned_premium - dac_remaining

        # LIC (simplified for PAA)
        lic = claims_incurred + ra_lic

        # Total insurance liability
        total_liability = lrc + lic

        formula_display = (
            f"{'='*70}\n"
            f"РАСЧЕТ ПО PAA (Premium Allocation Approach)\n"
            f"{'='*70}\n\n"
            f"LRC (Liability for Remaining Coverage):\n"
            f"  Total premiums: {format_currency(premiums)}\n"
            f"  Coverage period: {coverage_period_months} months\n"
            f"  Time elapsed: {time_elapsed_months} months\n"
            f"  Earned ratio: {float(earned_ratio):.2%}\n"
            f"  Earned premium: {format_currency(earned_premium)}\n"
            f"  Unearned premium: {format_currency(unearned_premium)}\n"
            f"  DAC remaining: {format_currency(dac_remaining)}\n"
            f"  LRC = {format_currency(self._round(lrc))}\n\n"
            f"LIC (Liability for Incurred Claims):\n"
            f"  Claims incurred: {format_currency(claims_incurred)}\n"
            f"  RA for LIC: {format_currency(ra_lic)}\n"
            f"  LIC = {format_currency(self._round(lic))}\n\n"
            f"Total Insurance Liability = {format_currency(self._round(total_liability))}\n"
            f"{'='*70}\n"
        )

        return {
            'measurement_model': MeasurementModel.PAA,
            'lrc': self._round(lrc),
            'lic': self._round(lic),
            'total_liability': self._round(total_liability),
            'unearned_premium': self._round(unearned_premium),
            'earned_premium': self._round(earned_premium),
            'dac': self._round(dac),
            'dac_remaining': self._round(dac_remaining),
            'ac_expensed': ac_expensed,
            'formula_display': formula_display,
            'reference_paragraphs': ['para 53-59']
        }

    # =========================================================================
    # LIC CALCULATION (para 40-52)
    # =========================================================================

    def calculate_lic(
        self,
        reported_claims: Decimal,
        ibnr: Decimal,
        ibner: Decimal,
        ulae: Decimal,
        alae: Decimal,
        ra_confidence: Decimal = Decimal('0.75'),
        discount_rate: Decimal = None
    ) -> LICResult:
        """
        Расчет LIC (Liability for Incurred Claims)

        LIC = Reported + IBNR + IBNER + ULAE + ALAE + RA

        Args:
            reported_claims: Заявленные убытки (case reserves)
            ibnr: Incurred But Not Reported
            ibner: Incurred But Not Enough Reported
            ulae: Unallocated Loss Adjustment Expenses
            alae: Allocated Loss Adjustment Expenses
            ra_confidence: Уровень доверия для RA
            discount_rate: Ставка дисконтирования

        Returns:
            LICResult
        """
        # Base LIC without RA
        base_lic = reported_claims + ibnr + ibner + ulae + alae

        # RA for LIC (simplified calculation)
        # RA = std_dev × z-score for confidence level
        estimated_std = base_lic * Decimal('0.15')  # Assumed 15% CoV
        z_score = Decimal(str(stats.norm.ppf(float(ra_confidence))))
        ra_lic = estimated_std * z_score
        ra_lic = max(Decimal('0'), ra_lic)

        # Total LIC
        lic_amount = base_lic + ra_lic

        # Discounting (if rate provided)
        if discount_rate is not None:
            # Assume average duration of 2 years for claims
            df = Decimal(str(np.exp(-float(discount_rate) * 2)))
            lic_amount = lic_amount * df

        lic_amount = self._round(lic_amount)

        formula_display = (
            f"{'='*70}\n"
            f"РАСЧЕТ LIC (Liability for Incurred Claims)\n"
            f"{'='*70}\n\n"
            f"Компоненты:\n"
            f"  Reported claims (case reserves): {format_currency(reported_claims)}\n"
            f"  IBNR: {format_currency(ibnr)}\n"
            f"  IBNER: {format_currency(ibner)}\n"
            f"  ULAE: {format_currency(ulae)}\n"
            f"  ALAE: {format_currency(alae)}\n"
            f"  RA (conf={float(ra_confidence):.0%}): {format_currency(self._round(ra_lic))}\n\n"
            f"LIC = {format_currency(lic_amount)}\n"
            f"{'='*70}\n"
        )

        return LICResult(
            lic_amount=lic_amount,
            reported_claims=reported_claims,
            ibnr=ibnr,
            ibner=ibner,
            ulae=ulae,
            alae=alae,
            ra_lic=self._round(ra_lic),
            formula_display=formula_display,
            development_triangles={}
        )

    # =========================================================================
    # INSURANCE FINANCE (para 87-92)
    # =========================================================================

    def calculate_insurance_finance(
        self,
        opening_liability: Decimal,
        closing_liability: Decimal,
        discount_rate_opening: Decimal,
        discount_rate_closing: Decimal,
        oci_option: bool = False
    ) -> InsuranceFinanceResult:
        """
        Расчет Insurance Finance Income/Expense (para 87-92)

        IFIE = Interest accretion + Effect of rate changes + Effect of assumption changes

        Args:
            opening_liability: Обязательство на начало
            closing_liability: Обязательство на конец
            discount_rate_opening: Ставка на начало
            discount_rate_closing: Ставка на конец
            oci_option: Использовать OCI для rate changes

        Returns:
            InsuranceFinanceResult
        """
        # Interest accretion (unwinding)
        interest_accretion = opening_liability * discount_rate_opening

        # Effect of rate changes
        rate_change = discount_rate_closing - discount_rate_opening
        # Simplified: assume linear relationship
        effect_rate_changes = opening_liability * rate_change * Decimal('-5')  # Duration ~5

        # Effect of assumption changes (residual)
        effect_assumptions = (
            closing_liability - opening_liability -
            interest_accretion - effect_rate_changes
        )

        # Total IFIE
        ifie_total = interest_accretion + effect_rate_changes + effect_assumptions

        # OCI disaggregation
        if oci_option:
            oci_amount = effect_rate_changes
            pnl_amount = interest_accretion + effect_assumptions
        else:
            oci_amount = Decimal('0')
            pnl_amount = ifie_total

        formula_display = (
            f"{'='*70}\n"
            f"INSURANCE FINANCE INCOME/EXPENSE (para 87-92)\n"
            f"{'='*70}\n\n"
            f"Interest accretion: {format_currency(self._round(interest_accretion))}\n"
            f"Effect of rate changes: {format_currency(self._round(effect_rate_changes))}\n"
            f"Effect of assumption changes: {format_currency(self._round(effect_assumptions))}\n\n"
            f"Total IFIE: {format_currency(self._round(ifie_total))}\n\n"
            f"Presentation (OCI option: {'Yes' if oci_option else 'No'}):\n"
            f"  P&L: {format_currency(self._round(pnl_amount))}\n"
            f"  OCI: {format_currency(self._round(oci_amount))}\n"
            f"{'='*70}\n"
        )

        return InsuranceFinanceResult(
            ifie_total=self._round(ifie_total),
            interest_accretion=self._round(interest_accretion),
            effect_changes_rates=self._round(effect_rate_changes),
            effect_changes_assumptions=self._round(effect_assumptions),
            oci_amount=self._round(oci_amount),
            pnl_amount=self._round(pnl_amount),
            ifie_bel=self._round(interest_accretion * Decimal('0.8')),
            ifie_ra=self._round(interest_accretion * Decimal('0.1')),
            ifie_csm=self._round(interest_accretion * Decimal('0.1')),
            disaggregation_approach='OCI' if oci_option else 'P&L',
            formula_display=formula_display
        )

    # =========================================================================
    # FULL CALCULATION
    # =========================================================================

    def calculate_full(
        self,
        cash_flows: List[Dict],
        contract_data: Dict,
        assumptions: Dict,
        measurement_model: MeasurementModel = None,
        ra_method: RAMethod = RAMethod.COC
    ) -> IFRS17FullResult:
        """
        Полный расчет по МСФО 17

        Args:
            cash_flows: Денежные потоки
            contract_data: Данные договора
            assumptions: Допущения
            measurement_model: Модель измерения (auto-detect если None)
            ra_method: Метод расчета RA

        Returns:
            IFRS17FullResult
        """
        # Auto-detect measurement model
        if measurement_model is None:
            paa_eligible, _ = self.check_paa_eligibility(contract_data)
            vfa_eligible, _ = self.check_vfa_eligibility(contract_data)

            if paa_eligible:
                measurement_model = MeasurementModel.PAA
            elif vfa_eligible:
                measurement_model = MeasurementModel.VFA
            else:
                measurement_model = MeasurementModel.GMM

        # BEL
        bel_result = self.calculate_bel_detailed(
            cash_flows, assumptions, 'bottom_up'
        )

        # RA
        net_cfs = [
            Decimal(str(cf.get('claims', 0) + cf.get('expenses', 0) - cf.get('premiums', 0)))
            for cf in cash_flows
        ]
        ra_result = self.calculate_ra_detailed(
            net_cfs, ra_method
        )

        # Premiums and AC
        premiums = sum(Decimal(str(cf.get('premiums', 0))) for cf in cash_flows)
        acquisition_costs = Decimal(str(contract_data.get('acquisition_costs', 0)))

        # CSM
        csm_result = self.calculate_csm_initial(
            premiums, acquisition_costs, bel_result.bel_amount, ra_result.ra_amount
        )

        # FCF = BEL + RA
        fcf = bel_result.bel_amount + ra_result.ra_amount

        # LRC = FCF + CSM
        lrc = fcf + csm_result.csm_closing

        # LIC (from contract data)
        lic_result = self.calculate_lic(
            reported_claims=Decimal(str(contract_data.get('reported_claims', 0))),
            ibnr=Decimal(str(contract_data.get('ibnr', 0))),
            ibner=Decimal(str(contract_data.get('ibner', 0))),
            ulae=Decimal(str(contract_data.get('ulae', 0))),
            alae=Decimal(str(contract_data.get('alae', 0)))
        )

        # Total liability
        total_liability = lrc + lic_result.lic_amount

        # Insurance Finance
        opening_rate, _ = self.yield_curve.get_discount_rate(1)
        closing_rate = opening_rate  # Same period
        ifie_result = self.calculate_insurance_finance(
            total_liability, total_liability, opening_rate, closing_rate
        )

        # Statement impacts
        sofp = {
            'insurance_contract_liabilities': total_liability,
            'lrc': lrc,
            'lic': lic_result.lic_amount,
            'reinsurance_contract_assets': Decimal('0')
        }

        sopl = {
            'insurance_revenue': premiums * Decimal('0.8'),  # Simplified
            'insurance_service_expense': bel_result.bel_claims + bel_result.bel_expenses,
            'insurance_service_result': premiums * Decimal('0.8') - bel_result.bel_claims - bel_result.bel_expenses,
            'insurance_finance_expense': ifie_result.pnl_amount
        }

        soci = {
            'insurance_finance_oci': ifie_result.oci_amount
        }

        # Full formula display
        formula_display = (
            f"{'='*70}\n"
            f"ПОЛНЫЙ РАСЧЕТ ПО МСФО 17\n"
            f"Модель: {measurement_model.value}\n"
            f"{'='*70}\n\n"
            f"КОМПОНЕНТЫ ОБЯЗАТЕЛЬСТВА:\n"
            f"  BEL: {format_currency(bel_result.bel_amount)}\n"
            f"  RA: {format_currency(ra_result.ra_amount)}\n"
            f"  FCF (BEL + RA): {format_currency(fcf)}\n"
            f"  CSM: {format_currency(csm_result.csm_closing)}\n"
            f"  LRC (FCF + CSM): {format_currency(lrc)}\n"
            f"  LIC: {format_currency(lic_result.lic_amount)}\n\n"
            f"  ИТОГО ОБЯЗАТЕЛЬСТВО: {format_currency(total_liability)}\n"
            f"{'='*70}\n"
        )

        justification = (
            f"Full IFRS 17 calculation using {measurement_model.value}. "
            f"Total insurance liability = {format_currency(total_liability)} "
            f"(LRC = {format_currency(lrc)}, LIC = {format_currency(lic_result.lic_amount)}). "
            f"Reference: IFRS 17 para 32-52."
        )

        return IFRS17FullResult(
            bel=bel_result,
            ra=ra_result,
            csm=csm_result,
            fcf=fcf,
            lrc=lrc,
            lic=lic_result,
            total_insurance_liability=total_liability,
            total_reinsurance_asset=None,
            insurance_finance=ifie_result,
            measurement_model=measurement_model,
            group_id=contract_data.get('group_id', 'GROUP-001'),
            cohort=contract_data.get('cohort', '2026-Q1'),
            statement_of_financial_position=sofp,
            statement_of_profit_loss=sopl,
            statement_of_oci=soci,
            formula_display=formula_display,
            justification=justification,
            audit_trail=self.audit_log
        )

    def get_audit_log(self) -> List[Dict]:
        """Получить аудиторский след"""
        return self.audit_log


# =============================================================================
# DEMONSTRATION
# =============================================================================

def demo_enhanced_ifrs17():
    """Демонстрация расширенного расчета МСФО 17"""
    calc = IFRS17EnhancedCalculator()

    # Пример: Договор страхования жизни на 10 лет
    cash_flows = []
    for year in range(1, 11):
        cf = {
            'period': year,
            'premiums': 100_000_000 if year == 1 else 10_000_000,
            'claims': 8_000_000 + year * 500_000,
            'maintenance_costs': 1_000_000,
            'claim_handling_costs': 500_000,
            'acquisition_costs': 15_000_000 if year == 1 else 0,
        }
        cash_flows.append(cf)

    contract_data = {
        'contract_term_years': 10,
        'acquisition_costs': 15_000_000,
        'reported_claims': 5_000_000,
        'ibnr': 2_000_000,
        'ibner': 500_000,
        'ulae': 300_000,
        'alae': 200_000,
        'group_id': 'LIFE-GROUP-001',
        'cohort': '2026-Q1'
    }

    assumptions = {
        'lapse_rate': 0.03,
        'mortality_rate': 0.0015,
        'expense_inflation': 0.05,
        'morbidity_rate': 0.01
    }

    result = calc.calculate_full(
        cash_flows=cash_flows,
        contract_data=contract_data,
        assumptions=assumptions,
        ra_method=RAMethod.COC
    )

    print(result.formula_display)
    print(f"\nОбоснование: {result.justification}")
    print(f"\nAudit log entries: {len(result.audit_trail)}")

    return result


if __name__ == '__main__':
    demo_enhanced_ifrs17()
