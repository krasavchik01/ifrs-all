# -*- coding: utf-8 -*-
"""
KZ-InsurePro - Главные маршруты Flask
Система с ролями: АРФР, ФГСВ, Страховые компании
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, session
from decimal import Decimal
from datetime import date, datetime
from sqlalchemy import func

# ВАЖНО: Используем только unified_calculation_service для всех расчетов!
# Это гарантирует что цифры везде одинаковые
from app.services.unified_calculation_service import unified_calculation_service
from app import db
from app.enterprise_models import JournalEntry, MeasurementModel
from config import (
    APP_CONFIG, MACRO_INDICATORS_2025,
    format_currency, format_percent
)

main_bp = Blueprint('main', __name__)


# =============================================================================
# ВЫБОР РОЛИ
# =============================================================================

@main_bp.route('/landing')
def landing():
    """Landing page - Продающая презентация Alliot"""
    return render_template('landing.html',
                          macro=MACRO_INDICATORS_2025,
                          APP_CONFIG=APP_CONFIG)


@main_bp.route('/select-role', methods=['GET', 'POST'])
def select_role():
    """Страница выбора роли"""
    if request.method == 'POST':
        role = request.form.get('role', 'insurer')
        session['role'] = role

        # Перенаправление на соответствующую панель
        if role == 'arfr':
            return redirect(url_for('main.arfr_dashboard'))
        elif role == 'fgsv':
            return redirect(url_for('main.fgsv_dashboard'))
        else:
            return redirect(url_for('main.index'))

    # Если пришли с landing page с параметром role
    if request.args.get('role'):
        role = request.args.get('role')
        session['role'] = role
        if role == 'arfr':
            return redirect(url_for('main.arfr_dashboard'))
        elif role == 'fgsv':
            return redirect(url_for('main.fgsv_dashboard'))
        else:
            return redirect(url_for('main.index'))

    return render_template('select_role.html',
                          macro=MACRO_INDICATORS_2025,
                          APP_CONFIG=APP_CONFIG)


# =============================================================================
# СТРАХОВАЯ КОМПАНИЯ - МАРШРУТЫ
# =============================================================================

@main_bp.route('/')
@main_bp.route('/dashboard')
def index():
    """Главная страница - Современный дашборд страховой компании с Chart.js графиками"""
    if not session.get('role'):
        session['role'] = 'insurer'

    return render_template('insurer_dashboard.html',
                          macro=MACRO_INDICATORS_2025,
                          APP_CONFIG=APP_CONFIG)


@main_bp.route('/help')
def help_guide():
    """Справка и руководство по использованию системы"""
    return render_template('help_guide.html',
                          macro=MACRO_INDICATORS_2025,
                          APP_CONFIG=APP_CONFIG)


# =============================================================================
# CRM - КЛИЕНТЫ И АГЕНТЫ
# =============================================================================

@main_bp.route('/customers')
def customers_page():
    """Страница управления клиентами - CRM модуль"""
    session['role'] = 'insurer'

    # Демо данные клиентов
    customers = [
        {
            'id': 'cust_001',
            'full_name': 'Алиева Айгерим Сериковна',
            'iin': '850215300123',
            'email': 'aigerim.alieva@example.kz',
            'phone': '+7 (701) 234-56-78',
            'segment': 'VIP',
            'risk_rating': 'LOW',
            'customer_lifetime_value': 2500000,
            'total_policies': 3,
            'total_claims': 1,
            'last_interaction': '2026-01-20',
            'is_active': True
        },
        {
            'id': 'cust_002',
            'full_name': 'Нурымбетов Ерлан Маратович',
            'iin': '920512400234',
            'email': 'erlan.nurymbetov@example.kz',
            'phone': '+7 (702) 345-67-89',
            'segment': 'STANDARD',
            'risk_rating': 'MEDIUM',
            'customer_lifetime_value': 950000,
            'total_policies': 2,
            'total_claims': 0,
            'last_interaction': '2026-01-18',
            'is_active': True
        },
        {
            'id': 'cust_003',
            'full_name': 'Сатпаева Динара Кайратовна',
            'iin': '880903500345',
            'email': 'dinara.satpaeva@example.kz',
            'phone': '+7 (707) 456-78-90',
            'segment': 'VIP',
            'risk_rating': 'LOW',
            'customer_lifetime_value': 4200000,
            'total_policies': 5,
            'total_claims': 2,
            'last_interaction': '2026-02-01',
            'is_active': True
        },
    ]

    stats = {
        'total': len(customers),
        'vip': len([c for c in customers if c['segment'] == 'VIP']),
        'total_clv': '{:,.0f}'.format(sum(c['customer_lifetime_value'] for c in customers)),
        'active': len([c for c in customers if c['is_active']])
    }

    return render_template('crm/customers.html',
                          customers=customers,
                          stats=stats,
                          macro=MACRO_INDICATORS_2025,
                          APP_CONFIG=APP_CONFIG)


@main_bp.route('/agents')
def agents_page():
    """Страница управления агентами - CRM модуль"""
    session['role'] = 'insurer'

    # Демо данные агентов
    agents = [
        {
            'id': 'agent_001',
            'agent_code': 'AG-001',
            'full_name': 'Досов Самат Ерланович',
            'email': 'samat.dosov@insureagent.kz',
            'phone': '+7 (701) 111-22-33',
            'type': 'INDIVIDUAL',
            'status': 'ACTIVE',
            'region': 'Алматы',
            'performance': {
                'total_policies_sold': 45,
                'total_premium_volume': 42500000,
                'total_commission_earned': 2125000,
                'conversion_rate': 68.5,
                'retention_rate': 92.0,
                'customer_satisfaction_score': 9.2
            },
            'kpi_score': 87.3,
            'last_sale_date': '2026-01-19'
        },
        {
            'id': 'agent_002',
            'agent_code': 'AG-002',
            'full_name': 'Касымова Алия Бекетовна',
            'email': 'aliya.kasymova@insureagent.kz',
            'phone': '+7 (702) 222-33-44',
            'type': 'BROKER',
            'status': 'ACTIVE',
            'region': 'Астана',
            'performance': {
                'total_policies_sold': 62,
                'total_premium_volume': 58300000,
                'total_commission_earned': 2915000,
                'conversion_rate': 72.1,
                'retention_rate': 89.5,
                'customer_satisfaction_score': 9.5
            },
            'kpi_score': 91.2,
            'last_sale_date': '2026-01-21'
        },
    ]

    summary = {
        'total_agents': len(agents),
        'active_agents': len([a for a in agents if a['status'] == 'ACTIVE']),
        'avg_kpi_score': round(sum(a['kpi_score'] for a in agents) / len(agents), 1),
        'total_premium': sum(a['performance']['total_premium_volume'] for a in agents),
        'total_commission': sum(a['performance']['total_commission_earned'] for a in agents)
    }

    stats = {
        'individual': 60,
        'brokers': 30,
        'corporate': 10
    }

    return render_template('crm/agents.html',
                          agents=agents,
                          summary=summary,
                          stats=stats,
                          macro=MACRO_INDICATORS_2025,
                          APP_CONFIG=APP_CONFIG)


# =============================================================================
# НОВЫЕ УПРОЩЕННЫЕ РОУТЫ
# =============================================================================

@main_bp.route('/ifrs9')
def ifrs9_page():
    """
    Страница МСФО 9 - Детальная подробная аналитика финансовых инструментов
    Все расчеты ECL, кликабельные инструменты с модальными окнами
    """
    session['role'] = 'insurer'
    return render_template('ifrs9_detailed.html',
                          macro=MACRO_INDICATORS_2025,
                          APP_CONFIG=APP_CONFIG)


@main_bp.route('/ifrs17')
def ifrs17_page():
    """
    Страница МСФО 17 - Детальная подробная аналитика страховых договоров
    Все расчеты CSM, BEL, Risk Adjustment с модальными окнами договоров
    """
    session['role'] = 'insurer'
    return render_template('ifrs17_detailed.html',
                          macro=MACRO_INDICATORS_2025,
                          APP_CONFIG=APP_CONFIG)


@main_bp.route('/settings')
def settings():
    """
    Настройки системы

    Включает:
    - Интеграция с 1С
    - План счетов
    - Пользователи
    """
    session['role'] = 'insurer'
    return render_template('settings.html',
                          macro=MACRO_INDICATORS_2025,
                          APP_CONFIG=APP_CONFIG)


@main_bp.route('/solvency2')
def solvency2_page():
    """
    Страница Solvency 2 - Детальная подробная аналитика платежеспособности
    Все расчеты SCR, Own Funds, Risk Analysis с полными формулами и диаграммами
    """
    session['role'] = 'insurer'
    return render_template('solvency2_detailed.html',
                          macro=MACRO_INDICATORS_2025,
                          APP_CONFIG=APP_CONFIG)


@main_bp.route('/afr')
def afr_report():
    """
    Годовой финансовый отчет (AFR) - Полное раскрытие финансовой информации
    Баланс, отчет о прибылях/убытках, ключевые показатели, аудиторское заключение
    """
    session['role'] = 'insurer'
    return render_template('afr_report.html',
                          macro=MACRO_INDICATORS_2025,
                          APP_CONFIG=APP_CONFIG)


# =============================================================================
# ГЛАВНЫЙ РАСЧЕТ - UNIFIED CALCULATION (ECL + IFRS 17 + Solvency)
# =============================================================================

from app.services.unified_calculation_service import unified_calculation_service

@main_bp.route('/calculation', methods=['GET', 'POST'])
def main_calculation():
    """Главный расчет - единая система ECL, МСФО 17 и платежеспособности"""
    # Главный расчет ТОЛЬКО для страховщиков
    session['role'] = 'insurer'

    result = None
    error = None

    if request.method == 'POST':
        try:
            # Получение параметров из формы
            gca = Decimal(request.form.get('gca', '500000000'))
            pd = Decimal(request.form.get('pd', '0.095'))
            lgd = Decimal(request.form.get('lgd', '0.69'))
            eir = Decimal(request.form.get('eir', '0.19'))
            term = int(request.form.get('term', '3'))
            dpd = int(request.form.get('dpd', '0'))

            premiums = Decimal(request.form.get('premiums', '100000000'))
            claims = Decimal(request.form.get('claims', '80000000'))
            expenses = Decimal(request.form.get('expenses', '5000000'))
            ac = Decimal(request.form.get('ac', '10000000'))
            contract_term = int(request.form.get('contract_term', '10'))
            ra_method = request.form.get('ra_method', 'coc')

            equity = Decimal(request.form.get('equity', '20000000000'))
            subordinated = Decimal(request.form.get('subordinated', '3000000000'))
            illiquid = Decimal(request.form.get('illiquid', '500000000'))
            k_coef = Decimal(request.form.get('k_coef', '0.70'))
            has_osago = request.form.get('osago') == 'on'

            # Выполняем главный расчет
            calc_result = unified_calculation_service.calculate_everything(
                gross_carrying_amount=gca,
                pd_annual=pd,
                lgd=lgd,
                eir=eir,
                remaining_term=term,
                days_past_due=dpd,
                premiums=premiums,
                claims_per_year=claims,
                expenses_per_year=expenses,
                acquisition_costs=ac,
                contract_term=contract_term,
                ra_method=ra_method,
                equity=equity,
                subordinated=subordinated,
                illiquid=illiquid,
                has_osago=has_osago,
                k_coef=k_coef,
            )

            # Форматируем для шаблона
            result = {
                'calculation_date': calc_result.calculation_date.isoformat(),
                'status': calc_result.status,
                'warnings': calc_result.warnings,
                'ecl': calc_result.ecl,
                'ecl_formatted': calc_result.ecl_formatted,
                'ifrs17': calc_result.ifrs17,
                'ifrs17_formatted': calc_result.ifrs17_formatted,
                'solvency': calc_result.solvency,
                'solvency_formatted': calc_result.solvency_formatted,
            }

        except Exception as e:
            error = f"Ошибка расчета: {str(e)}"

    return render_template('main_calculation.html',
                          result=result,
                          error=error,
                          macro=MACRO_INDICATORS_2025,
                          APP_CONFIG=APP_CONFIG)


@main_bp.route('/reports')
def reports():
    """Расширенная система отчетности"""
    session['role'] = 'insurer'
    return render_template('reports_advanced.html',
                          macro=MACRO_INDICATORS_2025,
                          APP_CONFIG=APP_CONFIG)


@main_bp.route('/audit')
def audit():
    """Аудиторский след"""
    session['role'] = 'insurer'
    return render_template('audit.html',
                          macro=MACRO_INDICATORS_2025,
                          APP_CONFIG=APP_CONFIG)


# =============================================================================
# АРФР - МАРШРУТЫ РЕГУЛЯТОРА
# =============================================================================

@main_bp.route('/arfr')
@main_bp.route('/arfr/dashboard')
def arfr_dashboard():
    """Панель надзора АРФР"""
    session['role'] = 'arfr'

    # Демо-данные для панели
    stats = {
        'total_insurers': 27,
        'compliant': 24,
        'warnings': 3,
        'violations': 2,
        'total_assets': '2.8 трлн ₸',
        'total_premiums': '890 млрд ₸',
        'avg_solvency': '2.15',
    }

    return render_template('arfr/dashboard.html',
                          stats=stats,
                          macro=MACRO_INDICATORS_2025,
                          APP_CONFIG=APP_CONFIG)


@main_bp.route('/arfr/insurers')
def arfr_insurers():
    """Список страховых компаний для АРФР"""
    session['role'] = 'arfr'
    # Демо-данные по страховым компаниям
    insurers = [
        {
            'id': 1, 'name': 'СК КазСтрах', 'bin': '123456789012',
            'type': 'Композитная', 'assets': '50.0 млрд', 'solvency': 2.57,
            'status': 'ok', 'ecl': '2.1 млрд', 'csm': '11.8 млрд'
        },
        {
            'id': 2, 'name': 'СК НурПолис', 'bin': '987654321098',
            'type': 'Non-life', 'assets': '25.0 млрд', 'solvency': 1.35,
            'status': 'warning', 'ecl': '0.8 млрд', 'csm': '0'
        },
        {
            'id': 3, 'name': 'СК Евразия', 'bin': '111222333444',
            'type': 'Life', 'assets': '120.0 млрд', 'solvency': 3.21,
            'status': 'ok', 'ecl': '5.2 млрд', 'csm': '35.4 млрд'
        },
        {
            'id': 4, 'name': 'СК Халык', 'bin': '555666777888',
            'type': 'Композитная', 'assets': '85.0 млрд', 'solvency': 2.89,
            'status': 'ok', 'ecl': '3.8 млрд', 'csm': '22.1 млрд'
        },
        {
            'id': 5, 'name': 'СК Виктория', 'bin': '999000111222',
            'type': 'Non-life', 'assets': '18.0 млрд', 'solvency': 1.12,
            'status': 'danger', 'ecl': '1.5 млрд', 'csm': '0'
        },
    ]

    return render_template('arfr/insurers.html',
                          insurers=insurers,
                          macro=MACRO_INDICATORS_2025,
                          APP_CONFIG=APP_CONFIG)


@main_bp.route('/arfr/reports')
def arfr_reports():
    """Проверка отчетности АРФР"""
    session['role'] = 'arfr'
    # Демо-данные по отчетам на проверке
    reports = [
        {
            'id': 1, 'insurer': 'СК НурПолис', 'type': 'Квартальный',
            'period': 'Q3 2025', 'submitted': '15.10.2025',
            'status': 'review', 'issues': 2
        },
        {
            'id': 2, 'insurer': 'СК Виктория', 'type': 'Ежемесячный',
            'period': 'Октябрь 2025', 'submitted': '05.11.2025',
            'status': 'issues', 'issues': 5
        },
        {
            'id': 3, 'insurer': 'СК КазСтрах', 'type': 'Квартальный',
            'period': 'Q3 2025', 'submitted': '14.10.2025',
            'status': 'pending', 'issues': 0
        },
    ]

    return render_template('arfr/reports.html',
                          reports=reports,
                          macro=MACRO_INDICATORS_2025,
                          APP_CONFIG=APP_CONFIG)


@main_bp.route('/arfr/violations')
def arfr_violations():
    """Нарушения - АРФР"""
    session['role'] = 'arfr'
    violations = [
        {
            'id': 1, 'insurer': 'СК Виктория', 'type': 'Nmп < 1.0',
            'description': 'Коэффициент платежеспособности ниже минимума',
            'date': '10.11.2025', 'severity': 'critical',
            'status': 'open', 'deadline': '10.12.2025'
        },
        {
            'id': 2, 'insurer': 'СК НурПолис', 'type': 'ECL',
            'description': 'Недостаточный резерв ECL по портфелю облигаций',
            'date': '08.11.2025', 'severity': 'warning',
            'status': 'in_progress', 'deadline': '08.12.2025'
        },
    ]

    return render_template('arfr/violations.html',
                          violations=violations,
                          macro=MACRO_INDICATORS_2025,
                          APP_CONFIG=APP_CONFIG)


@main_bp.route('/arfr/market')
def arfr_market():
    """Аналитика рынка страхования"""
    session['role'] = 'arfr'
    market_data = {
        'total_premiums': '890 млрд ₸',
        'yoy_growth': '+12.5%',
        'life_share': '35%',
        'nonlife_share': '65%',
        'osago_premiums': '180 млрд ₸',
        'top_5_share': '68%',
    }

    return render_template('arfr/market.html',
                          market_data=market_data,
                          macro=MACRO_INDICATORS_2025,
                          APP_CONFIG=APP_CONFIG)


@main_bp.route('/arfr/stress')
def arfr_stress():
    """Стресс-тесты рынка - АРФР"""
    session['role'] = 'arfr'
    return render_template('arfr/stress.html',
                          macro=MACRO_INDICATORS_2025,
                          APP_CONFIG=APP_CONFIG)


@main_bp.route('/arfr/compliance')
def arfr_compliance():
    """Проверка нормативного соответствия (МСФО 9/17, Solvency 2) - АРФР"""
    session['role'] = 'arfr'

    # Примеры проверки соответствия для каждой страховой компании
    compliance_checks = [
        {
            'insurer': 'СК КазСтрах',
            'bin': '123456789012',
            'ifrs9_ecl': {
                'status': 'compliant',
                'check': 'ECL стадия 1 - Нет SICR',
                'coverage_ratio': 4.2,
                'required': 0.5,
                'note': 'Резерв превышает требования'
            },
            'ifrs17_insurance': {
                'status': 'compliant',
                'check': 'BEL/RA/CSM рассчитаны по GMM',
                'onerous_count': 0,
                'total_contracts': 450,
                'note': 'Нет тяжелых договоров'
            },
            'solvency2': {
                'status': 'compliant',
                'nmp_ratio': 2.57,
                'required': 1.0,
                'stress_adverse': 1.85,
                'stress_severe': 1.23,
                'note': 'Хорошая платежеспособность'
            }
        },
        {
            'insurer': 'СК НурПолис',
            'bin': '987654321098',
            'ifrs9_ecl': {
                'status': 'warning',
                'check': 'ECL стадия 2 - SICR выявлен',
                'coverage_ratio': 1.8,
                'required': 0.5,
                'note': 'Дополнительный мониторинг требуется'
            },
            'ifrs17_insurance': {
                'status': 'warning',
                'check': 'Обнаружены признаки тяжелых договоров',
                'onerous_count': 3,
                'total_contracts': 125,
                'note': 'Требуется корректировка пакета премий'
            },
            'solvency2': {
                'status': 'warning',
                'nmp_ratio': 1.35,
                'required': 1.0,
                'stress_adverse': 0.92,
                'stress_severe': 0.65,
                'note': 'Требуется план восстановления капитала'
            }
        },
        {
            'insurer': 'СК Виктория',
            'bin': '999000111222',
            'ifrs9_ecl': {
                'status': 'critical',
                'check': 'ECL стадия 3 - Default',
                'coverage_ratio': 0.5,
                'required': 1.0,
                'note': 'Критический недостаток резервов'
            },
            'ifrs17_insurance': {
                'status': 'critical',
                'check': 'Множественные убыточные договоры',
                'onerous_count': 25,
                'total_contracts': 78,
                'note': 'Требуется срочное восстановление платежеспособности'
            },
            'solvency2': {
                'status': 'critical',
                'nmp_ratio': 1.12,
                'required': 1.0,
                'stress_adverse': 0.45,
                'stress_severe': 0.22,
                'note': 'НАРУШЕНИЕ - Немедленное действие АРФР'
            }
        },
    ]

    return render_template('arfr/compliance.html',
                          compliance_checks=compliance_checks,
                          macro=MACRO_INDICATORS_2025,
                          APP_CONFIG=APP_CONFIG)


# =============================================================================
# ФГСВ - МАРШРУТЫ ФОНДА ГАРАНТИРОВАНИЯ
# =============================================================================

@main_bp.route('/fgsv-info')
@main_bp.route('/fgsv-info/dashboard')
def fgsv_info():
    """Информация о ФГСВ для страховщиков и других ролей (read-only)"""
    session['role'] = 'insurer'
    stats = {
        'fund_balance': '50 млрд ₸',
        'total_contributions': '8.2 млрд ₸',
        'expected_payouts': '2.1 млрд ₸',
        'adequacy_ratio': '2.38',
        'insurers_monitored': 27,
        'high_risk': 3,
    }

    # Используем ту же шаблон, но отметим что это read-only версия
    return render_template('fgsv_info/dashboard.html',
                          stats=stats,
                          is_admin=False,
                          macro=MACRO_INDICATORS_2025,
                          APP_CONFIG=APP_CONFIG)


@main_bp.route('/fgsv-panel')
@main_bp.route('/fgsv-panel/dashboard')
def fgsv_dashboard():
    """Панель ФГСВ - ТОЛЬКО для администраторов ФГСВ"""
    # Страховщики могут только ПРОСМАТРИВАТЬ информацию о ФГСВ через read-only страницы
    # Полная административная панель ТОЛЬКО для роли 'fgsv'
    if session.get('role') != 'fgsv':
        # Перенаправляем на информационный просмотр для других ролей
        return redirect(url_for('main.fgsv_info'))

    stats = {
        'fund_balance': '50 млрд ₸',
        'total_contributions': '8.2 млрд ₸',
        'expected_payouts': '2.1 млрд ₸',
        'adequacy_ratio': '2.38',
        'insurers_monitored': 27,
        'high_risk': 3,
    }

    return render_template('fgsv_panel/dashboard.html',
                          stats=stats,
                          macro=MACRO_INDICATORS_2025,
                          APP_CONFIG=APP_CONFIG)


@main_bp.route('/fgsv-panel/contributions')
def fgsv_contributions():
    """Взносы в ФГСВ"""
    session['role'] = 'fgsv'
    contributions = [
        {
            'insurer': 'СК КазСтрах', 'premiums': '35 млрд ₸',
            'rate': '0.5%', 'amount': '175 млн ₸',
            'risk_class': 'low', 'status': 'paid', 'date': '15.10.2025'
        },
        {
            'insurer': 'СК НурПолис', 'premiums': '12 млрд ₸',
            'rate': '1.0%', 'amount': '120 млн ₸',
            'risk_class': 'medium', 'status': 'paid', 'date': '14.10.2025'
        },
        {
            'insurer': 'СК Виктория', 'premiums': '5 млрд ₸',
            'rate': '2.0%', 'amount': '100 млн ₸',
            'risk_class': 'high', 'status': 'pending', 'date': '-'
        },
    ]

    return render_template('fgsv_panel/contributions.html',
                          contributions=contributions,
                          macro=MACRO_INDICATORS_2025,
                          APP_CONFIG=APP_CONFIG)


@main_bp.route('/fgsv-panel/insurers')
def fgsv_insurers():
    """Страховщики - мониторинг ФГСВ"""
    session['role'] = 'fgsv'
    insurers = [
        {
            'name': 'СК КазСтрах', 'solvency': 2.57, 'loss_ratio': 0.55,
            'combined': 0.85, 'pd': 0.02, 'risk_class': 'low'
        },
        {
            'name': 'СК НурПолис', 'solvency': 1.35, 'loss_ratio': 0.71,
            'combined': 0.98, 'pd': 0.08, 'risk_class': 'medium'
        },
        {
            'name': 'СК Виктория', 'solvency': 1.12, 'loss_ratio': 0.82,
            'combined': 1.05, 'pd': 0.15, 'risk_class': 'high'
        },
    ]

    return render_template('fgsv_panel/insurers.html',
                          insurers=insurers,
                          macro=MACRO_INDICATORS_2025,
                          APP_CONFIG=APP_CONFIG)


@main_bp.route('/fgsv-panel/bankruptcy')
def fgsv_bankruptcy():
    """Риск банкротства - ФГСВ"""
    session['role'] = 'fgsv'
    risk_data = {
        'high_risk_count': 3,
        'expected_defaults': 0.8,
        'expected_loss': '1.2 млрд ₸',
        'var_95': '2.5 млрд ₸',
        'var_99': '4.1 млрд ₸',
    }

    return render_template('fgsv_panel/bankruptcy.html',
                          risk_data=risk_data,
                          macro=MACRO_INDICATORS_2025,
                          APP_CONFIG=APP_CONFIG)


@main_bp.route('/fgsv-panel/payouts')
def fgsv_payouts():
    """История выплат ФГСВ"""
    session['role'] = 'fgsv'
    payouts = [
        {
            'year': 2024, 'insurer': 'СК Альянс (ликвидирована)',
            'claims': 1250, 'amount': '1.8 млрд ₸', 'recovery': '720 млн ₸'
        },
        {
            'year': 2023, 'insurer': 'СК Гарант (ликвидирована)',
            'claims': 580, 'amount': '650 млн ₸', 'recovery': '195 млн ₸'
        },
    ]

    return render_template('fgsv_panel/payouts.html',
                          payouts=payouts,
                          macro=MACRO_INDICATORS_2025,
                          APP_CONFIG=APP_CONFIG)


@main_bp.route('/fgsv-panel/simulation')
def fgsv_simulation():
    """Monte Carlo моделирование - ФГСВ"""
    session['role'] = 'fgsv'
    return render_template('fgsv_panel/simulation.html',
                          macro=MACRO_INDICATORS_2025,
                          APP_CONFIG=APP_CONFIG)


# =============================================================================
# РЕЕСТРЫ - ПОРТФЕЛИ ДОГОВОРОВ И ИНСТРУМЕНТОВ
# =============================================================================

@main_bp.route('/contracts-registry')
def contracts_registry():
    """Реестр договоров страхования (МСФО 17)"""
    session['role'] = 'insurer'
    return render_template('contracts_registry.html',
                          macro=MACRO_INDICATORS_2025,
                          APP_CONFIG=APP_CONFIG)


@main_bp.route('/instruments-registry')
def instruments_registry():
    """Реестр финансовых инструментов (МСФО 9)"""
    session['role'] = 'insurer'
    return render_template('instruments_registry.html',
                          macro=MACRO_INDICATORS_2025,
                          APP_CONFIG=APP_CONFIG)


# =============================================================================
# ПАКЕТНЫЕ РАСЧЕТЫ (BATCH PROCESSING) - ENTERPRISE FEATURE
# =============================================================================

from app.services.batch_processing_service import batch_processing_service
from app.enterprise_models import CalculationRun, InsuranceType, ContractType


@main_bp.route('/calculations/runs')
def calculation_runs():
    """
    История пакетных расчетов

    КРИТИЧНО: В production системе расчеты НЕ выполняются вручную для каждого договора.
    Пользователь запускает JOB, который обрабатывает весь портфель.
    """
    session['role'] = 'insurer'
    # Получаем последние 20 расчетов
    runs = batch_processing_service.get_recent_runs(limit=20)

    return render_template('calculations/runs.html',
                          runs=runs,
                          macro=MACRO_INDICATORS_2025,
                          APP_CONFIG=APP_CONFIG)


@main_bp.route('/calculations/new', methods=['GET', 'POST'])
def new_calculation_run():
    """Запуск нового пакетного расчета"""
    session['role'] = 'insurer'
    if request.method == 'POST':
        try:
            # Параметры расчета
            calculation_type = request.form.get('calculation_type', 'ifrs17')
            reporting_date_str = request.form.get('reporting_date')
            description = request.form.get('description')

            # Фильтры портфеля
            portfolio_filter = {}
            if request.form.get('insurance_type'):
                portfolio_filter['insurance_type'] = InsuranceType(request.form.get('insurance_type'))
            if request.form.get('cohort_year'):
                portfolio_filter['cohort_year'] = int(request.form.get('cohort_year'))
            if request.form.get('contract_type'):
                portfolio_filter['contract_type'] = ContractType(request.form.get('contract_type'))

            # Парсим дату
            if reporting_date_str:
                reporting_date = datetime.strptime(reporting_date_str, '%Y-%m-%d').date()
            else:
                reporting_date = date.today()

            # Создаем расчет
            run = batch_processing_service.create_calculation_run(
                calculation_type=calculation_type,
                reporting_date=reporting_date,
                description=description,
                portfolio_filter=portfolio_filter if portfolio_filter else None
            )

            # Запускаем выполнение в фоне
            # TODO: В production использовать Celery/RQ для асинхронного выполнения
            result = batch_processing_service.execute_calculation_run(
                run_id=run.id,
                portfolio_filter=portfolio_filter if portfolio_filter else None
            )

            if result['status'] == 'success':
                flash(f'Расчет {run.run_code} успешно выполнен! Обработано групп: {result["processed"]}', 'success')
            else:
                flash(f'Ошибка выполнения расчета: {result.get("message")}', 'danger')

            return redirect(url_for('main.calculation_run_detail', run_id=run.id))

        except Exception as e:
            flash(f'Ошибка создания расчета: {str(e)}', 'danger')
            return redirect(url_for('main.calculation_runs'))

    # GET - показываем форму
    return render_template('calculations/new_run.html',
                          macro=MACRO_INDICATORS_2025,
                          APP_CONFIG=APP_CONFIG)


@main_bp.route('/calculations/run/<int:run_id>')
def calculation_run_detail(run_id):
    """Детальная информация по расчету"""
    session['role'] = 'insurer'
    run = CalculationRun.query.get_or_404(run_id)

    # Получаем результаты по группам
    from app.enterprise_models import GroupCalculationResult
    group_results = GroupCalculationResult.query.filter_by(
        calculation_run_id=run_id
    ).order_by(GroupCalculationResult.total_liability.desc()).limit(50).all()

    # Получаем логи ошибок
    from app.enterprise_models import CalculationLog
    error_logs = CalculationLog.query.filter_by(
        calculation_run_id=run_id,
        calculation_type='ERROR'
    ).all()

    return render_template('calculations/run_detail.html',
                          run=run,
                          group_results=group_results,
                          error_logs=error_logs,
                          macro=MACRO_INDICATORS_2025,
                          APP_CONFIG=APP_CONFIG)


@main_bp.route('/api/calculations/run/<int:run_id>/status')
def api_calculation_status(run_id):
    """
    API для получения статуса расчета (для AJAX polling)

    Используется для обновления прогресс-бара в реальном времени
    """
    status = batch_processing_service.get_run_status(run_id)
    return jsonify(status)


# =============================================================================
# JOURNAL ENTRY GENERATOR - АВТОМАТИЧЕСКОЕ СОЗДАНИЕ ПРОВОДОК
# =============================================================================

from app.services.journal_entry_generator_service import journal_entry_generator_service

@main_bp.route('/api/calculations/run/<int:run_id>/generate-entries', methods=['POST'])
def api_generate_entries(run_id):
    """
    API для генерирования проводок из результатов расчета

    POST /api/calculations/run/123/generate-entries
    Returns: {status, total_entries_created, total_amount, by_event_type}
    """
    try:
        result = journal_entry_generator_service.generate_entries_for_run(run_id=run_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@main_bp.route('/api/calculations/run/<int:run_id>/entries-summary', methods=['GET'])
def api_entries_summary(run_id):
    """
    Получить сводку по созданным проводкам

    GET /api/calculations/run/123/entries-summary
    Returns: {total_entries, posted_entries, pending_entries, by_event_type}
    """
    summary = journal_entry_generator_service.get_entry_summary(run_id)
    return jsonify(summary)


@main_bp.route('/api/calculations/run/<int:run_id>/post-entries', methods=['POST'])
def api_post_entries(run_id):
    """
    Проводить созданные проводки в главную книгу (необратимо!)

    POST /api/calculations/run/123/post-entries
    """
    result = journal_entry_generator_service.post_entries(run_id)
    return jsonify(result)


# =============================================================================
# ACCOUNTING ENGINE - НАСТРОЙКА МАППИНГА
# =============================================================================

from app.enterprise_models import ChartOfAccounts, AccountingRule, AccountingEventType


@main_bp.route('/accounting/chart-of-accounts')
def chart_of_accounts():
    """План счетов (Chart of Accounts)"""
    session['role'] = 'insurer'
    accounts = ChartOfAccounts.query.order_by(ChartOfAccounts.account_code).all()

    return render_template('accounting/chart_of_accounts.html',
                          accounts=accounts,
                          macro=MACRO_INDICATORS_2025,
                          APP_CONFIG=APP_CONFIG)


@main_bp.route('/accounting/mapping-rules')
def accounting_mapping_rules():
    """
    Правила маппинга событий на счета

    КРИТИЧНО: Это "мозг" Accounting Engine.
    Определяет какие проводки генерировать для каждого события.
    """
    session['role'] = 'insurer'
    rules = AccountingRule.query.order_by(
        AccountingRule.event_type,
        AccountingRule.priority
    ).all()

    # Группируем правила по типу события
    rules_by_event = {}
    for rule in rules:
        event_name = rule.event_type.value
        if event_name not in rules_by_event:
            rules_by_event[event_name] = []
        rules_by_event[event_name].append(rule)

    # Список всех возможных событий
    all_events = [e for e in AccountingEventType]

    return render_template('accounting/mapping_rules.html',
                          rules=rules,
                          rules_by_event=rules_by_event,
                          all_events=all_events,
                          macro=MACRO_INDICATORS_2025,
                          APP_CONFIG=APP_CONFIG)


@main_bp.route('/accounting/mapping-rules/new', methods=['GET', 'POST'])
def new_accounting_rule():
    """Создание нового правила маппинга"""
    session['role'] = 'insurer'
    if request.method == 'POST':
        try:
            # Получаем данные из формы
            event_type = AccountingEventType(request.form.get('event_type'))
            debit_account = request.form.get('debit_account')
            credit_account = request.form.get('credit_account')
            description = request.form.get('description')
            priority = int(request.form.get('priority', 100))

            # Фильтры (опционально)
            insurance_type_str = request.form.get('insurance_type')
            contract_type_str = request.form.get('contract_type')
            measurement_model_str = request.form.get('measurement_model')

            # Создаем правило
            rule = AccountingRule(
                event_type=event_type,
                debit_account_code=debit_account,
                credit_account_code=credit_account,
                description=description,
                priority=priority,
                is_active=True
            )

            # Добавляем фильтры если указаны
            if insurance_type_str:
                rule.insurance_type = InsuranceType(insurance_type_str)
            if contract_type_str:
                rule.contract_type = ContractType(contract_type_str)
            if measurement_model_str:
                rule.measurement_model = MeasurementModel(measurement_model_str)

            db.session.add(rule)
            db.session.commit()

            flash(f'Правило маппинга успешно создано!', 'success')
            return redirect(url_for('main.accounting_mapping_rules'))

        except Exception as e:
            flash(f'Ошибка создания правила: {str(e)}', 'danger')
            return redirect(url_for('main.new_accounting_rule'))

    # GET - показываем форму
    accounts = ChartOfAccounts.query.filter_by(is_active=True).order_by(ChartOfAccounts.account_code).all()
    all_events = [e for e in AccountingEventType]

    return render_template('accounting/new_rule.html',
                          accounts=accounts,
                          all_events=all_events,
                          macro=MACRO_INDICATORS_2025,
                          APP_CONFIG=APP_CONFIG)


@main_bp.route('/accounting/journal-entries')
def journal_entries():
    """Журнал проводок (Sub-ledger)"""
    session['role'] = 'insurer'
    from app.enterprise_models import JournalEntry
    from app import db
    from sqlalchemy import func

    # Получаем последние 100 проводок
    entries = JournalEntry.query.order_by(
        JournalEntry.posting_date.desc(),
        JournalEntry.entry_number.desc()
    ).limit(100).all()

    # Статистика
    total_entries = JournalEntry.query.count()
    posted_entries = JournalEntry.query.filter_by(is_posted=True).count()
    total_amount = db.session.query(func.sum(JournalEntry.amount)).scalar() or 0

    stats = {
        'total_entries': total_entries,
        'posted_entries': posted_entries,
        'pending_entries': total_entries - posted_entries,
        'total_amount': total_amount
    }

    return render_template('accounting/journal_entries.html',
                          entries=entries,
                          stats=stats,
                          macro=MACRO_INDICATORS_2025,
                          APP_CONFIG=APP_CONFIG)


# =============================================================================
# REINSURANCE ANALYSIS - АНАЛИЗ ПЕРЕСТРАХОВАНИЯ
# =============================================================================

from app.services.reinsurance_service import reinsurance_service

@main_bp.route('/api/calculations/run/<int:run_id>/reinsurance/portfolio', methods=['GET'])
def api_portfolio_net_gross(run_id):
    """
    Получить анализ портфеля: нетто/брутто разбор по типам договоров

    GET /api/calculations/run/123/reinsurance/portfolio
    """
    result = reinsurance_service.calculate_portfolio_net_gross(run_id)
    return jsonify(result)


@main_bp.route('/api/calculations/run/<int:run_id>/reinsurance/metrics', methods=['GET'])
def api_reinsurance_metrics(run_id):
    """
    Получить ключевые метрики перестрахования

    GET /api/calculations/run/123/reinsurance/metrics
    Returns: {cession_ratio, net_gross_ratio, relief_ratio, direct_ratio}
    """
    result = reinsurance_service.get_reinsurance_metrics(run_id)
    return jsonify(result)


@main_bp.route('/api/group-result/<int:result_id>/net-gross', methods=['GET'])
def api_group_net_gross(result_id):
    """
    Получить нетто/брутто разбор для конкретной группы

    GET /api/group-result/456/net-gross
    """
    result = reinsurance_service.get_group_net_gross(result_id)
    return jsonify(result)


@main_bp.route('/analytics/reinsurance', methods=['GET'])
def reinsurance_analysis():
    """Страница анализа перестрахования с Net/Gross разбором"""
    session['role'] = 'insurer'
    return render_template('analytics/reinsurance_analysis.html',
                          macro=MACRO_INDICATORS_2025,
                          APP_CONFIG=APP_CONFIG)


# =============================================================================
# YIELD CURVE MANAGEMENT - УПРАВЛЕНИЕ КРИВЫМИ ДОХОДНОСТИ
# =============================================================================

from app.services.yield_curve_service import yield_curve_service

@main_bp.route('/yield-curves', methods=['GET'])
def yield_curves_list():
    """Страница со списком всех кривых доходности"""
    session['role'] = 'insurer'
    result = yield_curve_service.list_curves()
    curves = result.get('curves', [])
    return render_template('analytics/yield_curves.html',
                          curves=curves,
                          macro=MACRO_INDICATORS_2025,
                          APP_CONFIG=APP_CONFIG)


@main_bp.route('/api/yield-curves', methods=['GET'])
def api_list_yield_curves():
    """
    Получить список всех кривых

    GET /api/yield-curves?type=risk_free&active=true
    """
    curve_type = request.args.get('type')
    active_only = request.args.get('active', 'true').lower() == 'true'
    
    result = yield_curve_service.list_curves(
        curve_type=curve_type,
        active_only=active_only
    )
    return jsonify(result)


@main_bp.route('/api/yield-curves', methods=['POST'])
def api_create_yield_curve():
    """
    Создать новую кривую доходности

    POST /api/yield-curves
    {
        "curve_name": "RFR_KZT_2025Q4",
        "curve_type": "risk_free",
        "reference_date": "2025-12-31",
        "curve_points": [
            {"term": 1, "rate": 0.05},
            {"term": 5, "rate": 0.06},
            {"term": 10, "rate": 0.065}
        ]
    }
    """
    try:
        data = request.get_json()
        result = yield_curve_service.create_yield_curve(
            curve_name=data.get('curve_name'),
            curve_type=data.get('curve_type'),
            reference_date=datetime.strptime(data.get('reference_date'), '%Y-%m-%d').date(),
            description=data.get('description'),
            curve_points=data.get('curve_points', [])
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400


@main_bp.route('/api/yield-curves/<int:curve_id>', methods=['GET'])
def api_get_yield_curve(curve_id):
    """
    Получить полные данные кривой (с интерполированными точками)

    GET /api/yield-curves/123
    """
    result = yield_curve_service.get_curve_data(curve_id)
    return jsonify(result)


@main_bp.route('/api/yield-curves/<int:curve_id>/points', methods=['PUT'])
def api_update_curve_points(curve_id):
    """
    Обновить точки кривой

    PUT /api/yield-curves/123/points
    {
        "curve_points": [
            {"term": 1, "rate": 0.05},
            {"term": 5, "rate": 0.06}
        ]
    }
    """
    try:
        data = request.get_json()
        result = yield_curve_service.update_curve_points(
            curve_id=curve_id,
            curve_points=data.get('curve_points', [])
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400


@main_bp.route('/api/yield-curves/<int:curve_id>/rate', methods=['GET'])
def api_get_rate_for_term(curve_id):
    """
    Получить ставку для конкретного срока

    GET /api/yield-curves/123/rate?term=5.5
    """
    try:
        term = float(request.args.get('term', 0))
        result = yield_curve_service.get_rate_for_term(curve_id, term)
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400


@main_bp.route('/api/yield-curves/<int:curve_id>/discount-factor', methods=['GET'])
def api_calculate_discount_factor(curve_id):
    """
    Вычислить дисконт-фактор

    GET /api/yield-curves/123/discount-factor?term=5&compounding=annual
    """
    try:
        term = float(request.args.get('term', 0))
        compounding = request.args.get('compounding', 'annual')
        
        result = yield_curve_service.calculate_discount_factor(
            curve_id=curve_id,
            term_years=term,
            compounding=compounding
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400


@main_bp.route('/api/yield-curves/<int:curve_id>/set-active', methods=['POST'])
def api_set_active_curve(curve_id):
    """
    Установить кривую как активную для типа

    POST /api/yield-curves/123/set-active
    {"curve_type": "risk_free"}
    """
    try:
        data = request.get_json()
        result = yield_curve_service.set_active_curve(
            curve_id=curve_id,
            curve_type=data.get('curve_type')
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400


# =============================================================================
# ГЕНЕРАТОР ОТЧЁТОВ
# =============================================================================

@main_bp.route('/reports/generator')
def reports_generator():
    """
    Генератор регуляторных отчётов

    Страница для выбора и генерации отчётов по:
    - Постановление №85: Формы отчётности
    - Постановление №86: Платёжеспособность
    - Постановление №304: Страховые резервы
    """
    session['role'] = 'insurer'
    return render_template('reports/generator.html',
                          macro=MACRO_INDICATORS_2025,
                          APP_CONFIG=APP_CONFIG)


# =============================================================================
# РЕГУЛЯТОРНАЯ ОТЧЁТНОСТЬ - ПОСТАНОВЛЕНИЯ АРРФР №85, №86, №304
# =============================================================================

from app.modules.regulatory_reports import (
    regulatory_report_service,
    ReportFrequency,
    FORMS_REGULATION_85,
    FORMS_REGULATION_86,
    FORMS_REGULATION_304
)


@main_bp.route('/regulatory')
@main_bp.route('/regulatory/dashboard')
def regulatory_dashboard():
    """
    Панель регуляторной отчётности

    Включает:
    - Постановление №85: Формы отчётности страховых организаций
    - Постановление №86: Требования к платёжеспособности
    - Постановление №304: Правила формирования страховых резервов
    """
    session['role'] = 'insurer'

    # Получаем ближайшие дедлайны
    upcoming_deadlines = regulatory_report_service.get_upcoming_deadlines(date.today())[:10]

    # Статистика по формам
    stats = {
        'total_forms': len(regulatory_report_service.all_forms),
        'monthly_forms': len(regulatory_report_service.get_forms_by_frequency(ReportFrequency.MONTHLY)),
        'quarterly_forms': len(regulatory_report_service.get_forms_by_frequency(ReportFrequency.QUARTERLY)),
        'annual_forms': len(regulatory_report_service.get_forms_by_frequency(ReportFrequency.ANNUAL)),
        'forms_85': len(FORMS_REGULATION_85),
        'forms_86': len(FORMS_REGULATION_86),
        'forms_304': len(FORMS_REGULATION_304),
    }

    return render_template('regulatory/dashboard.html',
                          stats=stats,
                          upcoming_deadlines=upcoming_deadlines,
                          macro=MACRO_INDICATORS_2025,
                          APP_CONFIG=APP_CONFIG)


@main_bp.route('/regulatory/forms')
def regulatory_forms():
    """Список всех форм регуляторной отчётности"""
    session['role'] = 'insurer'

    regulation = request.args.get('regulation')
    frequency = request.args.get('frequency')

    if regulation:
        forms = regulatory_report_service.get_forms_by_regulation(regulation)
    elif frequency:
        forms = regulatory_report_service.get_forms_by_frequency(ReportFrequency(frequency))
    else:
        forms = regulatory_report_service.all_forms

    return render_template('regulatory/forms.html',
                          forms=forms,
                          selected_regulation=regulation,
                          selected_frequency=frequency,
                          macro=MACRO_INDICATORS_2025,
                          APP_CONFIG=APP_CONFIG)


@main_bp.route('/regulatory/solvency')
def regulatory_solvency():
    """
    Расчёт платёжеспособности по Постановлению №86

    Включает:
    - ФМП (Фактическая маржа платёжеспособности)
    - НМП (Нормативная маржа платёжеспособности)
    - МГФ (Минимальный гарантийный фонд)
    """
    session['role'] = 'insurer'

    # Демо-данные для расчёта
    demo_result = regulatory_report_service.calculate_solvency_margin(
        equity_capital=Decimal('25000000000'),
        subordinated_debt=Decimal('5000000000'),
        intangible_assets=Decimal('500000000'),
        deferred_acquisition_costs=Decimal('1200000000'),
        gross_premiums_written=Decimal('35000000000'),
        gross_claims_paid=Decimal('22000000000'),
        reinsurance_ceded_ratio=Decimal('0.25'),
        insurance_type='non_life'
    )

    return render_template('regulatory/solvency.html',
                          result=demo_result,
                          forms=FORMS_REGULATION_86,
                          macro=MACRO_INDICATORS_2025,
                          APP_CONFIG=APP_CONFIG)


@main_bp.route('/regulatory/reserves')
def regulatory_reserves():
    """
    Страховые резервы по Постановлению №304

    Включает:
    - РНП (Резерв незаработанной премии)
    - РЗУ (Резерв заявленных убытков)
    - РПНУ/IBNR (Резерв произошедших, но незаявленных убытков)
    - РПЗУ (Резерв расходов на урегулирование)
    - Стабилизационный резерв
    """
    session['role'] = 'insurer'

    # Демо-расчёт РНП
    demo_rnpp = regulatory_report_service.calculate_rnpp(
        premium_amount=Decimal('1000000000'),
        inception_date=date(2025, 6, 1),
        expiry_date=date(2026, 5, 31),
        calculation_date=date.today(),
        method='pro_rata'
    )

    return render_template('regulatory/reserves.html',
                          rnpp_demo=demo_rnpp,
                          forms=FORMS_REGULATION_304,
                          macro=MACRO_INDICATORS_2025,
                          APP_CONFIG=APP_CONFIG)


@main_bp.route('/regulatory/reports-85')
def regulatory_reports_85():
    """Формы отчётности по Постановлению №85"""
    session['role'] = 'insurer'
    return render_template('regulatory/reports_85.html',
                          forms=FORMS_REGULATION_85,
                          macro=MACRO_INDICATORS_2025,
                          APP_CONFIG=APP_CONFIG)


# =============================================================================
# API РЕГУЛЯТОРНОЙ ОТЧЁТНОСТИ
# =============================================================================

@main_bp.route('/api/regulatory/forms', methods=['GET'])
def api_regulatory_forms():
    """
    API: Получить список форм отчётности

    GET /api/regulatory/forms?regulation=85&frequency=quarterly
    """
    regulation = request.args.get('regulation')
    frequency = request.args.get('frequency')

    if regulation:
        forms = regulatory_report_service.get_forms_by_regulation(regulation)
    elif frequency:
        forms = regulatory_report_service.get_forms_by_frequency(ReportFrequency(frequency))
    else:
        forms = regulatory_report_service.all_forms

    return jsonify({
        'status': 'success',
        'data': {
            'forms': [
                {
                    'form_code': f.form_code,
                    'form_name': f.form_name,
                    'form_name_kz': f.form_name_kz,
                    'regulation_number': f.regulation_number,
                    'frequency': f.frequency.value,
                    'deadline_days': f.deadline_days,
                    'description': f.description,
                    'is_mandatory': f.is_mandatory
                }
                for f in forms
            ],
            'total': len(forms)
        }
    })


@main_bp.route('/api/regulatory/deadlines', methods=['GET'])
def api_regulatory_deadlines():
    """
    API: Получить ближайшие дедлайны сдачи отчётности

    GET /api/regulatory/deadlines?reference_date=2025-12-31&limit=10
    """
    reference_date_str = request.args.get('reference_date')
    limit = int(request.args.get('limit', 20))

    if reference_date_str:
        reference_date = datetime.strptime(reference_date_str, '%Y-%m-%d').date()
    else:
        reference_date = date.today()

    deadlines = regulatory_report_service.get_upcoming_deadlines(reference_date)[:limit]

    return jsonify({
        'status': 'success',
        'data': {
            'reference_date': reference_date.isoformat(),
            'deadlines': [
                {
                    'form_code': d['form_code'],
                    'form_name': d['form_name'],
                    'regulation': d['regulation'],
                    'deadline': d['deadline'].isoformat(),
                    'days_remaining': d['days_remaining']
                }
                for d in deadlines
            ]
        }
    })


@main_bp.route('/api/regulatory/solvency/calculate', methods=['POST'])
def api_calculate_solvency():
    """
    API: Расчёт платёжеспособности по Постановлению №86

    POST /api/regulatory/solvency/calculate
    {
        "equity_capital": "25000000000",
        "subordinated_debt": "5000000000",
        "intangible_assets": "500000000",
        "deferred_acquisition_costs": "1200000000",
        "gross_premiums_written": "35000000000",
        "gross_claims_paid": "22000000000",
        "reinsurance_ceded_ratio": "0.25",
        "insurance_type": "non_life"
    }
    """
    try:
        data = request.get_json()

        result = regulatory_report_service.calculate_solvency_margin(
            equity_capital=Decimal(data.get('equity_capital', '0')),
            subordinated_debt=Decimal(data.get('subordinated_debt', '0')),
            intangible_assets=Decimal(data.get('intangible_assets', '0')),
            deferred_acquisition_costs=Decimal(data.get('deferred_acquisition_costs', '0')),
            gross_premiums_written=Decimal(data.get('gross_premiums_written', '0')),
            gross_claims_paid=Decimal(data.get('gross_claims_paid', '0')),
            reinsurance_ceded_ratio=Decimal(data.get('reinsurance_ceded_ratio', '0')),
            insurance_type=data.get('insurance_type', 'non_life')
        )

        return jsonify({
            'status': 'success',
            'data': {
                'reporting_date': result.reporting_date.isoformat(),
                'fmp': {
                    'equity_capital': str(result.equity_capital),
                    'subordinated_debt': str(result.subordinated_debt),
                    'intangible_assets': str(result.intangible_assets),
                    'deferred_acquisition_costs': str(result.deferred_acquisition_costs),
                    'fmp_calculated': str(result.fmp_calculated)
                },
                'nmp': {
                    'nmp_by_premiums': str(result.nmp_by_premiums),
                    'nmp_by_claims': str(result.nmp_by_claims),
                    'nmp_calculated': str(result.nmp_calculated)
                },
                'solvency_ratio': str(result.solvency_ratio),
                'mgf': {
                    'required': str(result.mgf_required),
                    'actual': str(result.mgf_actual)
                },
                'is_compliant': result.is_compliant,
                'violations': result.violations,
                'regulatory_reference': 'Постановление АРРФР №86'
            }
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400


@main_bp.route('/api/regulatory/reserves/rnpp/calculate', methods=['POST'])
def api_calculate_rnpp():
    """
    API: Расчёт РНП по Постановлению №304

    POST /api/regulatory/reserves/rnpp/calculate
    {
        "premium_amount": "1000000000",
        "inception_date": "2025-06-01",
        "expiry_date": "2026-05-31",
        "calculation_date": "2025-12-31",
        "method": "pro_rata"
    }
    """
    try:
        data = request.get_json()

        result = regulatory_report_service.calculate_rnpp(
            premium_amount=Decimal(data.get('premium_amount', '0')),
            inception_date=datetime.strptime(data['inception_date'], '%Y-%m-%d').date(),
            expiry_date=datetime.strptime(data['expiry_date'], '%Y-%m-%d').date(),
            calculation_date=datetime.strptime(data['calculation_date'], '%Y-%m-%d').date(),
            method=data.get('method', 'pro_rata')
        )

        return jsonify({
            'status': 'success',
            'data': {
                'reserve_type': result.reserve_type.value,
                'calculation_date': result.calculation_date.isoformat(),
                'method': result.calculation_method,
                'gross_amount': str(result.gross_amount),
                'reserve_amount': str(result.reserve_amount),
                'formula_display': result.formula_display,
                'parameters': result.parameters,
                'regulatory_reference': 'Постановление АРРФР №304'
            }
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400


# =============================================================================
# API МСФО 17 - РАСШИРЕННЫЕ РАСЧЁТЫ
# =============================================================================

from app.modules.ifrs17_enhanced import (
    IFRS17EnhancedCalculator,
    MeasurementModel,
    RAMethod,
    CoverageUnitsMethod
)

# Инициализируем калькулятор
ifrs17_enhanced_calculator = IFRS17EnhancedCalculator()


@main_bp.route('/api/ifrs17/calculate/full', methods=['POST'])
def api_ifrs17_full_calculation():
    """
    API: Полный расчёт по МСФО 17

    POST /api/ifrs17/calculate/full
    {
        "cash_flows": [
            {"period": 1, "premiums": 100000000, "claims": 8000000, ...},
            {"period": 2, ...}
        ],
        "contract_data": {
            "contract_term_years": 10,
            "acquisition_costs": 15000000,
            ...
        },
        "assumptions": {
            "lapse_rate": 0.03,
            "mortality_rate": 0.0015,
            "expense_inflation": 0.05
        },
        "measurement_model": "GMM",  // "GMM", "VFA", "PAA" или auto
        "ra_method": "COC"  // "VAR", "TVAR", "COC", "CTE"
    }
    """
    try:
        data = request.get_json()

        cash_flows = data.get('cash_flows', [])
        contract_data = data.get('contract_data', {})
        assumptions = data.get('assumptions', {
            'lapse_rate': 0.05,
            'mortality_rate': 0.001,
            'expense_inflation': 0.05
        })

        # Определяем модель измерения
        model_str = data.get('measurement_model', 'auto')
        if model_str == 'auto':
            measurement_model = None
        else:
            measurement_model = MeasurementModel[model_str]

        # Определяем метод RA
        ra_method_str = data.get('ra_method', 'COC')
        ra_method = RAMethod[ra_method_str]

        # Выполняем расчёт
        result = ifrs17_enhanced_calculator.calculate_full(
            cash_flows=cash_flows,
            contract_data=contract_data,
            assumptions=assumptions,
            measurement_model=measurement_model,
            ra_method=ra_method
        )

        return jsonify({
            'status': 'success',
            'data': {
                'measurement_model': result.measurement_model.value,
                'group_id': result.group_id,
                'cohort': result.cohort,
                'bel': {
                    'amount': str(result.bel.bel_amount),
                    'premiums': str(result.bel.bel_premiums),
                    'claims': str(result.bel.bel_claims),
                    'expenses': str(result.bel.bel_expenses),
                    'sensitivity': {k: str(v) for k, v in result.bel.sensitivity_analysis.items()},
                    'justification': result.bel.justification
                },
                'ra': {
                    'amount': str(result.ra.ra_amount),
                    'method': result.ra.method.value,
                    'confidence_level': str(result.ra.confidence_level),
                    'components': {
                        'insurance_risk': str(result.ra.ra_insurance_risk),
                        'lapse_risk': str(result.ra.ra_lapse_risk),
                        'expense_risk': str(result.ra.ra_expense_risk),
                        'operational_risk': str(result.ra.ra_operational_risk)
                    },
                    'undiversified': str(result.ra.ra_undiversified),
                    'diversified': str(result.ra.ra_diversified),
                    'diversification_benefit': str(result.ra.diversification_benefit),
                    'justification': result.ra.justification
                },
                'csm': {
                    'opening': str(result.csm.csm_opening),
                    'closing': str(result.csm.csm_closing),
                    'is_onerous': result.csm.is_onerous,
                    'loss_component': str(result.csm.loss_component_closing),
                    'locked_in_rate': str(result.csm.locked_in_rate),
                    'justification': result.csm.justification
                },
                'fcf': str(result.fcf),
                'lrc': str(result.lrc),
                'lic': {
                    'amount': str(result.lic.lic_amount),
                    'reported_claims': str(result.lic.reported_claims),
                    'ibnr': str(result.lic.ibnr),
                    'ibner': str(result.lic.ibner),
                    'ra_lic': str(result.lic.ra_lic)
                },
                'total_insurance_liability': str(result.total_insurance_liability),
                'insurance_finance': {
                    'total': str(result.insurance_finance.ifie_total),
                    'interest_accretion': str(result.insurance_finance.interest_accretion),
                    'effect_rate_changes': str(result.insurance_finance.effect_changes_rates),
                    'pnl_amount': str(result.insurance_finance.pnl_amount),
                    'oci_amount': str(result.insurance_finance.oci_amount)
                },
                'statements': {
                    'financial_position': {k: str(v) for k, v in result.statement_of_financial_position.items()},
                    'profit_loss': {k: str(v) for k, v in result.statement_of_profit_loss.items()},
                    'oci': {k: str(v) for k, v in result.statement_of_oci.items()}
                },
                'formula_display': result.formula_display,
                'justification': result.justification,
                'audit_trail_count': len(result.audit_trail)
            }
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400


@main_bp.route('/api/ifrs17/calculate/bel', methods=['POST'])
def api_ifrs17_bel_calculation():
    """
    API: Расчёт BEL (Best Estimate Liability)

    POST /api/ifrs17/calculate/bel
    {
        "cash_flows": [...],
        "assumptions": {...},
        "discount_approach": "bottom_up"
    }
    """
    try:
        data = request.get_json()

        result = ifrs17_enhanced_calculator.calculate_bel_detailed(
            cash_flows=data.get('cash_flows', []),
            assumptions=data.get('assumptions', {}),
            discount_approach=data.get('discount_approach', 'bottom_up')
        )

        return jsonify({
            'status': 'success',
            'data': {
                'bel_amount': str(result.bel_amount),
                'components': {
                    'premiums': str(result.bel_premiums),
                    'claims': str(result.bel_claims),
                    'expenses': str(result.bel_expenses),
                    'other': str(result.bel_other)
                },
                'pv_breakdown': {
                    'future_premiums': str(result.pv_future_premiums),
                    'future_claims': str(result.pv_future_claims),
                    'future_expenses': str(result.pv_future_expenses),
                    'acquisition_costs': str(result.pv_acquisition_costs)
                },
                'sensitivity_analysis': {k: str(v) for k, v in result.sensitivity_analysis.items()},
                'formula_display': result.formula_display,
                'justification': result.justification,
                'calculation_date': result.calculation_date.isoformat(),
                'reference_paragraphs': result.reference_paragraphs
            }
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400


@main_bp.route('/api/ifrs17/calculate/ra', methods=['POST'])
def api_ifrs17_ra_calculation():
    """
    API: Расчёт Risk Adjustment

    POST /api/ifrs17/calculate/ra
    {
        "cash_flows": [100000, 90000, 85000, ...],
        "method": "COC",  // "VAR", "TVAR", "COC", "CTE"
        "confidence_level": 0.95,
        "capital_requirement": 50000000,
        "risk_parameters": {
            "insurance_risk_loading": 0.05,
            "lapse_risk_loading": 0.02,
            ...
        }
    }
    """
    try:
        data = request.get_json()

        cash_flows = [Decimal(str(cf)) for cf in data.get('cash_flows', [])]
        method = RAMethod[data.get('method', 'COC')]
        confidence_level = Decimal(str(data.get('confidence_level', 0.95)))
        capital_requirement = Decimal(str(data.get('capital_requirement', 0))) if data.get('capital_requirement') else None
        risk_parameters = data.get('risk_parameters')

        result = ifrs17_enhanced_calculator.calculate_ra_detailed(
            cash_flows=cash_flows,
            method=method,
            confidence_level=confidence_level,
            capital_requirement=capital_requirement,
            risk_parameters=risk_parameters
        )

        return jsonify({
            'status': 'success',
            'data': {
                'ra_amount': str(result.ra_amount),
                'method': result.method.value,
                'confidence_level': str(result.confidence_level),
                'components': {
                    'insurance_risk': str(result.ra_insurance_risk),
                    'lapse_risk': str(result.ra_lapse_risk),
                    'expense_risk': str(result.ra_expense_risk),
                    'operational_risk': str(result.ra_operational_risk)
                },
                'undiversified': str(result.ra_undiversified),
                'diversified': str(result.ra_diversified),
                'diversification_benefit': str(result.diversification_benefit),
                'percentiles': {k: str(v) for k, v in result.percentiles.items()},
                'confidence_interval': [str(result.confidence_interval[0]), str(result.confidence_interval[1])],
                'formula_display': result.formula_display,
                'justification': result.justification,
                'reference_paragraphs': result.reference_paragraphs
            }
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400


@main_bp.route('/api/ifrs17/calculate/csm', methods=['POST'])
def api_ifrs17_csm_calculation():
    """
    API: Расчёт CSM (Contractual Service Margin)

    POST /api/ifrs17/calculate/csm
    {
        "type": "initial",  // "initial", "rollforward_gmm", "rollforward_vfa"
        "premiums": 100000000,
        "acquisition_costs": 15000000,
        "bel": 75000000,
        "ra": 5000000,
        // Для rollforward:
        "opening_csm": 10000000,
        "locked_in_rate": 0.035,
        ...
    }
    """
    try:
        data = request.get_json()
        calc_type = data.get('type', 'initial')

        if calc_type == 'initial':
            result = ifrs17_enhanced_calculator.calculate_csm_initial(
                premiums=Decimal(str(data.get('premiums', 0))),
                acquisition_costs=Decimal(str(data.get('acquisition_costs', 0))),
                bel=Decimal(str(data.get('bel', 0))),
                ra=Decimal(str(data.get('ra', 0)))
            )

            return jsonify({
                'status': 'success',
                'data': {
                    'type': 'initial',
                    'csm_closing': str(result.csm_closing),
                    'is_onerous': result.is_onerous,
                    'loss_component': str(result.loss_component_closing),
                    'locked_in_rate': str(result.locked_in_rate),
                    'formula_display': result.formula_display,
                    'justification': result.justification,
                    'reference_paragraphs': result.reference_paragraphs
                }
            })

        elif calc_type == 'rollforward_gmm':
            result = ifrs17_enhanced_calculator.calculate_csm_rollforward_gmm(
                opening_csm=Decimal(str(data.get('opening_csm', 0))),
                opening_loss_component=Decimal(str(data.get('opening_loss_component', 0))),
                locked_in_rate=Decimal(str(data.get('locked_in_rate', 0.035))),
                new_contracts_csm=Decimal(str(data.get('new_contracts_csm', 0))),
                changes_future_service=Decimal(str(data.get('changes_future_service', 0))),
                experience_adjustment_csm=Decimal(str(data.get('experience_adjustment_csm', 0))),
                coverage_units_current=Decimal(str(data.get('coverage_units_current', 1))),
                coverage_units_remaining=Decimal(str(data.get('coverage_units_remaining', 10))),
                currency_effect=Decimal(str(data.get('currency_effect', 0)))
            )

            return jsonify({
                'status': 'success',
                'data': {
                    'type': 'rollforward_gmm',
                    'csm_opening': str(result.csm_opening),
                    'csm_closing': str(result.csm_closing),
                    'csm_interest_accretion': str(result.csm_interest_accretion),
                    'csm_changes_future_service': str(result.csm_changes_future_service),
                    'csm_release': str(result.csm_release),
                    'is_onerous': result.is_onerous,
                    'loss_component_closing': str(result.loss_component_closing),
                    'formula_display': result.formula_display,
                    'justification': result.justification
                }
            })

        elif calc_type == 'rollforward_vfa':
            result = ifrs17_enhanced_calculator.calculate_csm_rollforward_vfa(
                opening_csm=Decimal(str(data.get('opening_csm', 0))),
                change_fv_underlying=Decimal(str(data.get('change_fv_underlying', 0))),
                entity_share=Decimal(str(data.get('entity_share', 0.9))),
                changes_fcf_non_variable=Decimal(str(data.get('changes_fcf_non_variable', 0))),
                coverage_units_current=Decimal(str(data.get('coverage_units_current', 1))),
                coverage_units_remaining=Decimal(str(data.get('coverage_units_remaining', 10)))
            )

            return jsonify({
                'status': 'success',
                'data': {
                    'type': 'rollforward_vfa',
                    'csm_opening': str(result.csm_opening),
                    'csm_closing': str(result.csm_closing),
                    'csm_variable_fee_change': str(result.csm_variable_fee_change),
                    'csm_release': str(result.csm_release),
                    'is_onerous': result.is_onerous,
                    'loss_component_closing': str(result.loss_component_closing),
                    'formula_display': result.formula_display,
                    'justification': result.justification
                }
            })

        else:
            return jsonify({'status': 'error', 'message': f'Unknown calculation type: {calc_type}'}), 400

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400


@main_bp.route('/api/ifrs17/calculate/paa', methods=['POST'])
def api_ifrs17_paa_calculation():
    """
    API: Расчёт по PAA (Premium Allocation Approach)

    POST /api/ifrs17/calculate/paa
    {
        "premiums": 10000000,
        "acquisition_costs": 1500000,
        "expense_acquisition": true,
        "coverage_period_months": 12,
        "time_elapsed_months": 6,
        "claims_incurred": 3000000,
        "ra_lic": 500000
    }
    """
    try:
        data = request.get_json()

        result = ifrs17_enhanced_calculator.calculate_paa(
            premiums=Decimal(str(data.get('premiums', 0))),
            acquisition_costs=Decimal(str(data.get('acquisition_costs', 0))),
            expense_acquisition=data.get('expense_acquisition', False),
            coverage_period_months=int(data.get('coverage_period_months', 12)),
            time_elapsed_months=int(data.get('time_elapsed_months', 0)),
            claims_incurred=Decimal(str(data.get('claims_incurred', 0))),
            ra_lic=Decimal(str(data.get('ra_lic', 0)))
        )

        return jsonify({
            'status': 'success',
            'data': {
                'measurement_model': result['measurement_model'].value,
                'lrc': str(result['lrc']),
                'lic': str(result['lic']),
                'total_liability': str(result['total_liability']),
                'unearned_premium': str(result['unearned_premium']),
                'earned_premium': str(result['earned_premium']),
                'dac': str(result['dac']),
                'dac_remaining': str(result['dac_remaining']),
                'ac_expensed': str(result['ac_expensed']),
                'formula_display': result['formula_display'],
                'reference_paragraphs': result['reference_paragraphs']
            }
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400


@main_bp.route('/api/ifrs17/eligibility/paa', methods=['POST'])
def api_ifrs17_paa_eligibility():
    """
    API: Проверка eligibility для PAA

    POST /api/ifrs17/eligibility/paa
    {
        "coverage_period_months": 12,
        "has_significant_variability": false,
        "cf_variability": 0.1,
        "has_embedded_options": false
    }
    """
    try:
        data = request.get_json()

        eligible, justification = ifrs17_enhanced_calculator.check_paa_eligibility(data)

        return jsonify({
            'status': 'success',
            'data': {
                'eligible': eligible,
                'justification': justification
            }
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400


@main_bp.route('/api/ifrs17/eligibility/vfa', methods=['POST'])
def api_ifrs17_vfa_eligibility():
    """
    API: Проверка eligibility для VFA

    POST /api/ifrs17/eligibility/vfa
    {
        "has_explicit_share": true,
        "correlation_underlying": 0.85,
        "variable_fee_portion": 0.6
    }
    """
    try:
        data = request.get_json()

        eligible, justification = ifrs17_enhanced_calculator.check_vfa_eligibility(data)

        return jsonify({
            'status': 'success',
            'data': {
                'eligible': eligible,
                'justification': justification
            }
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400


@main_bp.route('/api/ifrs17/yield-curve', methods=['GET'])
def api_ifrs17_yield_curve():
    """
    API: Получить кривую доходности для МСФО 17

    GET /api/ifrs17/yield-curve?max_term=30&approach=bottom_up
    """
    try:
        max_term = int(request.args.get('max_term', 30))
        approach = request.args.get('approach', 'bottom_up')

        discount_factors = ifrs17_enhanced_calculator.yield_curve.get_discount_factors(max_term, approach)
        forward_rates = ifrs17_enhanced_calculator.yield_curve.get_forward_rates(max_term)

        spot_rates = {}
        for term in range(1, max_term + 1):
            rate, _ = ifrs17_enhanced_calculator.yield_curve.get_discount_rate(term, approach)
            spot_rates[term] = str(rate)

        return jsonify({
            'status': 'success',
            'data': {
                'approach': approach,
                'reference_date': ifrs17_enhanced_calculator.yield_curve.reference_date.isoformat(),
                'spot_rates': spot_rates,
                'discount_factors': {k: str(v) for k, v in discount_factors.items()},
                'forward_rates': {k: str(v) for k, v in forward_rates.items()}
            }
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400


@main_bp.route('/api/ifrs17/audit-log', methods=['GET'])
def api_ifrs17_audit_log():
    """
    API: Получить аудиторский след расчётов МСФО 17

    GET /api/ifrs17/audit-log?limit=100
    """
    try:
        limit = int(request.args.get('limit', 100))
        audit_log = ifrs17_enhanced_calculator.get_audit_log()[-limit:]

        return jsonify({
            'status': 'success',
            'data': {
                'entries': audit_log,
                'total_count': len(ifrs17_enhanced_calculator.audit_log),
                'returned_count': len(audit_log)
            }
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400


# =============================================================================
# API ГЕНЕРАТОРА РЕГУЛЯТОРНЫХ ОТЧЁТОВ
# =============================================================================

from app.services.report_generator import report_generator_service, ReportFormat
from flask import send_file
import io

# Временное хранилище сгенерированных отчётов
_generated_reports = {}


@main_bp.route('/api/reports/generate', methods=['POST'])
def api_generate_report():
    """
    API: Генерация регуляторного отчёта

    POST /api/reports/generate
    {
        "report_code": "1-SK",      // Код формы
        "period": "2026-01",        // Период (YYYY-MM, YYYY-QN, YYYY)
        "format": "xlsx"            // Формат: xlsx, pdf, json
    }

    Returns:
        {
            "status": "success",
            "data": {
                "report_id": "uuid",
                "filename": "1-SK_2026-01.xlsx",
                "download_url": "/api/reports/download/uuid"
            }
        }
    """
    try:
        data = request.get_json()

        report_code = data.get('report_code')
        period = data.get('period')
        format_str = data.get('format', 'xlsx')

        if not report_code:
            return jsonify({'status': 'error', 'message': 'report_code is required'}), 400
        if not period:
            return jsonify({'status': 'error', 'message': 'period is required'}), 400

        # Parse format
        format_map = {
            'xlsx': ReportFormat.EXCEL,
            'excel': ReportFormat.EXCEL,
            'pdf': ReportFormat.PDF,
            'json': ReportFormat.JSON
        }
        report_format = format_map.get(format_str.lower(), ReportFormat.EXCEL)

        # Generate report
        report = report_generator_service.generate_report(
            report_code=report_code,
            period=period,
            format=report_format
        )

        # Store report for download
        import uuid
        report_id = str(uuid.uuid4())
        _generated_reports[report_id] = {
            'content': report.content,
            'filename': report.filename,
            'format': report.format,
            'metadata': {
                'report_code': report.metadata.report_code,
                'report_name': report.metadata.report_name,
                'regulation': report.metadata.regulation,
                'period': report.metadata.period,
                'company_name': report.metadata.company_name,
                'generated_at': report.metadata.generated_at.isoformat()
            }
        }

        return jsonify({
            'status': 'success',
            'data': {
                'report_id': report_id,
                'filename': report.filename,
                'download_url': f'/api/reports/download/{report_id}',
                'metadata': _generated_reports[report_id]['metadata']
            }
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400


@main_bp.route('/api/reports/download/<report_id>')
def api_download_report(report_id):
    """
    API: Скачивание сгенерированного отчёта

    GET /api/reports/download/{report_id}

    Returns: Binary file (Excel/PDF/JSON)
    """
    try:
        if report_id not in _generated_reports:
            return jsonify({'status': 'error', 'message': 'Report not found'}), 404

        report_data = _generated_reports[report_id]

        # Determine MIME type
        mime_types = {
            ReportFormat.EXCEL: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            ReportFormat.PDF: 'application/pdf',
            ReportFormat.JSON: 'application/json'
        }
        mime_type = mime_types.get(report_data['format'], 'application/octet-stream')

        # Create buffer and send
        buffer = io.BytesIO(report_data['content'])
        buffer.seek(0)

        return send_file(
            buffer,
            as_attachment=True,
            download_name=report_data['filename'],
            mimetype=mime_type
        )

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400


@main_bp.route('/api/reports/list')
def api_list_reports():
    """
    API: Список доступных форм отчётности

    GET /api/reports/list

    Returns:
        {
            "status": "success",
            "data": {
                "forms": [
                    {"code": "1-SK", "name": "...", "regulation": "..."},
                    ...
                ]
            }
        }
    """
    forms = [
        # Постановление №85 - Статистическая отчётность
        {'code': '1-SK', 'name': 'Отчёт о страховой деятельности', 'name_kz': 'Сақтандыру қызметі туралы есеп',
         'regulation': '85', 'frequency': 'monthly', 'category': 'Статистика'},
        {'code': '2-SK', 'name': 'Отчёт о страховых премиях и выплатах', 'name_kz': 'Сақтандыру сыйлықақылары мен төлемдері туралы есеп',
         'regulation': '85', 'frequency': 'monthly', 'category': 'Статистика'},
        {'code': '3-SK', 'name': 'Отчёт о структуре активов', 'name_kz': 'Активтер құрылымы туралы есеп',
         'regulation': '85', 'frequency': 'quarterly', 'category': 'Статистика'},
        {'code': '4-SK', 'name': 'Отчёт о перестраховочных операциях', 'name_kz': 'Қайта сақтандыру операциялары туралы есеп',
         'regulation': '85', 'frequency': 'quarterly', 'category': 'Статистика'},
        {'code': '5-SK', 'name': 'Годовой бухгалтерский баланс', 'name_kz': 'Жылдық бухгалтерлік баланс',
         'regulation': '85', 'frequency': 'annual', 'category': 'Бухгалтерия'},

        # Постановление №86 - Платёжеспособность
        {'code': 'P86-1', 'name': 'Расчёт маржи платёжеспособности', 'name_kz': 'Төлем қабілеттілігі маржасын есептеу',
         'regulation': '86', 'frequency': 'quarterly', 'category': 'Платёжеспособность'},
        {'code': 'P86-2', 'name': 'Расчёт минимального гарантийного фонда', 'name_kz': 'Ең төменгі кепілдік қорын есептеу',
         'regulation': '86', 'frequency': 'quarterly', 'category': 'Платёжеспособность'},
        {'code': 'P86-3', 'name': 'Расчёт нормативов достаточности капитала', 'name_kz': 'Капитал жеткіліктілігі нормативтерін есептеу',
         'regulation': '86', 'frequency': 'quarterly', 'category': 'Капитал'},

        # Постановление №304 - Резервы
        {'code': 'R304-1', 'name': 'Расчёт резерва незаработанной премии (РНПП)', 'name_kz': 'Жұмыс істемеген сыйлықақы резервін есептеу',
         'regulation': '304', 'frequency': 'monthly', 'category': 'Резервы'},
        {'code': 'R304-2', 'name': 'Расчёт резерва заявленных убытков (РЗУ)', 'name_kz': 'Мәлімделген шығындар резервін есептеу',
         'regulation': '304', 'frequency': 'monthly', 'category': 'Резервы'},
        {'code': 'R304-3', 'name': 'Расчёт РПНУ/IBNR методом Chain-Ladder', 'name_kz': 'IBNR тізбекті баспалдақ әдісімен есептеу',
         'regulation': '304', 'frequency': 'quarterly', 'category': 'Резервы'},
        {'code': 'R304-4', 'name': 'Расчёт стабилизационного резерва', 'name_kz': 'Тұрақтандыру резервін есептеу',
         'regulation': '304', 'frequency': 'annual', 'category': 'Резервы'}
    ]

    return jsonify({
        'status': 'success',
        'data': {
            'forms': forms,
            'regulations': [
                {'code': '85', 'name': 'Постановление АРРФР №85', 'description': 'О формах статистической отчётности'},
                {'code': '86', 'name': 'Постановление АРРФР №86', 'description': 'О расчёте маржи платёжеспособности'},
                {'code': '304', 'name': 'Постановление АРРФР №304', 'description': 'О формировании страховых резервов'}
            ]
        }
    })


@main_bp.route('/api/reports/submit-arrfr', methods=['POST'])
def api_submit_to_arrfr():
    """
    API: Отправка отчёта в АРРФР (имитация)

    POST /api/reports/submit-arrfr
    {
        "report_id": "uuid"
    }

    Returns:
        {
            "status": "success",
            "data": {
                "submission_id": "ARRFR-2026-001234",
                "submitted_at": "2026-01-21T14:30:00",
                "status": "pending",
                "message": "Отчёт успешно отправлен в АРРФР"
            }
        }
    """
    try:
        data = request.get_json()
        report_id = data.get('report_id')

        if not report_id or report_id not in _generated_reports:
            return jsonify({'status': 'error', 'message': 'Report not found'}), 404

        # Simulated submission
        import uuid
        from datetime import datetime

        submission_id = f"ARRFR-{datetime.now().year}-{str(uuid.uuid4())[:8].upper()}"

        return jsonify({
            'status': 'success',
            'data': {
                'submission_id': submission_id,
                'submitted_at': datetime.now().isoformat(),
                'status': 'pending',
                'message': 'Отчёт успешно отправлен в АРРФР. Ожидайте подтверждения.',
                'estimated_processing_time': '1-3 рабочих дня',
                'report_metadata': _generated_reports[report_id]['metadata']
            }
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400


# =============================================================================
# CRM & DASHBOARD API ENDPOINTS
# =============================================================================

@main_bp.route('/api/dashboard/metrics', methods=['GET'])
def api_dashboard_metrics():
    """
    API: Get dashboard metrics for Chart.js visualization

    GET /api/dashboard/metrics

    Returns:
        Real-time metrics for 8 dashboard charts
    """
    try:
        from datetime import datetime, timedelta
        from decimal import Decimal
        import random

        # Получаем реальные данные из unified_calculation_service
        calc_result = unified_calculation_service.calculate_everything()

        current_date = datetime.now()
        months = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек']

        # Извлекаем реальные значения из расчетов (объект UnifiedCalculationResult)
        real_solvency = float(calc_result.solvency.ratio) * 100  # Конвертируем в проценты
        real_ecl = float(calc_result.ecl.ecl_amount)
        real_bel = float(calc_result.ifrs17.bel)
        real_csm = float(calc_result.ifrs17.csm)
        real_ra = float(calc_result.ifrs17.ra)

        # 1. Solvency Ratio trend (12 months) - используем реальное значение как конечную точку
        solvency_ratios = []
        base_solvency = real_solvency - 15  # Начальная точка на 15% ниже текущей
        for i in range(12):
            progress = (real_solvency - base_solvency) * (i / 11)
            fluctuation = random.uniform(-2, 2)
            solvency_ratios.append(round(base_solvency + progress + fluctuation, 1))
        solvency_ratios[-1] = real_solvency  # Гарантируем точное последнее значение

        solvency_data = {
            'labels': months,
            'solvencyRatio': solvency_ratios,
            'minRequirement': [100] * 12,
            'targetLevel': [120] * 12
        }

        # 2. Portfolio composition by currency - используем реальный BEL
        total_portfolio = real_bel
        portfolio_data = {
            'labels': ['KZT', 'USD', 'EUR', 'RUB'],
            'values': [
                int(total_portfolio * 0.76),  # 76% KZT
                int(total_portfolio * 0.14),  # 14% USD
                int(total_portfolio * 0.06),  # 6% EUR
                int(total_portfolio * 0.04)   # 4% RUB
            ]
        }

        # 3. ECL by Stage - используем реальный ECL
        ecl_stage1 = real_ecl * 0.50  # 50% Stage 1
        ecl_stage2 = real_ecl * 0.35  # 35% Stage 2
        ecl_stage3 = real_ecl * 0.15  # 15% Stage 3
        ecl_data = {
            'labels': ['Q1 2025', 'Q2 2025', 'Q3 2025', 'Q4 2025', 'Q1 2026 (П)'],
            'stage1': [int(ecl_stage1*0.85), int(ecl_stage1*0.90), int(ecl_stage1*0.95), int(ecl_stage1*0.98), int(ecl_stage1)],
            'stage2': [int(ecl_stage2*0.82), int(ecl_stage2*0.88), int(ecl_stage2*0.93), int(ecl_stage2*0.97), int(ecl_stage2)],
            'stage3': [int(ecl_stage3*0.80), int(ecl_stage3*0.85), int(ecl_stage3*0.92), int(ecl_stage3*0.96), int(ecl_stage3)]
        }

        # 4. CSM Waterfall - используем реальный CSM
        csm_opening = real_csm * 0.92
        csm_new = real_csm * 0.18
        csm_changes = -real_csm * 0.03
        csm_experience = real_csm * 0.025
        csm_amort = -real_csm * 0.13
        csm_data = {
            'labels': ['Нач. баланс', 'Новые договоры', 'Ожид. изменения', 'Опыт. корректировки', 'Амортизация', 'Кон. баланс'],
            'values': [int(csm_opening), int(csm_new), int(csm_changes), int(csm_experience), int(csm_amort), int(real_csm)],
            'colors': ['#1e3a5f', '#06d6a0', '#ef476f', '#06d6a0', '#ef476f', '#1e3a5f']
        }

        # 5. Premiums vs Claims
        premiums = []
        claims = []
        base_premium = 125000000
        base_claim = 78000000
        for i in range(12):
            premium_growth = random.uniform(0.98, 1.05)
            claim_growth = random.uniform(0.97, 1.06)
            premiums.append(int(base_premium * premium_growth))
            claims.append(int(base_claim * claim_growth))
            base_premium *= 1.02
            base_claim *= 1.015

        premiums_vs_claims_data = {
            'labels': months,
            'premiums': premiums,
            'claims': claims
        }

        # 6. Products mix
        products_data = {
            'labels': ['Жизнь', 'Не-жизнь', 'Здоровье', 'Аннуитеты'],
            'values': [420000000, 285000000, 95000000, 50000000]
        }

        # 7. Gauge metrics
        gauge_data = {
            'solvency_ratio': solvency_ratios[-1],
            'loss_ratio': round((claims[-1] / premiums[-1]) * 100, 1)
        }

        # 8. Risk matrix
        risk_matrix_data = {
            'labels': ['Market Risk', 'Credit Risk', 'Operational Risk', 'Underwriting Risk', 'Liquidity Risk', 'Concentration Risk'],
            'current': [65, 45, 55, 70, 35, 60],
            'target': [50, 40, 45, 60, 30, 50]
        }

        return jsonify({
            'status': 'success',
            'data': {
                'solvency_ratio': solvency_data,
                'portfolio_composition': portfolio_data,
                'ecl_by_stage': ecl_data,
                'csm_waterfall': csm_data,
                'premiums_vs_claims': premiums_vs_claims_data,
                'products_mix': products_data,
                'gauge_metrics': gauge_data,
                'risk_matrix': risk_matrix_data,
                'timestamp': datetime.now().isoformat()
            }
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@main_bp.route('/api/customers', methods=['GET'])
def api_get_customers():
    """
    API: Get all customers with pagination and filtering

    GET /api/customers?page=1&limit=50&segment=VIP&search=

    Returns:
        List of customers with metadata
    """
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 50))
        segment = request.args.get('segment', '')
        search = request.args.get('search', '')

        # Mock data (in production, query from database)
        customers = [
            {
                'id': 'cust_001',
                'full_name': 'Алиева Айгерим Сериковна',
                'iin': '850215300123',
                'email': 'aigerim.alieva@example.kz',
                'phone': '+7 (701) 234-56-78',
                'segment': 'VIP',
                'risk_rating': 'LOW',
                'customer_lifetime_value': 2500000,
                'total_policies': 3,
                'total_claims': 1,
                'last_interaction': '2026-01-20',
                'is_active': True
            },
            {
                'id': 'cust_002',
                'full_name': 'Нурымбетов Ерлан Маратович',
                'iin': '920512400234',
                'email': 'erlan.nurymbetov@example.kz',
                'phone': '+7 (702) 345-67-89',
                'segment': 'STANDARD',
                'risk_rating': 'MEDIUM',
                'customer_lifetime_value': 950000,
                'total_policies': 2,
                'total_claims': 0,
                'last_interaction': '2026-01-18',
                'is_active': True
            }
        ]

        # Apply filters
        if segment:
            customers = [c for c in customers if c['segment'] == segment]

        if search:
            customers = [c for c in customers if
                        search.lower() in c['full_name'].lower() or
                        search in c['iin'] or
                        search in c.get('email', '')]

        # Calculate pagination
        total = len(customers)
        start = (page - 1) * limit
        end = start + limit
        paginated_customers = customers[start:end]

        return jsonify({
            'status': 'success',
            'data': {
                'customers': paginated_customers,
                'pagination': {
                    'total': total,
                    'page': page,
                    'limit': limit,
                    'pages': (total + limit - 1) // limit
                }
            }
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@main_bp.route('/api/agents', methods=['GET'])
def api_get_agents():
    """
    API: Get all agents with KPI metrics

    GET /api/agents?page=1&limit=50&status=ACTIVE

    Returns:
        List of agents with performance metrics
    """
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 50))
        status = request.args.get('status', 'ACTIVE')

        # Mock agent data
        agents = [
            {
                'id': 'agent_001',
                'agent_code': 'AG-001',
                'full_name': 'Досов Самат Ерланович',
                'email': 'samat.dosov@insureagent.kz',
                'phone': '+7 (701) 111-22-33',
                'type': 'INDIVIDUAL',
                'status': 'ACTIVE',
                'region': 'Алматы',
                'performance': {
                    'total_policies_sold': 45,
                    'total_premium_volume': 42500000,
                    'total_commission_earned': 2125000,
                    'conversion_rate': 68.5,
                    'retention_rate': 92.0,
                    'customer_satisfaction_score': 9.2
                },
                'kpi_score': 87.3,
                'last_sale_date': '2026-01-19'
            },
            {
                'id': 'agent_002',
                'agent_code': 'AG-002',
                'full_name': 'Касымова Алия Бекетовна',
                'email': 'aliya.kasymova@insureagent.kz',
                'phone': '+7 (702) 222-33-44',
                'type': 'BROKER',
                'status': 'ACTIVE',
                'region': 'Астана',
                'performance': {
                    'total_policies_sold': 62,
                    'total_premium_volume': 58300000,
                    'total_commission_earned': 2915000,
                    'conversion_rate': 72.1,
                    'retention_rate': 89.5,
                    'customer_satisfaction_score': 9.5
                },
                'kpi_score': 91.2,
                'last_sale_date': '2026-01-21'
            }
        ]

        # Apply filters
        if status:
            agents = [a for a in agents if a['status'] == status]

        # Calculate pagination
        total = len(agents)
        start = (page - 1) * limit
        end = start + limit
        paginated_agents = agents[start:end]

        return jsonify({
            'status': 'success',
            'data': {
                'agents': paginated_agents,
                'pagination': {
                    'total': total,
                    'page': page,
                    'limit': limit,
                    'pages': (total + limit - 1) // limit
                },
                'summary': {
                    'total_agents': total,
                    'active_agents': len([a for a in agents if a['status'] == 'ACTIVE']),
                    'avg_kpi_score': round(sum(a['kpi_score'] for a in agents) / len(agents), 1) if agents else 0
                }
            }
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# =============================================================================
# API: ИНТЕГРАЦИИ С УЧЕТНЫМИ СИСТЕМАМИ КАЗАХСТАНА
# =============================================================================

@main_bp.route('/api/sync/<system_id>', methods=['POST'])
def api_sync_system(system_id):
    """
    API: Синхронизация с внешней учетной системой

    POST /api/sync/1c - 1С:Бухгалтерия
    POST /api/sync/esbd - Единая страховая база данных
    POST /api/sync/nbk - Национальный Банк Казахстана
    POST /api/sync/arfr - АРФР Портал
    POST /api/sync/kcmr - Казахстанский центр межбанковских расчетов
    POST /api/sync/egov - Электронное правительство
    """
    import random
    from datetime import timedelta

    systems_config = {
        '1c': {
            'name': '1С:Бухгалтерия',
            'data_types': [
                {'name': 'Журнал проводок', 'count': 5420},
                {'name': 'Оборотная ведомость', 'count': 248},
                {'name': 'Баланс', 'count': 1}
            ],
            'description': 'Финансовые данные из 1С:Бухгалтерия 8.3'
        },
        'esbd': {
            'name': 'ЕСБД',
            'data_types': [
                {'name': 'Полисы ОСАГО', 'count': 4250},
                {'name': 'Полисы КАСКО', 'count': 1850},
                {'name': 'Страховые случаи', 'count': 892}
            ],
            'description': 'Единая страховая база данных Казахстана'
        },
        'nbk': {
            'name': 'НБК API',
            'data_types': [
                {'name': 'Курсы валют USD/KZT', 'count': 365},
                {'name': 'Базовая ставка', 'count': 12},
                {'name': 'Инфляция', 'count': 12}
            ],
            'description': 'Национальный Банк Казахстана - официальные курсы и ставки'
        },
        'arfr': {
            'name': 'АРФР Портал',
            'data_types': [
                {'name': 'Форма №85 (Активы)', 'count': 12},
                {'name': 'Форма №86 (Платежеспособность)', 'count': 12},
                {'name': 'Форма №304 (Резервы)', 'count': 12}
            ],
            'description': 'Агентство РК по регулированию и развитию финансового рынка'
        },
        'kcmr': {
            'name': 'КЦМР',
            'data_types': [
                {'name': 'Гос. облигации', 'count': 450},
                {'name': 'Корп. облигации', 'count': 890},
                {'name': 'Акции KASE', 'count': 125}
            ],
            'description': 'Казахстанский центр межбанковских расчетов - котировки ЦБ'
        },
        'egov': {
            'name': 'eGov / ЦОН',
            'data_types': [
                {'name': 'Верификация ИИН', 'count': 12500},
                {'name': 'Адресные данные', 'count': 12500},
                {'name': 'Контактные данные', 'count': 8900}
            ],
            'description': 'Электронное правительство - данные клиентов'
        }
    }

    if system_id not in systems_config:
        return jsonify({
            'status': 'error',
            'message': f'Неизвестная система: {system_id}'
        }), 400

    system = systems_config[system_id]
    sync_results = []
    total_records = 0

    for data_type in system['data_types']:
        actual_count = data_type['count'] + random.randint(-50, 100)
        actual_count = max(1, actual_count)
        total_records += actual_count
        sync_results.append({
            'data_type': data_type['name'],
            'records_synced': actual_count,
            'status': 'success'
        })

    return jsonify({
        'status': 'success',
        'system': {
            'id': system_id,
            'name': system['name'],
            'description': system['description']
        },
        'sync_results': sync_results,
        'total_records': total_records,
        'sync_timestamp': datetime.now().isoformat(),
        'next_sync_scheduled': (datetime.now() + timedelta(hours=1)).isoformat()
    })


@main_bp.route('/api/integrations/status', methods=['GET'])
def api_integrations_status():
    """
    API: Получить статус всех интеграций с внешними системами
    """
    from datetime import timedelta

    integrations = [
        {
            'id': '1c',
            'name': '1С:Бухгалтерия',
            'status': 'connected',
            'last_sync': (datetime.now() - timedelta(minutes=15)).isoformat(),
            'records_count': 15420,
            'health': 'healthy'
        },
        {
            'id': 'esbd',
            'name': 'ЕСБД',
            'status': 'connected',
            'last_sync': (datetime.now() - timedelta(minutes=30)).isoformat(),
            'records_count': 8750,
            'health': 'healthy'
        },
        {
            'id': 'nbk',
            'name': 'НБК API',
            'status': 'connected',
            'last_sync': (datetime.now() - timedelta(hours=1)).isoformat(),
            'records_count': 389,
            'health': 'healthy'
        },
        {
            'id': 'arfr',
            'name': 'АРФР Портал',
            'status': 'connected',
            'last_sync': (datetime.now() - timedelta(hours=2)).isoformat(),
            'records_count': 48,
            'health': 'healthy'
        },
        {
            'id': 'kcmr',
            'name': 'КЦМР',
            'status': 'connected',
            'last_sync': (datetime.now() - timedelta(minutes=45)).isoformat(),
            'records_count': 1465,
            'health': 'healthy'
        },
        {
            'id': 'egov',
            'name': 'eGov / ЦОН',
            'status': 'connected',
            'last_sync': (datetime.now() - timedelta(hours=4)).isoformat(),
            'records_count': 33900,
            'health': 'healthy'
        }
    ]

    return jsonify({
        'status': 'success',
        'integrations': integrations,
        'total_systems': len(integrations),
        'connected_systems': len([i for i in integrations if i['status'] == 'connected']),
        'timestamp': datetime.now().isoformat()
    })


# =============================================================================
# API: ОБЕЗЛИЧЕННЫЕ ДАННЫЕ ДЛЯ РЕГУЛЯТОРОВ
# =============================================================================

@main_bp.route('/api/regulatory/anonymized-data', methods=['GET'])
def api_regulatory_anonymized_data():
    """
    API: Получить обезличенные данные для регуляторной отчетности

    Параметры:
    - regulator: arfr, fgsv, nbk (обязательный)
    - report_type: тип отчета (опционально)
    - period: период отчетности YYYY-MM (опционально)

    Все персональные данные обезличены согласно Закону РК "О персональных данных"
    """
    from app.services.data_anonymization import get_anonymizer, anonymize_for_regulator

    regulator = request.args.get('regulator', 'arfr')
    report_type = request.args.get('report_type', 'general')
    period = request.args.get('period', datetime.now().strftime('%Y-%m'))

    anonymizer = get_anonymizer()

    # Демо-данные клиентов (обычно из БД)
    raw_customers = [
        {
            'id': 1,
            'iin': '850415350789',
            'full_name': 'Иванов Иван Иванович',
            'phone': '+77071234567',
            'email': 'ivanov@mail.kz',
            'date_of_birth': '1985-04-15',
            'gender': 'M',
            'region': 'Алматы',
            'segment': 'VIP',
            'risk_rating': 'LOW',
            'total_policies': 3,
            'total_claims': 1,
            'total_premium_paid': 2500000,
            'customer_lifetime_value': 5800000,
            'created_at': '2020-03-15',
            'last_interaction': '2025-01-10'
        },
        {
            'id': 2,
            'iin': '920722450123',
            'full_name': 'Петрова Анна Сергеевна',
            'phone': '+77019876543',
            'email': 'petrova@gmail.com',
            'date_of_birth': '1992-07-22',
            'gender': 'F',
            'region': 'Астана',
            'segment': 'STANDARD',
            'risk_rating': 'MEDIUM',
            'total_policies': 2,
            'total_claims': 0,
            'total_premium_paid': 850000,
            'customer_lifetime_value': 1200000,
            'created_at': '2022-08-20',
            'last_interaction': '2025-01-15'
        }
    ]

    # Обезличиваем данные
    anonymized_customers = [
        anonymizer.anonymize_customer(c, level='full')
        for c in raw_customers
    ]

    # Агрегированная статистика (без персональных данных)
    aggregates = {
        'total_customers': 12450,
        'total_policies': 28750,
        'total_claims': 3420,
        'total_premium': 850000000,
        'total_claims_paid': 312000000,
        'loss_ratio': 36.7,
        'by_segment': {
            'VIP': {'count': 1245, 'premium_share': 0.35},
            'STANDARD': {'count': 9876, 'premium_share': 0.55},
            'RISK': {'count': 1329, 'premium_share': 0.10}
        },
        'by_region': {
            'Алматы': {'count': 4500, 'share': 0.36},
            'Астана': {'count': 3200, 'share': 0.26},
            'Другие': {'count': 4750, 'share': 0.38}
        },
        'by_age_group': {
            '18-24': 0.08,
            '25-34': 0.25,
            '35-44': 0.30,
            '45-54': 0.22,
            '55-64': 0.10,
            '65+': 0.05
        }
    }

    return jsonify({
        'status': 'success',
        'regulator': regulator,
        'report_type': report_type,
        'period': period,
        'data_anonymization': {
            'method': 'full_anonymization',
            'compliance': 'Law on Personal Data Protection of RK',
            'fields_removed': ['iin', 'full_name', 'phone', 'email', 'address'],
            'fields_hashed': ['iin_hash'],
            'fields_grouped': ['age_group', 'registration_year']
        },
        'customers_sample': anonymized_customers,  # Обезличенные данные
        'aggregates': aggregates,  # Агрегированная статистика
        'generated_at': datetime.now().isoformat(),
        'note': 'Персональные данные обезличены. Для сверки используйте iin_hash.'
    })


@main_bp.route('/api/regulatory/data-protection-info', methods=['GET'])
def api_data_protection_info():
    """
    API: Информация о защите персональных данных
    """
    return jsonify({
        'status': 'success',
        'data_protection': {
            'compliance': [
                'Закон РК "О персональных данных и их защите"',
                'GDPR (где применимо)',
                'Требования АРФР по информационной безопасности'
            ],
            'anonymization_methods': {
                'full': 'Полное обезличивание - удаление всех персональных данных',
                'partial': 'Частичное маскирование - для внутренних отчетов',
                'aggregate': 'Только агрегированные показатели - для публичной статистики'
            },
            'sensitive_fields_protected': [
                'ИИН/БИН',
                'ФИО',
                'Контактные данные (телефон, email)',
                'Адрес',
                'Паспортные данные',
                'Банковские реквизиты'
            ],
            'data_flow': {
                'internal': 'Полные данные хранятся только внутри СК',
                'to_arfr': 'Обезличенные + агрегированные данные',
                'to_fgsv': 'Обезличенные + агрегированные данные',
                'to_nbk': 'Только агрегированные показатели'
            },
            'retention_policy': {
                'personal_data': '5 лет после окончания договора',
                'anonymized_data': 'Бессрочно',
                'audit_logs': '10 лет'
            }
        },
        'timestamp': datetime.now().isoformat()
    })


@main_bp.route('/api/customers/export', methods=['GET'])
def api_customers_export():
    """
    API: Экспорт клиентов в Excel
    Параметры:
    - type: full (полные данные) или anonymized (обезличенные)
    """
    import io
    from flask import send_file

    export_type = request.args.get('type', 'full')

    # Демо-данные клиентов
    customers = [
        {
            'id': 1,
            'iin': '850415350789',
            'full_name': 'Иванов Иван Иванович',
            'phone': '+77071234567',
            'email': 'ivanov@mail.kz',
            'date_of_birth': '1985-04-15',
            'segment': 'VIP',
            'risk_rating': 'LOW',
            'total_policies': 3,
            'total_claims': 1,
            'customer_lifetime_value': 5800000,
        },
        {
            'id': 2,
            'iin': '920722450123',
            'full_name': 'Петрова Анна Сергеевна',
            'phone': '+77019876543',
            'email': 'petrova@gmail.com',
            'date_of_birth': '1992-07-22',
            'segment': 'STANDARD',
            'risk_rating': 'MEDIUM',
            'total_policies': 2,
            'total_claims': 0,
            'customer_lifetime_value': 1200000,
        },
        {
            'id': 3,
            'iin': '880903500345',
            'full_name': 'Сатпаева Динара Кайратовна',
            'phone': '+77074567890',
            'email': 'satpaeva@mail.kz',
            'date_of_birth': '1988-09-03',
            'segment': 'VIP',
            'risk_rating': 'LOW',
            'total_policies': 5,
            'total_claims': 2,
            'customer_lifetime_value': 4200000,
        }
    ]

    if export_type == 'anonymized':
        from app.services.data_anonymization import get_anonymizer
        anonymizer = get_anonymizer()

        # Обезличиваем данные
        export_data = []
        for c in customers:
            export_data.append({
                'ID': anonymizer.generate_anonymous_id(c['id']),
                'ИИН (хеш)': anonymizer.hash_identifier(c['iin']),
                'Сегмент': c['segment'],
                'Риск': c['risk_rating'],
                'Полисов': c['total_policies'],
                'Убытков': c['total_claims'],
                'CLV': c['customer_lifetime_value'],
            })
        filename = f'customers_anonymized_{datetime.now().strftime("%Y%m%d")}.xlsx'
    else:
        # Полные данные
        export_data = []
        for c in customers:
            export_data.append({
                'ID': c['id'],
                'ИИН': c['iin'],
                'ФИО': c['full_name'],
                'Телефон': c['phone'],
                'Email': c['email'],
                'Дата рождения': c['date_of_birth'],
                'Сегмент': c['segment'],
                'Риск': c['risk_rating'],
                'Полисов': c['total_policies'],
                'Убытков': c['total_claims'],
                'CLV': c['customer_lifetime_value'],
            })
        filename = f'customers_full_{datetime.now().strftime("%Y%m%d")}.xlsx'

    # Создаем Excel файл
    try:
        import pandas as pd
        df = pd.DataFrame(export_data)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Клиенты')
        output.seek(0)

        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
    except ImportError:
        # Если pandas не установлен, возвращаем CSV
        import csv
        output = io.StringIO()
        if export_data:
            writer = csv.DictWriter(output, fieldnames=export_data[0].keys())
            writer.writeheader()
            writer.writerows(export_data)

        csv_output = io.BytesIO(output.getvalue().encode('utf-8-sig'))
        csv_output.seek(0)

        return send_file(
            csv_output,
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename.replace('.xlsx', '.csv')
        )
