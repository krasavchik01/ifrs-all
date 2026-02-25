# -*- coding: utf-8 -*-
"""
Alliot - Модуль регуляторной отчётности для АРРФР
Постановления №85, №86, №304

Полное соответствие требованиям Агентства по регулированию
и развитию финансового рынка Республики Казахстан (АРРФР)
"""

from dataclasses import dataclass, field
from decimal import Decimal
from datetime import date, datetime
from typing import List, Dict, Optional, Any
from enum import Enum
import json


# =============================================================================
# ПОСТАНОВЛЕНИЕ №85 - Об утверждении форм отчётности страховых организаций
# =============================================================================

class ReportFrequency(Enum):
    """Периодичность сдачи отчётности"""
    DAILY = 'daily'           # Ежедневно
    WEEKLY = 'weekly'         # Еженедельно
    MONTHLY = 'monthly'       # Ежемесячно
    QUARTERLY = 'quarterly'   # Ежеквартально
    SEMI_ANNUAL = 'semi_annual'  # Полугодовой
    ANNUAL = 'annual'         # Ежегодно


class ReportStatus(Enum):
    """Статус отчёта"""
    DRAFT = 'draft'           # Черновик
    PENDING = 'pending'       # На проверке
    SUBMITTED = 'submitted'   # Отправлен
    ACCEPTED = 'accepted'     # Принят АРРФР
    REJECTED = 'rejected'     # Отклонён
    CORRECTED = 'corrected'   # Корректировка


@dataclass
class RegulatoryReportForm:
    """Базовая форма регуляторной отчётности"""
    form_code: str           # Код формы (например "01-СК")
    form_name: str           # Название формы
    form_name_kz: str        # Название на казахском
    regulation_number: str   # Номер постановления (85, 86, 304)
    frequency: ReportFrequency
    deadline_days: int       # Срок сдачи (дней после отчётной даты)
    description: str = ""
    is_mandatory: bool = True


# Формы по Постановлению №85
FORMS_REGULATION_85 = [
    RegulatoryReportForm(
        form_code="01-СК",
        form_name="Бухгалтерский баланс страховой организации",
        form_name_kz="Сақтандыру ұйымының бухгалтерлік балансы",
        regulation_number="85",
        frequency=ReportFrequency.QUARTERLY,
        deadline_days=25,
        description="Активы, обязательства и собственный капитал"
    ),
    RegulatoryReportForm(
        form_code="02-СК",
        form_name="Отчёт о прибылях и убытках страховой организации",
        form_name_kz="Сақтандыру ұйымының пайда мен залалдар туралы есебі",
        regulation_number="85",
        frequency=ReportFrequency.QUARTERLY,
        deadline_days=25,
        description="Доходы, расходы, финансовый результат"
    ),
    RegulatoryReportForm(
        form_code="03-СК",
        form_name="Отчёт о движении денежных средств",
        form_name_kz="Ақша қаражаттарының қозғалысы туралы есеп",
        regulation_number="85",
        frequency=ReportFrequency.QUARTERLY,
        deadline_days=25,
        description="Операционная, инвестиционная, финансовая деятельность"
    ),
    RegulatoryReportForm(
        form_code="04-СК",
        form_name="Отчёт о страховых премиях и выплатах",
        form_name_kz="Сақтандыру сыйлықақылары мен төлемдері туралы есеп",
        regulation_number="85",
        frequency=ReportFrequency.MONTHLY,
        deadline_days=15,
        description="Премии по классам, выплаты, резервы"
    ),
    RegulatoryReportForm(
        form_code="05-СК",
        form_name="Отчёт о страховых резервах",
        form_name_kz="Сақтандыру резервтері туралы есеп",
        regulation_number="85",
        frequency=ReportFrequency.QUARTERLY,
        deadline_days=25,
        description="РНПП, РЗУ, РПНУ, РПЗУ, стаб. резерв"
    ),
    RegulatoryReportForm(
        form_code="06-СК",
        form_name="Отчёт о перестраховочных операциях",
        form_name_kz="Қайта сақтандыру операциялары туралы есеп",
        regulation_number="85",
        frequency=ReportFrequency.QUARTERLY,
        deadline_days=25,
        description="Входящее/исходящее перестрахование"
    ),
    RegulatoryReportForm(
        form_code="07-СК",
        form_name="Отчёт об инвестиционной деятельности",
        form_name_kz="Инвестициялық қызмет туралы есеп",
        regulation_number="85",
        frequency=ReportFrequency.QUARTERLY,
        deadline_days=25,
        description="Структура инвестиций, доходность"
    ),
    RegulatoryReportForm(
        form_code="08-СК",
        form_name="Отчёт о собственном капитале",
        form_name_kz="Меншікті капитал туралы есеп",
        regulation_number="85",
        frequency=ReportFrequency.QUARTERLY,
        deadline_days=25,
        description="Движение собственного капитала"
    ),
    RegulatoryReportForm(
        form_code="09-СК",
        form_name="Отчёт об обязательном страховании",
        form_name_kz="Міндетті сақтандыру туралы есеп",
        regulation_number="85",
        frequency=ReportFrequency.MONTHLY,
        deadline_days=15,
        description="ОГПО ВТС, ОГПО владельцев опасных объектов"
    ),
    RegulatoryReportForm(
        form_code="10-СК",
        form_name="Сведения о крупных рисках",
        form_name_kz="Ірі тәуекелдер туралы мәліметтер",
        regulation_number="85",
        frequency=ReportFrequency.QUARTERLY,
        deadline_days=25,
        description="Концентрация рисков > 10% капитала"
    ),
]


