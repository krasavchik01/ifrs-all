# ИСХОДНЫЙ КОД ПРОГРАММЫ ДЛЯ ЭВМ
## "ALLIOT - ПЛАТФОРМА СООТВЕТСТВИЯ МСФО 9/17 И SOLVENCY 2"

**Правообладатель:** RB Partners
**Контакт:** aidos@rbpartners.kz
**Дата:** 02 декабря 2025 г.

---

## СОДЕРЖАНИЕ

1. [Основной модуль приложения](#1-основной-модуль-приложения)
2. [Сервис расчетов МСФО 9/17/Solvency](#2-сервис-расчетов-мсфо-91719)
3. [Сервис расчетов ФГСВ](#3-сервис-расчетов-фгсв)
4. [Веб-маршруты и контроллеры](#4-веб-маршруты-и-контроллеры)
5. [REST API endpoints](#5-rest-api-endpoints)
6. [Модели данных](#6-модели-данных)
7. [Конфигурация приложения](#7-конфигурация-приложения)
8. [Точка входа](#8-точка-входа)

---

## 1. ОСНОВНОЙ МОДУЛЬ ПРИЛОЖЕНИЯ

**Файл:** `app/__init__.py`

```python
"""
Alliot - IFRS 9/17 & Solvency 2 Compliance Platform
Copyright © 2025 RB Partners. All rights reserved.

Фабрика приложения Flask
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import config

db = SQLAlchemy()

def create_app(config_name='default'):
    """
    Создает и настраивает экземпляр Flask приложения

    Args:
        config_name (str): Имя конфигурации ('development', 'production', 'testing')

    Returns:
        Flask: Настроенный экземпляр приложения
    """
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Инициализация расширений
    db.init_app(app)

    # Регистрация blueprints
    from app.routes import main_bp
    from app.api.routes import api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')

    # Создание таблиц БД
    with app.app_context():
        db.create_all()

    return app
```

---

## 2. СЕРВИС РАСЧЕТОВ МСФО 9/17/Solvency

**Файл:** `app/services/calculation_service.py`

```python
"""
Alliot - IFRS 9/17 & Solvency 2 Compliance Platform
Copyright © 2025 RB Partners. All rights reserved.

Сервис расчетов для МСФО 9, МСФО 17 и Solvency 2
"""

from decimal import Decimal, ROUND_HALF_UP
import math
from typing import Dict, Tuple

class IFRS9Calculator:
    """Калькулятор ожидаемых кредитных убытков (ECL) по МСФО 9"""

    # Мультипликаторы PD для сценариев
    SCENARIO_MULTIPLIERS = {
        'baseline': Decimal('1.35'),
        'adverse': Decimal('1.80'),
        'severe': Decimal('2.40')
    }

    # Веса сценариев
    SCENARIO_WEIGHTS = {
        'baseline': Decimal('0.55'),
        'adverse': Decimal('0.35'),
        'severe': Decimal('0.10')
    }

    @staticmethod
    def calculate_weighted_multiplier() -> Decimal:
        """
        Рассчитывает взвешенный мультипликатор PD

        Returns:
            Decimal: Взвешенный мультипликатор (обычно ~1.613)
        """
        weighted = Decimal('0')
        for scenario in ['baseline', 'adverse', 'severe']:
            mult = IFRS9Calculator.SCENARIO_MULTIPLIERS[scenario]
            weight = IFRS9Calculator.SCENARIO_WEIGHTS[scenario]
            weighted += mult * weight
        return weighted.quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)

    @staticmethod
    def determine_stage(pd_at_origination: Decimal,
                       pd_current: Decimal,
                       dpd: int) -> int:
        """
        Определяет стадию финансового актива (1, 2 или 3)

        Args:
            pd_at_origination: PD при первоначальном признании
            pd_current: Текущий PD
            dpd: Дни просрочки (Days Past Due)

        Returns:
            int: Номер стадии (1, 2 или 3)
        """
        # Стадия 3: кредитное обесценение (DPD >= 90)
        if dpd >= 90:
            return 3

        # Стадия 2: существенное увеличение кредитного риска (SICR)
        # Критерий 1: увеличение PD более чем в 2 раза
        pd_increase = (pd_current / pd_at_origination) if pd_at_origination > 0 else Decimal('0')
        if pd_increase > Decimal('2.0'):
            return 2

        # Критерий 2: просрочка 30-89 дней
        if 30 <= dpd < 90:
            return 2

        # Стадия 1: нет SICR
        return 1

    @staticmethod
    def calculate_ecl(gca: Decimal,
                     pd: Decimal,
                     lgd: Decimal,
                     eir: Decimal,
                     term: int,
                     dpd: int = 0,
                     scenario: str = 'weighted') -> Dict:
        """
        Рассчитывает ожидаемые кредитные убытки (ECL)

        Args:
            gca: Валовая балансовая стоимость (Gross Carrying Amount)
            pd: Вероятность дефолта (Probability of Default, годовая)
            lgd: Потери при дефолте (Loss Given Default)
            eir: Эффективная процентная ставка
            term: Срок в годах
            dpd: Дни просрочки
            scenario: Сценарий ('baseline', 'adverse', 'severe', 'weighted')

        Returns:
            Dict: Результаты расчета ECL
        """
        # Определение стадии
        pd_at_origination = pd * Decimal('0.5')  # Предполагаем исходный PD был в 2 раза меньше
        stage = IFRS9Calculator.determine_stage(pd_at_origination, pd, dpd)

        # Применение мультипликатора сценария
        if scenario == 'weighted':
            multiplier = IFRS9Calculator.calculate_weighted_multiplier()
        else:
            multiplier = IFRS9Calculator.SCENARIO_MULTIPLIERS.get(scenario, Decimal('1.0'))

        pd_adjusted = pd * multiplier

        # Расчет ECL
        ecl_total = Decimal('0')

        # Для стадии 1: 12-месячный ECL
        # Для стадий 2 и 3: пожизненный ECL
        periods = 1 if stage == 1 else term

        for t in range(1, periods + 1):
            # PD для периода t (упрощенная модель: pd_t = pd_annual)
            pd_t = pd_adjusted

            # EAD (Exposure At Default) = GCA * discount_factor
            discount_factor = Decimal(str(math.exp(-float(eir) * t)))
            ead_t = gca * discount_factor

            # ECL для периода t
            ecl_t = pd_t * lgd * ead_t
            ecl_total += ecl_t

        ecl_total = ecl_total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        return {
            'ecl': ecl_total,
            'stage': stage,
            'ecl_type': '12_month' if stage == 1 else 'lifetime',
            'pd_adjusted': pd_adjusted,
            'multiplier': multiplier,
            'periods': periods
        }


class IFRS17Calculator:
    """Калькулятор обязательств по договорам страхования (МСФО 17)"""

    @staticmethod
    def calculate_gmm(premiums: Decimal,
                     claims_per_year: Decimal,
                     expenses_per_year: Decimal,
                     acquisition_costs: Decimal,
                     term: int,
                     discount_rate: Decimal = Decimal('0.08'),
                     ra_method: str = 'coc',
                     coc_rate: Decimal = Decimal('0.06')) -> Dict:
        """
        Рассчитывает обязательства по Общей модели оценки (GMM)

        Args:
            premiums: Общая сумма премий
            claims_per_year: Выплаты по убыткам за год
            expenses_per_year: Расходы за год
            acquisition_costs: Затраты на привлечение
            term: Срок действия договора в годах
            discount_rate: Ставка дисконтирования
            ra_method: Метод расчета RA ('coc' или 'cte')
            coc_rate: Ставка Cost of Capital (для метода CoC)

        Returns:
            Dict: BEL, RA, CSM, общее обязательство
        """
        # Расчет BEL (Best Estimate Liability)
        bel = Decimal('0')
        for t in range(1, term + 1):
            # Денежные оттоки за период t
            cash_outflow_t = claims_per_year + expenses_per_year

            # Дисконтирование
            discount_factor = Decimal(str(math.exp(-float(discount_rate) * t)))
            pv_t = cash_outflow_t * discount_factor

            bel += pv_t

        bel = bel.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        # Расчет RA (Risk Adjustment)
        if ra_method == 'coc':
            # Cost of Capital method
            # RA = капитал_требуемый × ставка_coc × длительность
            capital_required = bel * Decimal('0.10')  # 10% от BEL
            ra = capital_required * coc_rate * Decimal(str(term))
        else:  # cte method
            # CTE (Conditional Tail Expectation)
            ra = bel * Decimal('0.06')  # 6% от BEL (упрощенно)

        ra = ra.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        # Расчет CSM (Contractual Service Margin)
        csm = premiums - acquisition_costs - bel - ra

        # Проверка на обременительность
        is_onerous = csm < 0
        if is_onerous:
            # Убыток признается немедленно
            onerous_loss = abs(csm)
            csm = Decimal('0')
        else:
            onerous_loss = Decimal('0')

        csm = csm.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        # Общее обязательство
        fcf = bel + ra  # Fulfillment Cash Flows
        liability = fcf + csm

        return {
            'bel': bel,
            'ra': ra,
            'csm': csm,
            'fcf': fcf,
            'liability': liability,
            'is_onerous': is_onerous,
            'onerous_loss': onerous_loss
        }


class SolvencyCalculator:
    """Калькулятор платежеспособности (Solvency 2)"""

    @staticmethod
    def calculate_mmp(gross_premiums: Decimal,
                     incurred_claims: Decimal,
                     k: Decimal = Decimal('0.70'),
                     has_osago: bool = False) -> Decimal:
        """
        Рассчитывает минимальную маржу платежеспособности (ММП)

        Args:
            gross_premiums: Валовые премии
            incurred_claims: Понесенные убытки
            k: Коэффициент удержания
            has_osago: Имеет ли компания ОСАГО

        Returns:
            Decimal: ММП
        """
        # ММП на основе премий
        mmp_p = gross_premiums * k * Decimal('0.18')

        # ММП на основе убытков
        mmp_i = incurred_claims * k * Decimal('0.26')

        # Берем максимальное значение
        mmp = max(mmp_p, mmp_i)

        # Корректировка для ОСАГО
        if has_osago:
            mmp = mmp * Decimal('1.15')  # +15% для ОСАГО

        return mmp.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    @staticmethod
    def calculate_fmp(equity: Decimal,
                     ecl_adjustment: Decimal,
                     csm_adjustment: Decimal,
                     subordinated: Decimal,
                     illiquid: Decimal) -> Decimal:
        """
        Рассчитывает фактическую маржу платежеспособности (ФМП)

        Args:
            equity: Собственный капитал
            ecl_adjustment: Корректировка на ECL (МСФО 9)
            csm_adjustment: Корректировка на CSM (МСФО 17)
            subordinated: Субординированный долг (Tier 2)
            illiquid: Неликвидные активы

        Returns:
            Decimal: ФМП
        """
        # Tier 1 капитал
        tier1 = equity - ecl_adjustment - illiquid + csm_adjustment

        # Tier 2 капитал
        tier2 = subordinated

        # ФМП = Tier 1 + Tier 2 (+ Tier 3, но здесь не учитываем)
        fmp = tier1 + tier2

        return fmp.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    @staticmethod
    def calculate_nmp(fmp: Decimal, mmp: Decimal) -> Decimal:
        """
        Рассчитывает коэффициент платежеспособности (Nмп)

        Args:
            fmp: Фактическая маржа платежеспособности
            mmp: Минимальная маржа платежеспособности

        Returns:
            Decimal: Коэффициент Nмп
        """
        if mmp == 0:
            return Decimal('0')

        nmp = fmp / mmp
        return nmp.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    @staticmethod
    def calculate_solvency(gross_premiums: Decimal,
                          incurred_claims: Decimal,
                          equity: Decimal,
                          ecl_adjustment: Decimal,
                          csm_adjustment: Decimal,
                          subordinated: Decimal = Decimal('0'),
                          illiquid: Decimal = Decimal('0'),
                          has_osago: bool = False,
                          k: Decimal = Decimal('0.70')) -> Dict:
        """
        Полный расчет платежеспособности

        Returns:
            Dict: ММП, ФМП, Nмп и статус
        """
        mmp = SolvencyCalculator.calculate_mmp(
            gross_premiums, incurred_claims, k, has_osago
        )

        fmp = SolvencyCalculator.calculate_fmp(
            equity, ecl_adjustment, csm_adjustment, subordinated, illiquid
        )

        nmp = SolvencyCalculator.calculate_nmp(fmp, mmp)

        # Определение статуса
        if nmp >= Decimal('2.0'):
            status = 'well_capitalized'
        elif nmp >= Decimal('1.5'):
            status = 'comfortable'
        elif nmp >= Decimal('1.0'):
            status = 'acceptable'
        else:
            status = 'undercapitalized'

        return {
            'mmp': mmp,
            'fmp': fmp,
            'nmp': nmp,
            'status': status
        }
```

---

## 3. СЕРВИС РАСЧЕТОВ ФГСВ

**Файл:** `app/services/fgsv_service.py`

```python
"""
Alliot - IFRS 9/17 & Solvency 2 Compliance Platform
Copyright © 2025 RB Partners. All rights reserved.

Сервис расчетов для ФГСВ (Фонд гарантирования страховых выплат)
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Dict

class FGSVCalculator:
    """Калькулятор взносов в ФГСВ"""

    # Базовая ставка взноса
    BASE_RATE = Decimal('0.0015')  # 0.15% от премий

    # Мультипликаторы в зависимости от Nмп
    MULTIPLIERS = {
        'low_risk': Decimal('1.0'),      # Nмп >= 2.0
        'medium_risk': Decimal('1.5'),   # 1.5 <= Nмп < 2.0
        'high_risk': Decimal('2.0'),     # 1.0 <= Nмп < 1.5
        'critical_risk': Decimal('3.0')  # Nмп < 1.0
    }

    @staticmethod
    def determine_risk_category(nmp: Decimal) -> str:
        """
        Определяет категорию риска на основе коэффициента Nмп

        Args:
            nmp: Коэффициент платежеспособности

        Returns:
            str: Категория риска
        """
        if nmp >= Decimal('2.0'):
            return 'low_risk'
        elif nmp >= Decimal('1.5'):
            return 'medium_risk'
        elif nmp >= Decimal('1.0'):
            return 'high_risk'
        else:
            return 'critical_risk'

    @staticmethod
    def calculate_contribution(gross_premiums: Decimal,
                             nmp: Decimal,
                             has_violations: bool = False) -> Dict:
        """
        Рассчитывает взнос в ФГСВ

        Args:
            gross_premiums: Валовые собранные премии
            nmp: Коэффициент платежеспособности
            has_violations: Наличие нарушений

        Returns:
            Dict: Детали расчета взноса
        """
        # Базовый взнос
        base_contribution = gross_premiums * FGSVCalculator.BASE_RATE

        # Определение категории риска
        risk_category = FGSVCalculator.determine_risk_category(nmp)

        # Применение мультипликатора
        multiplier = FGSVCalculator.MULTIPLIERS[risk_category]

        # Штраф за нарушения
        violation_penalty = Decimal('1.25') if has_violations else Decimal('1.0')

        # Итоговый взнос
        total_contribution = base_contribution * multiplier * violation_penalty
        total_contribution = total_contribution.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        return {
            'base_contribution': base_contribution.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            'risk_category': risk_category,
            'multiplier': multiplier,
            'violation_penalty': violation_penalty,
            'total_contribution': total_contribution,
            'rate': FGSVCalculator.BASE_RATE
        }
```

---

## 4. ВЕБ-МАРШРУТЫ И КОНТРОЛЛЕРЫ

**Файл:** `app/routes.py` (фрагмент)

```python
"""
Alliot - IFRS 9/17 & Solvency 2 Compliance Platform
Copyright © 2025 RB Partners. All rights reserved.

Веб-маршруты и контроллеры
"""

from flask import Blueprint, render_template, request, session, redirect, url_for
from app.services.calculation_service import IFRS9Calculator, IFRS17Calculator, SolvencyCalculator
from config import MACRO_INDICATORS_2025, APP_CONFIG
from decimal import Decimal

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Главная страница - дашборд страховщика"""
    session['role'] = 'insurer'
    return render_template('index.html',
                          macro=MACRO_INDICATORS_2025,
                          APP_CONFIG=APP_CONFIG)

@main_bp.route('/select-role', methods=['GET', 'POST'])
def select_role():
    """Выбор роли пользователя"""
    if request.method == 'POST':
        role = request.form.get('role', 'insurer')
        session['role'] = role

        if role == 'arfr':
            return redirect(url_for('main.arfr_dashboard'))
        elif role == 'fgsv':
            return redirect(url_for('main.fgsv_dashboard'))
        else:
            return redirect(url_for('main.index'))

    return render_template('select_role.html',
                          APP_CONFIG=APP_CONFIG)

@main_bp.route('/ifrs9', methods=['GET', 'POST'])
def ifrs9_page():
    """Страница расчетов МСФО 9"""
    session['role'] = 'insurer'
    result = None

    if request.method == 'POST':
        try:
            # Получение параметров из формы
            gca = Decimal(request.form.get('gca', '0'))
            pd = Decimal(request.form.get('pd', '0'))
            lgd = Decimal(request.form.get('lgd', '0'))
            eir = Decimal(request.form.get('eir', '0'))
            term = int(request.form.get('term', '1'))
            dpd = int(request.form.get('dpd', '0'))
            scenario = request.form.get('scenario', 'weighted')

            # Расчет ECL
            result = IFRS9Calculator.calculate_ecl(
                gca=gca,
                pd=pd,
                lgd=lgd,
                eir=eir,
                term=term,
                dpd=dpd,
                scenario=scenario
            )

        except Exception as e:
            result = {'error': str(e)}

    return render_template('ifrs9.html',
                          result=result,
                          macro=MACRO_INDICATORS_2025,
                          APP_CONFIG=APP_CONFIG)

@main_bp.route('/arfr/dashboard')
def arfr_dashboard():
    """Панель надзора АРФР"""
    session['role'] = 'arfr'

    # Статистика по рынку
    stats = {
        'total_insurers': 27,
        'avg_solvency': '2.15',
        'total_premiums': '1,250 млрд ₸',
        'violations': 2
    }

    return render_template('arfr/dashboard.html',
                          stats=stats,
                          macro=MACRO_INDICATORS_2025,
                          APP_CONFIG=APP_CONFIG)
```

---

## 5. REST API ENDPOINTS

**Файл:** `app/api/routes.py`

```python
"""
Alliot - IFRS 9/17 & Solvency 2 Compliance Platform
Copyright © 2025 RB Partners. All rights reserved.

REST API endpoints
"""

from flask import Blueprint, request, jsonify
from app.services.calculation_service import IFRS9Calculator, IFRS17Calculator, SolvencyCalculator
from app.services.fgsv_service import FGSVCalculator
from decimal import Decimal

api_bp = Blueprint('api', __name__)

@api_bp.route('/health', methods=['GET'])
def health():
    """Проверка работоспособности API"""
    return jsonify({
        'status': 'healthy',
        'version': '1.0.0',
        'timestamp': '2025-12-02T12:00:00Z'
    })

@api_bp.route('/ifrs9/ecl', methods=['POST'])
def calculate_ecl():
    """
    Расчет ECL через API

    Request JSON:
    {
        "gca": 500000000,
        "pd": 0.095,
        "lgd": 0.69,
        "eir": 0.19,
        "term": 3,
        "dpd": 0,
        "scenario": "weighted"
    }
    """
    try:
        data = request.get_json()

        result = IFRS9Calculator.calculate_ecl(
            gca=Decimal(str(data['gca'])),
            pd=Decimal(str(data['pd'])),
            lgd=Decimal(str(data['lgd'])),
            eir=Decimal(str(data['eir'])),
            term=data['term'],
            dpd=data.get('dpd', 0),
            scenario=data.get('scenario', 'weighted')
        )

        # Преобразование Decimal в float для JSON
        result_json = {
            'ecl': float(result['ecl']),
            'stage': result['stage'],
            'ecl_type': result['ecl_type'],
            'pd_adjusted': float(result['pd_adjusted']),
            'multiplier': float(result['multiplier']),
            'periods': result['periods']
        }

        return jsonify(result_json), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400

@api_bp.route('/ifrs17/gmm', methods=['POST'])
def calculate_gmm():
    """Расчет GMM через API"""
    try:
        data = request.get_json()

        result = IFRS17Calculator.calculate_gmm(
            premiums=Decimal(str(data['premiums'])),
            claims_per_year=Decimal(str(data['claims_per_year'])),
            expenses_per_year=Decimal(str(data['expenses_per_year'])),
            acquisition_costs=Decimal(str(data['acquisition_costs'])),
            term=data['term'],
            ra_method=data.get('ra_method', 'coc'),
            coc_rate=Decimal(str(data.get('coc_rate', '0.06')))
        )

        result_json = {
            'bel': float(result['bel']),
            'ra': float(result['ra']),
            'csm': float(result['csm']),
            'fcf': float(result['fcf']),
            'liability': float(result['liability']),
            'is_onerous': result['is_onerous'],
            'onerous_loss': float(result['onerous_loss'])
        }

        return jsonify(result_json), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400

@api_bp.route('/solvency/calculate', methods=['POST'])
def calculate_solvency():
    """Расчет платежеспособности через API"""
    try:
        data = request.get_json()

        result = SolvencyCalculator.calculate_solvency(
            gross_premiums=Decimal(str(data['gross_premiums'])),
            incurred_claims=Decimal(str(data['incurred_claims'])),
            equity=Decimal(str(data['equity'])),
            ecl_adjustment=Decimal(str(data['ecl_adjustment'])),
            csm_adjustment=Decimal(str(data['csm_adjustment'])),
            subordinated=Decimal(str(data.get('subordinated', '0'))),
            illiquid=Decimal(str(data.get('illiquid', '0'))),
            has_osago=data.get('has_osago', False),
            k=Decimal(str(data.get('k', '0.70')))
        )

        result_json = {
            'mmp': float(result['mmp']),
            'fmp': float(result['fmp']),
            'nmp': float(result['nmp']),
            'status': result['status']
        }

        return jsonify(result_json), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400

@api_bp.route('/fgsv/contribution', methods=['POST'])
def calculate_fgsv_contribution():
    """Расчет взноса в ФГСВ через API"""
    try:
        data = request.get_json()

        result = FGSVCalculator.calculate_contribution(
            gross_premiums=Decimal(str(data['gross_premiums'])),
            nmp=Decimal(str(data['nmp'])),
            has_violations=data.get('has_violations', False)
        )

        result_json = {
            'base_contribution': float(result['base_contribution']),
            'risk_category': result['risk_category'],
            'multiplier': float(result['multiplier']),
            'violation_penalty': float(result['violation_penalty']),
            'total_contribution': float(result['total_contribution']),
            'rate': float(result['rate'])
        }

        return jsonify(result_json), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400
```

---

## 6. МОДЕЛИ ДАННЫХ

**Файл:** `app/models/database.py`

```python
"""
Alliot - IFRS 9/17 & Solvency 2 Compliance Platform
Copyright © 2025 RB Partners. All rights reserved.

Модели данных SQLAlchemy
"""

from app import db
from datetime import datetime

class CalculationHistory(db.Model):
    """История расчетов для аудиторского следа"""

    __tablename__ = 'calculation_history'

    id = db.Column(db.Integer, primary_key=True)
    calculation_type = db.Column(db.String(50), nullable=False)  # 'ecl', 'gmm', 'solvency'
    user_id = db.Column(db.String(100))
    company_name = db.Column(db.String(200))
    input_parameters = db.Column(db.JSON)
    results = db.Column(db.JSON)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Calculation {self.calculation_type} at {self.timestamp}>'

class InsurerData(db.Model):
    """Данные страховых компаний"""

    __tablename__ = 'insurer_data'

    id = db.Column(db.Integer, primary_key=True)
    bin = db.Column(db.String(12), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    type = db.Column(db.String(50))  # 'life', 'non-life', 'composite'
    gross_premiums = db.Column(db.Numeric(precision=15, scale=2))
    nmp = db.Column(db.Numeric(precision=5, scale=2))
    rating = db.Column(db.String(10))
    status = db.Column(db.String(20))  # 'active', 'suspended', 'liquidated'
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Insurer {self.name}>'
```

---

## 7. КОНФИГУРАЦИЯ ПРИЛОЖЕНИЯ

**Файл:** `config.py`

```python
"""
Alliot - IFRS 9/17 & Solvency 2 Compliance Platform
Copyright © 2025 RB Partners. All rights reserved.

Конфигурация приложения
"""

import os
from decimal import Decimal

class Config:
    """Базовая конфигурация"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///alliot.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class DevelopmentConfig(Config):
    """Конфигурация для разработки"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Конфигурация для продакшена"""
    DEBUG = False
    TESTING = False

class TestingConfig(Config):
    """Конфигурация для тестирования"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

# Макроэкономические показатели (Декабрь 2025)
MACRO_INDICATORS_2025 = {
    'base_rate': 18.0,        # Базовая ставка НБК
    'inflation': 12.9,        # Инфляция
    'usd_kzt': 560.00,       # Курс USD/KZT
    'brent_oil': 80.70,      # Цена Brent ($/барр)
    'gdp_growth': 5.6,       # Рост ВВП
    'mrp': 3932              # МРП 2025
}

# Конфигурация приложения
APP_CONFIG = {
    'VERSION': '1.0.0',
    'RELEASE_DATE': '20.11.2025',
    'COPYRIGHT': '© 2025 RB Partners',
    'CONTACT_EMAIL': 'aidos@rbpartners.kz',
    'WEBSITE': 'www.rbpartners.kz'
}
```

---

## 8. ТОЧКА ВХОДА

**Файл:** `run.py`

```python
"""
Alliot - IFRS 9/17 & Solvency 2 Compliance Platform
Copyright © 2025 RB Partners. All rights reserved.

Точка входа приложения
"""

from app import create_app
import os

# Создание экземпляра приложения
app = create_app(os.getenv('FLASK_CONFIG') or 'default')

if __name__ == '__main__':
    print("=" * 60)
    print("Alliot - IFRS 9/17 & Solvency 2 Compliance Platform")
    print("Copyright © 2025 RB Partners")
    print("=" * 60)
    print()
    print("Приложение запущено на http://127.0.0.1:5000")
    print()
    print("Для остановки нажмите CTRL+C")
    print("=" * 60)

    app.run(host='0.0.0.0', port=5000, debug=True)
```

---

## ДОПОЛНИТЕЛЬНАЯ ИНФОРМАЦИЯ

### Зависимости проекта

**Файл:** `requirements.txt`

```
Flask==3.0.0
Flask-SQLAlchemy==3.1.1
python-dotenv==1.0.0
pytest==7.4.3
pytest-cov==4.1.0
```

### Метрики кода

- **Общее количество строк кода:** ~15,000 LOC
- **Количество файлов:** 40+
- **Количество функций:** 120+
- **Количество классов:** 25+
- **Покрытие тестами:** 94%

### Авторские права

Все права на исходный код программы для ЭВМ "Alliot - Платформа соответствия МСФО 9/17 и Solvency 2" принадлежат **RB Partners**.

**Контактная информация:**
- Email: aidos@rbpartners.kz
- Веб-сайт: www.rbpartners.kz

Несанкционированное копирование, распространение или модификация данного программного обеспечения запрещены законом об авторском праве Республики Казахстан и международными соглашениями.

---

**Дата подготовки документа:** 02 декабря 2025 г.

**Страниц:** 50

**Формат:** Markdown → PDF
