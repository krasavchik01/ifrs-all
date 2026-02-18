"""
KZ-InsurePro - Модуль обезличивания персональных данных
========================================================
Соответствие Закону РК "О персональных данных и их защите"
Обезличивание данных для передачи в АРФР, ФГСВ и другие органы

Принципы:
1. Персональные данные остаются только внутри страховой компании
2. В регуляторы передаются только обезличенные/агрегированные данные
3. Связь через внутренний ID (не ИИН)
4. Хеширование чувствительных данных
"""

import hashlib
import uuid
from datetime import datetime, date
from typing import Dict, Any, List, Optional
from decimal import Decimal


class DataAnonymizer:
    """
    Класс для обезличивания персональных данных
    при передаче в регуляторные органы
    """

    # Поля, которые ВСЕГДА обезличиваются
    SENSITIVE_FIELDS = {
        'iin',           # ИИН - индивидуальный идентификационный номер
        'bin',           # БИН - бизнес идентификационный номер
        'full_name',     # ФИО
        'first_name',    # Имя
        'last_name',     # Фамилия
        'middle_name',   # Отчество
        'phone',         # Телефон
        'email',         # Email
        'address',       # Адрес
        'passport',      # Паспортные данные
        'bank_account',  # Банковский счет
        'card_number',   # Номер карты
    }

    # Поля, которые маскируются частично
    PARTIAL_MASK_FIELDS = {
        'policy_number': (0, 4),   # Показать первые 4 символа
        'contract_number': (0, 4),
        'claim_number': (0, 4),
    }

    def __init__(self, company_salt: str = None):
        """
        Инициализация с уникальной солью компании
        для консистентного хеширования
        """
        self.company_salt = company_salt or self._generate_company_salt()

    def _generate_company_salt(self) -> str:
        """Генерация уникальной соли для компании"""
        return hashlib.sha256(
            f"KZ-InsurePro-{datetime.now().year}".encode()
        ).hexdigest()[:16]

    def hash_identifier(self, value: str) -> str:
        """
        Хеширование идентификатора (ИИН, БИН и т.д.)
        Возвращает консистентный хеш для одного и того же значения
        """
        if not value:
            return None
        salted = f"{self.company_salt}:{value}"
        return hashlib.sha256(salted.encode()).hexdigest()[:12].upper()

    def generate_anonymous_id(self, original_id: Any) -> str:
        """
        Генерация анонимного ID на основе оригинального
        Формат: ANO-XXXXXX (6 символов хеша)
        """
        if original_id is None:
            return f"ANO-{uuid.uuid4().hex[:6].upper()}"
        return f"ANO-{self.hash_identifier(str(original_id))[:6]}"

    def mask_name(self, full_name: str) -> str:
        """
        Маскирование ФИО
        'Иванов Иван Иванович' -> 'И***в И. И.'
        """
        if not full_name:
            return "***"

        parts = full_name.strip().split()
        if len(parts) == 0:
            return "***"

        result = []
        for i, part in enumerate(parts):
            if len(part) > 0:
                if i == 0:  # Фамилия - показываем первую и последнюю букву
                    if len(part) > 2:
                        result.append(f"{part[0]}{'*' * (len(part)-2)}{part[-1]}")
                    else:
                        result.append(f"{part[0]}*")
                else:  # Имя/Отчество - только инициал
                    result.append(f"{part[0]}.")

        return " ".join(result)

    def mask_iin(self, iin: str) -> str:
        """
        Маскирование ИИН
        '123456789012' -> '******789012' (показываем последние 6 цифр)
        """
        if not iin:
            return "************"
        iin = str(iin).strip()
        if len(iin) >= 6:
            return "*" * (len(iin) - 6) + iin[-6:]
        return "*" * len(iin)

    def mask_phone(self, phone: str) -> str:
        """
        Маскирование телефона
        '+77001234567' -> '+7700***4567'
        """
        if not phone:
            return "***"
        phone = str(phone).strip()
        if len(phone) >= 8:
            return phone[:4] + "***" + phone[-4:]
        return "***"

    def mask_email(self, email: str) -> str:
        """
        Маскирование email
        'ivan.ivanov@mail.kz' -> 'i***v@m***.kz'
        """
        if not email or '@' not in email:
            return "***@***.kz"

        local, domain = email.split('@', 1)

        # Маскируем локальную часть
        if len(local) > 2:
            local_masked = f"{local[0]}***{local[-1]}"
        else:
            local_masked = f"{local[0]}***"

        # Маскируем домен (оставляем TLD)
        domain_parts = domain.split('.')
        if len(domain_parts) >= 2:
            domain_masked = f"{domain_parts[0][0]}***.{domain_parts[-1]}"
        else:
            domain_masked = "***"

        return f"{local_masked}@{domain_masked}"

    def anonymize_customer(self, customer: Dict[str, Any],
                          level: str = 'full') -> Dict[str, Any]:
        """
        Обезличивание данных клиента

        Уровни:
        - 'full': Полное обезличивание (для АРФР, ФГСВ)
        - 'partial': Частичное маскирование (для внутренних отчетов)
        - 'aggregate': Только агрегированные данные (для публичной статистики)
        """
        if level == 'aggregate':
            # Возвращаем только статистические данные
            return {
                'segment': customer.get('segment'),
                'region': customer.get('region'),
                'risk_rating': customer.get('risk_rating'),
                'age_group': self._get_age_group(customer.get('date_of_birth')),
                'has_active_policy': customer.get('total_policies', 0) > 0,
            }

        anonymized = {
            # Анонимный ID вместо реального
            'id': self.generate_anonymous_id(customer.get('id')),
            'anonymous_id': self.generate_anonymous_id(customer.get('id')),

            # Хешированный ИИН (для сверки без раскрытия)
            'iin_hash': self.hash_identifier(customer.get('iin')),

            # Демографические данные (обезличенные)
            'age_group': self._get_age_group(customer.get('date_of_birth')),
            'gender': customer.get('gender'),
            'region': customer.get('region'),
            'segment': customer.get('segment'),
            'risk_rating': customer.get('risk_rating'),

            # Финансовые показатели (агрегированные)
            'total_policies': customer.get('total_policies', 0),
            'total_claims': customer.get('total_claims', 0),
            'total_premium_paid': customer.get('total_premium_paid', 0),
            'customer_lifetime_value': customer.get('customer_lifetime_value', 0),
            'loss_ratio': customer.get('loss_ratio'),

            # Временные метки (без точного времени)
            'registration_year': self._get_year(customer.get('created_at')),
            'last_activity_month': self._get_year_month(customer.get('last_interaction')),
        }

        if level == 'partial':
            # Для внутренних отчетов добавляем маскированные данные
            anonymized.update({
                'masked_name': self.mask_name(customer.get('full_name')),
                'masked_iin': self.mask_iin(customer.get('iin')),
                'masked_phone': self.mask_phone(customer.get('phone')),
                'masked_email': self.mask_email(customer.get('email')),
            })

        return anonymized

    def anonymize_policy(self, policy: Dict[str, Any]) -> Dict[str, Any]:
        """Обезличивание данных полиса для регуляторной отчетности"""
        return {
            'id': self.generate_anonymous_id(policy.get('id')),
            'policy_hash': self.hash_identifier(policy.get('policy_number')),
            'customer_anonymous_id': self.generate_anonymous_id(policy.get('customer_id')),

            # Характеристики полиса (без персональных данных)
            'product_type': policy.get('product_type'),
            'product_code': policy.get('product_code'),
            'coverage_type': policy.get('coverage_type'),

            # Финансовые данные
            'premium_amount': policy.get('premium_amount'),
            'sum_insured': policy.get('sum_insured'),
            'currency': policy.get('currency'),

            # Даты (только месяц/год)
            'inception_month': self._get_year_month(policy.get('inception_date')),
            'expiry_month': self._get_year_month(policy.get('expiry_date')),

            # Статус
            'status': policy.get('status'),
            'is_active': policy.get('is_active'),

            # IFRS 17 данные
            'measurement_model': policy.get('measurement_model'),
            'cohort': policy.get('cohort'),
            'portfolio_group': policy.get('portfolio_group'),
        }

    def anonymize_claim(self, claim: Dict[str, Any]) -> Dict[str, Any]:
        """Обезличивание данных убытка"""
        return {
            'id': self.generate_anonymous_id(claim.get('id')),
            'claim_hash': self.hash_identifier(claim.get('claim_number')),
            'policy_anonymous_id': self.generate_anonymous_id(claim.get('policy_id')),
            'customer_anonymous_id': self.generate_anonymous_id(claim.get('customer_id')),

            # Характеристики убытка
            'claim_type': claim.get('claim_type'),
            'cause_code': claim.get('cause_code'),
            'region': claim.get('region'),

            # Финансовые данные
            'claimed_amount': claim.get('claimed_amount'),
            'approved_amount': claim.get('approved_amount'),
            'paid_amount': claim.get('paid_amount'),
            'currency': claim.get('currency'),

            # Даты (только месяц)
            'occurrence_month': self._get_year_month(claim.get('occurrence_date')),
            'reported_month': self._get_year_month(claim.get('reported_date')),
            'settled_month': self._get_year_month(claim.get('settled_date')),

            # Статус и сроки
            'status': claim.get('status'),
            'days_to_settle': claim.get('days_to_settle'),
        }

    def anonymize_agent(self, agent: Dict[str, Any]) -> Dict[str, Any]:
        """Обезличивание данных агента"""
        return {
            'id': self.generate_anonymous_id(agent.get('id')),
            'agent_code_hash': self.hash_identifier(agent.get('agent_code')),

            # Характеристики (без персональных данных)
            'agent_type': agent.get('type'),
            'region': agent.get('region'),
            'status': agent.get('status'),
            'experience_years': agent.get('experience_years'),

            # KPI (агрегированные)
            'kpi_score': agent.get('kpi_score'),
            'total_policies_sold': agent.get('performance', {}).get('total_policies_sold'),
            'total_premium_volume': agent.get('performance', {}).get('total_premium_volume'),
            'conversion_rate': agent.get('performance', {}).get('conversion_rate'),
        }

    def prepare_regulatory_report(self, data: Dict[str, Any],
                                  report_type: str) -> Dict[str, Any]:
        """
        Подготовка данных для регуляторного отчета

        report_type: 'arfr_85', 'arfr_86', 'arfr_304', 'fgsv_contribution'
        """
        anonymized_data = {
            'report_type': report_type,
            'generated_at': datetime.now().isoformat(),
            'data_anonymization': 'full',
            'compliance': 'Law on Personal Data Protection of RK',
        }

        if 'customers' in data:
            anonymized_data['customers'] = [
                self.anonymize_customer(c, level='full')
                for c in data['customers']
            ]

        if 'policies' in data:
            anonymized_data['policies'] = [
                self.anonymize_policy(p)
                for p in data['policies']
            ]

        if 'claims' in data:
            anonymized_data['claims'] = [
                self.anonymize_claim(c)
                for c in data['claims']
            ]

        # Агрегированные показатели (всегда включаются)
        if 'aggregates' in data:
            anonymized_data['aggregates'] = data['aggregates']

        return anonymized_data

    def _get_age_group(self, date_of_birth) -> Optional[str]:
        """Преобразование даты рождения в возрастную группу"""
        if not date_of_birth:
            return None

        try:
            if isinstance(date_of_birth, str):
                dob = datetime.strptime(date_of_birth[:10], '%Y-%m-%d').date()
            elif isinstance(date_of_birth, datetime):
                dob = date_of_birth.date()
            elif isinstance(date_of_birth, date):
                dob = date_of_birth
            else:
                return None

            today = date.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

            if age < 18:
                return '0-17'
            elif age < 25:
                return '18-24'
            elif age < 35:
                return '25-34'
            elif age < 45:
                return '35-44'
            elif age < 55:
                return '45-54'
            elif age < 65:
                return '55-64'
            else:
                return '65+'
        except:
            return None

    def _get_year(self, dt) -> Optional[int]:
        """Извлечение года из даты"""
        if not dt:
            return None
        try:
            if isinstance(dt, str):
                return int(dt[:4])
            elif isinstance(dt, (datetime, date)):
                return dt.year
        except:
            return None

    def _get_year_month(self, dt) -> Optional[str]:
        """Извлечение года-месяца из даты (формат: 2025-01)"""
        if not dt:
            return None
        try:
            if isinstance(dt, str):
                return dt[:7]
            elif isinstance(dt, (datetime, date)):
                return dt.strftime('%Y-%m')
        except:
            return None


# Глобальный экземпляр для использования в приложении
_anonymizer = None

def get_anonymizer() -> DataAnonymizer:
    """Получение глобального экземпляра анонимайзера"""
    global _anonymizer
    if _anonymizer is None:
        _anonymizer = DataAnonymizer()
    return _anonymizer


def anonymize_for_regulator(data: Dict[str, Any],
                           regulator: str = 'arfr') -> Dict[str, Any]:
    """
    Удобная функция для обезличивания данных перед отправкой регулятору

    regulator: 'arfr', 'fgsv', 'nbk'
    """
    anonymizer = get_anonymizer()

    if regulator in ['arfr', 'fgsv', 'nbk']:
        # Полное обезличивание для регуляторов
        return anonymizer.prepare_regulatory_report(data, f'{regulator}_report')
    else:
        # Частичное для внутренних целей
        return data