# =============================================================================
# ПОСТАНОВЛЕНИЕ №86 - Требования к платёжеспособности (маржа/норматив)
# =============================================================================

@dataclass
class SolvencyReportData:
    """Данные отчёта о платёжеспособности по П.№86"""
    reporting_date: date

    # Фактическая маржа платёжеспособности (ФМП)
    equity_capital: Decimal = Decimal('0')           # Собственный капитал
    subordinated_debt: Decimal = Decimal('0')        # Субординированный долг (до 50% от ФМП)
    intangible_assets: Decimal = Decimal('0')        # Нематериальные активы (-)
    deferred_acquisition_costs: Decimal = Decimal('0')  # Отложенные аквизиционные расходы (-)
    fmp_calculated: Decimal = Decimal('0')           # Рассчитанная ФМП

    # Нормативная маржа платёжеспособности (НМП)
    premium_base: Decimal = Decimal('0')             # База по премиям
    claims_base: Decimal = Decimal('0')              # База по убыткам
    nmp_by_premiums: Decimal = Decimal('0')          # НМП по премиям
    nmp_by_claims: Decimal = Decimal('0')            # НМП по убыткам
    nmp_calculated: Decimal = Decimal('0')           # Итоговая НМП (max)

    # Коэффициент платёжеспособности
    solvency_ratio: Decimal = Decimal('0')           # ФМП / НМП (должен быть >= 1.0)

    # Для страхования жизни
    life_technical_reserves: Decimal = Decimal('0')  # Технические резервы (жизнь)
    nmp_life: Decimal = Decimal('0')                 # НМП для жизни (4% от резервов)

    # Минимальный гарантийный фонд (МГФ)
    mgf_required: Decimal = Decimal('0')             # Требуемый МГФ
    mgf_actual: Decimal = Decimal('0')               # Фактический МГФ

    # Статус
    is_compliant: bool = True
    violations: List[str] = field(default_factory=list)


FORMS_REGULATION_86 = [
    RegulatoryReportForm(
        form_code="01-ПЛ",
        form_name="Расчёт фактической маржи платёжеспособности",
        form_name_kz="Төлем қабілеттілігінің нақты маржасын есептеу",
        regulation_number="86",
        frequency=ReportFrequency.MONTHLY,
        deadline_days=10,
        description="Собственный капитал, корректировки"
    ),
    RegulatoryReportForm(
        form_code="02-ПЛ",
        form_name="Расчёт нормативной маржи платёжеспособности",
        form_name_kz="Төлем қабілеттілігінің нормативтік маржасын есептеу",
        regulation_number="86",
        frequency=ReportFrequency.MONTHLY,
        deadline_days=10,
        description="По премиям и по убыткам"
    ),
    RegulatoryReportForm(
        form_code="03-ПЛ",
        form_name="Расчёт минимального гарантийного фонда",
        form_name_kz="Ең төменгі кепілдік қорын есептеу",
        regulation_number="86",
        frequency=ReportFrequency.QUARTERLY,
        deadline_days=25,
        description="МГФ = 1/3 от НМП, но не менее минимума"
    ),
    RegulatoryReportForm(
        form_code="04-ПЛ",
        form_name="Сводный отчёт о платёжеспособности",
        form_name_kz="Төлем қабілеттілігі туралы жиынтық есеп",
        regulation_number="86",
        frequency=ReportFrequency.MONTHLY,
        deadline_days=10,
        description="ФМП, НМП, коэффициент, МГФ"
    ),
]


# =============================================================================
# ПОСТАНОВЛЕНИЕ №304 - Правила формирования страховых резервов
# =============================================================================

class ReserveType(Enum):
    """Виды страховых резервов по П.№304"""
    RNPP = 'rnpp'    # Резерв незаработанной премии (РНП)
    RZU = 'rzu'      # Резерв заявленных, но неурегулированных убытков (РЗУ)
    RPNU = 'rpnu'    # Резерв произошедших, но незаявленных убытков (РПНУ/IBNR)
    RPZU = 'rpzu'    # Резерв расходов на урегулирование убытков (РПЗУ)
    STAB = 'stab'    # Стабилизационный резерв

    # Для страхования жизни
    MR = 'mr'        # Математический резерв
    RUV = 'ruv'      # Резерв участия в прибыли


@dataclass
class ReserveCalculation:
    """Расчёт страхового резерва"""
    reserve_type: ReserveType
    calculation_date: date
    insurance_class: str      # Класс страхования

    # Входные данные
    gross_amount: Decimal = Decimal('0')     # Брутто-сумма
    reinsurance_share: Decimal = Decimal('0')  # Доля перестраховщиков
    net_amount: Decimal = Decimal('0')       # Нетто-сумма

    # Метод расчёта
    calculation_method: str = ""             # Метод (pro-rata, 1/365, chain-ladder, etc.)

    # Параметры
    parameters: Dict[str, Any] = field(default_factory=dict)

    # Результат
    reserve_amount: Decimal = Decimal('0')

    # Формула
    formula_display: str = ""
    justification: str = ""


@dataclass
class ReservesReport:
    """Сводный отчёт о страховых резервах по П.№304"""
    reporting_date: date
    reporting_period: str   # "Q1 2025", "2024" etc.

    # Резервы по общему страхованию
    rnpp_gross: Decimal = Decimal('0')
    rnpp_reinsurance: Decimal = Decimal('0')
    rnpp_net: Decimal = Decimal('0')

    rzu_gross: Decimal = Decimal('0')
    rzu_reinsurance: Decimal = Decimal('0')
    rzu_net: Decimal = Decimal('0')

    rpnu_gross: Decimal = Decimal('0')
    rpnu_reinsurance: Decimal = Decimal('0')
    rpnu_net: Decimal = Decimal('0')

    rpzu_amount: Decimal = Decimal('0')

    stab_reserve: Decimal = Decimal('0')

    # Резервы по страхованию жизни
    math_reserve: Decimal = Decimal('0')
    profit_participation_reserve: Decimal = Decimal('0')

    # Итого
    total_reserves_gross: Decimal = Decimal('0')
    total_reserves_net: Decimal = Decimal('0')

    # Активы, покрывающие резервы
    covering_assets: Decimal = Decimal('0')
    coverage_ratio: Decimal = Decimal('0')  # Должен быть >= 100%

    # Детализация по классам
    by_class: Dict[str, Dict[str, Decimal]] = field(default_factory=dict)


FORMS_REGULATION_304 = [
    RegulatoryReportForm(
        form_code="01-РЗ",
        form_name="Расчёт резерва незаработанной премии (РНП)",
        form_name_kz="Еңбексіз сыйлықақы резервін есептеу (РНП)",
        regulation_number="304",
        frequency=ReportFrequency.QUARTERLY,
        deadline_days=25,
        description="Метод pro-rata temporis или 1/365"
    ),
    RegulatoryReportForm(
        form_code="02-РЗ",
        form_name="Расчёт резерва заявленных убытков (РЗУ)",
        form_name_kz="Мәлімделген залалдар резервін есептеу (РЗУ)",
        regulation_number="304",
        frequency=ReportFrequency.QUARTERLY,
        deadline_days=25,
        description="Индивидуальная оценка по каждому убытку"
    ),
    RegulatoryReportForm(
        form_code="03-РЗ",
        form_name="Расчёт резерва IBNR (РПНУ)",
        form_name_kz="IBNR резервін есептеу (РПНУ)",
        regulation_number="304",
        frequency=ReportFrequency.QUARTERLY,
        deadline_days=25,
        description="Chain-Ladder, Bornhuetter-Ferguson"
    ),
    RegulatoryReportForm(
        form_code="04-РЗ",
        form_name="Расчёт резерва расходов на урегулирование (РПЗУ)",
        form_name_kz="Реттеу шығындары резервін есептеу (РПЗУ)",
        regulation_number="304",
        frequency=ReportFrequency.QUARTERLY,
        deadline_days=25,
        description="% от РЗУ + РПНУ"
    ),
    RegulatoryReportForm(
        form_code="05-РЗ",
        form_name="Расчёт стабилизационного резерва",
        form_name_kz="Тұрақтандыру резервін есептеу",
        regulation_number="304",
        frequency=ReportFrequency.ANNUAL,
        deadline_days=45,
        description="Для катастрофических рисков"
    ),
    RegulatoryReportForm(
        form_code="06-РЗ",
        form_name="Сводный отчёт о страховых резервах",
        form_name_kz="Сақтандыру резервтері туралы жиынтық есеп",
        regulation_number="304",
        frequency=ReportFrequency.QUARTERLY,
        deadline_days=25,
        description="Все резервы, покрытие активами"
    ),
    RegulatoryReportForm(
        form_code="07-РЗ",
        form_name="Математический резерв (страхование жизни)",
        form_name_kz="Математикалық резерв (өмірді сақтандыру)",
        regulation_number="304",
        frequency=ReportFrequency.QUARTERLY,
        deadline_days=25,
        description="Prospective/Retrospective метод"
    ),
]


# =============================================================================
# СЕРВИС РЕГУЛЯТОРНОЙ ОТЧЁТНОСТИ
# =============================================================================

class RegulatoryReportService:
    """Сервис для работы с регуляторной отчётностью"""

    def __init__(self):
        self.all_forms = FORMS_REGULATION_85 + FORMS_REGULATION_86 + FORMS_REGULATION_304

    def get_forms_by_regulation(self, regulation_number: str) -> List[RegulatoryReportForm]:
        """Получить формы по номеру постановления"""
        return [f for f in self.all_forms if f.regulation_number == regulation_number]

    def get_forms_by_frequency(self, frequency: ReportFrequency) -> List[RegulatoryReportForm]:
        """Получить формы по периодичности"""
        return [f for f in self.all_forms if f.frequency == frequency]

    def get_upcoming_deadlines(self, reference_date: date) -> List[Dict]:
        """Получить ближайшие дедлайны сдачи отчётности"""
        deadlines = []
        for form in self.all_forms:
            # Расчёт дедлайна в зависимости от периодичности
            if form.frequency == ReportFrequency.MONTHLY:
                # Дедлайн = N дней после конца месяца
                from datetime import timedelta
                import calendar
                last_day = calendar.monthrange(reference_date.year, reference_date.month)[1]
                period_end = date(reference_date.year, reference_date.month, last_day)
                deadline = period_end + timedelta(days=form.deadline_days)
            elif form.frequency == ReportFrequency.QUARTERLY:
                # Дедлайн = N дней после конца квартала
                from datetime import timedelta
                quarter = (reference_date.month - 1) // 3 + 1
                quarter_end_month = quarter * 3
                import calendar
                last_day = calendar.monthrange(reference_date.year, quarter_end_month)[1]
                period_end = date(reference_date.year, quarter_end_month, last_day)
                deadline = period_end + timedelta(days=form.deadline_days)
            else:
                continue

            deadlines.append({
                'form_code': form.form_code,
                'form_name': form.form_name,
                'regulation': f"П.№{form.regulation_number}",
                'deadline': deadline,
                'days_remaining': (deadline - reference_date).days
            })

        # Сортируем по дате дедлайна
        return sorted(deadlines, key=lambda x: x['deadline'])

    def calculate_solvency_margin(
        self,
        equity_capital: Decimal,
        subordinated_debt: Decimal,
        intangible_assets: Decimal,
        deferred_acquisition_costs: Decimal,
        gross_premiums_written: Decimal,
        gross_claims_paid: Decimal,
        reinsurance_ceded_ratio: Decimal,  # Доля перестрахования (0-1)
        insurance_type: str = 'non_life'
    ) -> SolvencyReportData:
        """
        Расчёт платёжеспособности по Постановлению №86

        ФМП = Собственный капитал + Субординированный долг (до 50%) - НМА - DAC
        НМП = max(НМП по премиям, НМП по убыткам)
        Коэффициент = ФМП / НМП >= 1.0
        """
        result = SolvencyReportData(reporting_date=date.today())

        # Расчёт ФМП
        # Субординированный долг - не более 50% от собственного капитала
        max_subordinated = equity_capital * Decimal('0.5')
        adjusted_subordinated = min(subordinated_debt, max_subordinated)

        result.equity_capital = equity_capital
        result.subordinated_debt = adjusted_subordinated
        result.intangible_assets = intangible_assets
        result.deferred_acquisition_costs = deferred_acquisition_costs

        result.fmp_calculated = (
            equity_capital +
            adjusted_subordinated -
            intangible_assets -
            deferred_acquisition_costs
        )

        # Расчёт НМП для общего страхования
        if insurance_type == 'non_life':
            # По премиям: 18% от первых 200 млн + 16% от превышения
            threshold = Decimal('200000000')  # 200 млн тенге
            if gross_premiums_written <= threshold:
                nmp_premiums_gross = gross_premiums_written * Decimal('0.18')
            else:
                nmp_premiums_gross = (
                    threshold * Decimal('0.18') +
                    (gross_premiums_written - threshold) * Decimal('0.16')
                )

            # По убыткам: 26% от первых 140 млн + 23% от превышения
            claims_threshold = Decimal('140000000')  # 140 млн тенге
            if gross_claims_paid <= claims_threshold:
                nmp_claims_gross = gross_claims_paid * Decimal('0.26')
            else:
                nmp_claims_gross = (
                    claims_threshold * Decimal('0.26') +
                    (gross_claims_paid - claims_threshold) * Decimal('0.23')
                )

            # Корректировка на перестрахование (не менее 50%)
            retention_ratio = max(Decimal('1') - reinsurance_ceded_ratio, Decimal('0.5'))

            result.nmp_by_premiums = nmp_premiums_gross * retention_ratio
            result.nmp_by_claims = nmp_claims_gross * retention_ratio
            result.nmp_calculated = max(result.nmp_by_premiums, result.nmp_by_claims)

        else:  # life insurance
            # Для страхования жизни: 4% от технических резервов
            result.nmp_life = result.life_technical_reserves * Decimal('0.04')
            result.nmp_calculated = result.nmp_life

        # Коэффициент платёжеспособности
        if result.nmp_calculated > 0:
            result.solvency_ratio = result.fmp_calculated / result.nmp_calculated

        # Минимальный гарантийный фонд
        # МГФ = 1/3 от НМП, но не менее установленного минимума
        mgf_from_nmp = result.nmp_calculated / Decimal('3')

        # Минимум МГФ зависит от типа лицензии (упрощённо)
        if insurance_type == 'life':
            mgf_minimum = Decimal('5000000000')  # 5 млрд для life
        else:
            mgf_minimum = Decimal('3000000000')  # 3 млрд для non-life

        result.mgf_required = max(mgf_from_nmp, mgf_minimum)
        result.mgf_actual = result.fmp_calculated

        # Проверка соответствия
        result.violations = []
        if result.solvency_ratio < Decimal('1.0'):
            result.is_compliant = False
            result.violations.append(
                f"Коэффициент платёжеспособности {result.solvency_ratio:.2f} < 1.0"
            )
        if result.mgf_actual < result.mgf_required:
            result.is_compliant = False
            result.violations.append(
                f"МГФ {result.mgf_actual:,.0f} < требуемого {result.mgf_required:,.0f}"
            )

        return result

    def calculate_rnpp(
        self,
        premium_amount: Decimal,
        inception_date: date,
        expiry_date: date,
        calculation_date: date,
        method: str = 'pro_rata'  # 'pro_rata' или '1_365'
    ) -> ReserveCalculation:
        """
        Расчёт резерва незаработанной премии (РНП) по П.№304

        Метод pro-rata temporis:
        РНП = Премия × (Оставшиеся дни / Всего дней)

        Метод 1/365:
        РНП = Премия × Оставшиеся дни / 365
        """
        result = ReserveCalculation(
            reserve_type=ReserveType.RNPP,
            calculation_date=calculation_date,
            insurance_class="general",
            gross_amount=premium_amount,
            calculation_method=method
        )

        total_days = (expiry_date - inception_date).days
        elapsed_days = (calculation_date - inception_date).days
        remaining_days = max(0, total_days - elapsed_days)

        if method == 'pro_rata':
            if total_days > 0:
                unearned_portion = Decimal(str(remaining_days)) / Decimal(str(total_days))
            else:
                unearned_portion = Decimal('0')
            result.reserve_amount = premium_amount * unearned_portion
            result.formula_display = f"РНП = {premium_amount:,.0f} × ({remaining_days} / {total_days}) = {result.reserve_amount:,.0f}"

        elif method == '1_365':
            unearned_portion = Decimal(str(remaining_days)) / Decimal('365')
            result.reserve_amount = premium_amount * unearned_portion
            result.formula_display = f"РНП = {premium_amount:,.0f} × ({remaining_days} / 365) = {result.reserve_amount:,.0f}"

        result.parameters = {
            'inception_date': inception_date.isoformat(),
            'expiry_date': expiry_date.isoformat(),
            'total_days': total_days,
            'elapsed_days': elapsed_days,
            'remaining_days': remaining_days
        }

        return result

    def calculate_ibnr_chain_ladder(
        self,
        loss_triangles: List[List[Decimal]],
        calculation_date: date
    ) -> ReserveCalculation:
        """
        Расчёт IBNR методом Chain-Ladder по П.№304

        Development factors вычисляются из треугольника развития убытков
        """
        result = ReserveCalculation(
            reserve_type=ReserveType.RPNU,
            calculation_date=calculation_date,
            insurance_class="general",
            calculation_method="chain_ladder"
        )

        # Упрощённый Chain-Ladder
        # loss_triangles[i][j] = убытки года i на период развития j
        if not loss_triangles or not loss_triangles[0]:
            result.reserve_amount = Decimal('0')
            return result

        n_years = len(loss_triangles)
        n_periods = len(loss_triangles[0])

        # Расчёт факторов развития
        development_factors = []
        for j in range(n_periods - 1):
            sum_current = Decimal('0')
            sum_previous = Decimal('0')
            for i in range(n_years - j - 1):
                if j < len(loss_triangles[i]) and j + 1 < len(loss_triangles[i]):
                    sum_current += loss_triangles[i][j + 1]
                    sum_previous += loss_triangles[i][j]

            if sum_previous > 0:
                factor = sum_current / sum_previous
            else:
                factor = Decimal('1')
            development_factors.append(factor)

        # Проекция убытков
        ultimate_losses = []
        for i in range(n_years):
            current_period = len([x for x in loss_triangles[i] if x is not None])
            if current_period > 0:
                ultimate = loss_triangles[i][current_period - 1]
                for j in range(current_period - 1, n_periods - 1):
                    if j < len(development_factors):
                        ultimate *= development_factors[j]
                ultimate_losses.append(ultimate)

        # IBNR = Ultimate - Paid
        total_paid = sum(
            loss_triangles[i][-1] if loss_triangles[i] else Decimal('0')
            for i in range(n_years)
        )
        total_ultimate = sum(ultimate_losses)
        result.reserve_amount = max(Decimal('0'), total_ultimate - total_paid)

        result.parameters = {
            'development_factors': [str(f) for f in development_factors],
            'ultimate_losses': [str(u) for u in ultimate_losses],
            'n_years': n_years,
            'n_periods': n_periods
        }
        result.formula_display = f"IBNR = Ultimate ({total_ultimate:,.0f}) - Paid ({total_paid:,.0f}) = {result.reserve_amount:,.0f}"

        return result


# Глобальный экземпляр сервиса
regulatory_report_service = RegulatoryReportService()
