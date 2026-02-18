"""
CRM Models for KZ-InsurePro
Customer Management, Agents, and Commission tracking
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum as PyEnum
from sqlalchemy import (
    Column, String, Integer, Numeric, Boolean, DateTime,
    ForeignKey, Text, JSON, Index
)
from sqlalchemy.orm import relationship
from app.models.database import Base


# =============================================================================
# ENUMS
# =============================================================================

class CustomerSegment(str, PyEnum):
    VIP = "VIP"
    STANDARD = "STANDARD"
    RISK = "RISK"
    PROSPECT = "PROSPECT"


class InteractionChannel(str, PyEnum):
    EMAIL = "EMAIL"
    PHONE = "PHONE"
    SMS = "SMS"
    APP = "APP"
    OFFICE = "OFFICE"
    WEBSITE = "WEBSITE"


class InteractionType(str, PyEnum):
    QUOTE_REQUEST = "QUOTE_REQUEST"
    COMPLAINT = "COMPLAINT"
    CLAIM = "CLAIM"
    RENEWAL = "RENEWAL"
    CONSULTATION = "CONSULTATION"
    PAYMENT = "PAYMENT"


class InteractionResult(str, PyEnum):
    CONVERTED = "CONVERTED"
    PENDING = "PENDING"
    REJECTED = "REJECTED"
    RESOLVED = "RESOLVED"


class AgentType(str, PyEnum):
    INDIVIDUAL = "INDIVIDUAL"
    BROKER = "BROKER"
    CORPORATE = "CORPORATE"
    BANCASSURANCE = "BANCASSURANCE"


class AgentStatus(str, PyEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"


# =============================================================================
# CUSTOMER MODELS
# =============================================================================

class Customer(Base):
    """Customer/Policyholder entity with 360° view"""
    __tablename__ = "customers"

    # Primary key
    id = Column(String, primary_key=True, default=lambda: f"cust_{datetime.now().timestamp()}")
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)
    external_id = Column(String, nullable=True)

    # Basic information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    middle_name = Column(String(100), nullable=True)
    date_of_birth = Column(DateTime, nullable=True)
    iin = Column(String(12), unique=True, nullable=True, index=True)  # IIN - 12 digits

    # Contact information
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(20), nullable=True, index=True)
    mobile = Column(String(20), nullable=True)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    country = Column(String(3), default="KZ")

    # Financial profile
    credit_rating = Column(String(10), nullable=True)  # AAA, BBB, C, etc.
    payment_history_score = Column(Numeric(5, 2), nullable=True)  # 0-100
    average_payment_delay = Column(Integer, default=0)  # days

    # Insurance profile
    risk_rating = Column(String(20), nullable=True, index=True)  # LOW, MEDIUM, HIGH
    total_claims_count = Column(Integer, default=0)
    total_claims_amount = Column(Numeric(15, 2), default=0)
    last_claim_date = Column(DateTime, nullable=True)

    # Segmentation and analytics
    segment = Column(String(20), default=CustomerSegment.STANDARD.value, index=True)
    customer_lifetime_value = Column(Numeric(15, 2), default=0)  # CLV
    acquisition_cost = Column(Numeric(10, 2), default=0)
    acquisition_date = Column(DateTime, default=datetime.utcnow)
    acquisition_channel = Column(String(50), nullable=True)

    # Status
    is_active = Column(Boolean, default=True)
    is_blocked = Column(Boolean, default=False)
    blocked_reason = Column(Text, nullable=True)

    # Preferences
    preferred_language = Column(String(5), default="kz")
    marketing_consent = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_interaction_at = Column(DateTime, nullable=True)

    # Relationships
    interactions = relationship("CustomerInteraction", back_populates="customer")

    # Indexes
    __table_args__ = (
        Index("idx_customer_tenant", "tenant_id"),
        Index("idx_customer_segment", "segment"),
        Index("idx_customer_risk", "risk_rating"),
    )

    def __repr__(self):
        return f"<Customer {self.first_name} {self.last_name} (IIN: {self.iin})>"

    @property
    def full_name(self):
        """Get full name"""
        parts = [self.last_name, self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        return " ".join(parts)

    def calculate_clv(self, avg_policy_value: Decimal, retention_years: int = 5) -> Decimal:
        """Calculate Customer Lifetime Value"""
        # Simple CLV = (Avg Annual Revenue × Retention Rate) × Retention Period - Acquisition Cost
        annual_revenue = avg_policy_value
        retention_rate = 0.85  # 85% retention assumption
        clv = (annual_revenue * Decimal(retention_rate)) * retention_years - self.acquisition_cost
        return clv

    def get_risk_score(self) -> int:
        """Calculate risk score 0-100 (higher = riskier)"""
        score = 0

        # Claims history (40 points)
        if self.total_claims_count > 5:
            score += 40
        elif self.total_claims_count > 2:
            score += 25
        elif self.total_claims_count > 0:
            score += 10

        # Payment history (30 points)
        if self.payment_history_score:
            score += int(30 - (float(self.payment_history_score) * 0.3))

        # Payment delays (30 points)
        if self.average_payment_delay > 30:
            score += 30
        elif self.average_payment_delay > 14:
            score += 20
        elif self.average_payment_delay > 0:
            score += 10

        return min(score, 100)


class CustomerInteraction(Base):
    """Customer interaction tracking for CRM"""
    __tablename__ = "customer_interactions"

    # Primary key
    id = Column(String, primary_key=True, default=lambda: f"int_{datetime.now().timestamp()}")
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)
    customer_id = Column(String, ForeignKey("customers.id"), nullable=True)

    # Interaction details
    channel = Column(String(20), nullable=False, index=True)
    type = Column(String(30), nullable=False, index=True)
    subject = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Result
    result = Column(String(20), default=InteractionResult.PENDING.value, index=True)
    resolution_notes = Column(Text, nullable=True)

    # Timing
    started_at = Column(DateTime, default=datetime.utcnow, index=True)
    ended_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)

    # User/Agent who handled
    handled_by = Column(String, nullable=True)  # User ID
    agent_id = Column(String, ForeignKey("agents.id"), nullable=True)

    # Follow-up
    requires_followup = Column(Boolean, default=False)
    followup_date = Column(DateTime, nullable=True)

    # Conversion tracking
    converted_to_policy = Column(Boolean, default=False)
    policy_id = Column(String, nullable=True)
    estimated_value = Column(Numeric(12, 2), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    customer = relationship("Customer", back_populates="interactions")
    agent = relationship("Agent", back_populates="interactions")

    # Indexes
    __table_args__ = (
        Index("idx_interaction_tenant", "tenant_id"),
        Index("idx_interaction_customer", "customer_id"),
        Index("idx_interaction_agent", "agent_id"),
        Index("idx_interaction_channel", "channel"),
        Index("idx_interaction_type", "type"),
    )

    def __repr__(self):
        return f"<Interaction {self.type} via {self.channel} - {self.result}>"

    def calculate_duration(self):
        """Calculate and set duration if not already set"""
        if self.ended_at and self.started_at:
            delta = self.ended_at - self.started_at
            self.duration_seconds = int(delta.total_seconds())


# =============================================================================
# AGENT MODELS
# =============================================================================

class Agent(Base):
    """Insurance agent/broker entity"""
    __tablename__ = "agents"

    # Primary key
    id = Column(String, primary_key=True, default=lambda: f"agent_{datetime.now().timestamp()}")
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)
    external_id = Column(String, nullable=True)

    # Basic information
    agent_code = Column(String(50), unique=True, nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    middle_name = Column(String(100), nullable=True)
    iin = Column(String(12), nullable=True)
    bin = Column(String(12), nullable=True)  # For corporate agents

    # Type and classification
    type = Column(String(20), default=AgentType.INDIVIDUAL.value, index=True)
    status = Column(String(20), default=AgentStatus.ACTIVE.value, index=True)
    license_number = Column(String(50), nullable=True)
    license_expiry_date = Column(DateTime, nullable=True)

    # Contact information
    email = Column(String(255), nullable=False, index=True)
    phone = Column(String(20), nullable=False)
    mobile = Column(String(20), nullable=True)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    region = Column(String(100), nullable=True)

    # Organizational structure
    parent_agent_id = Column(String, ForeignKey("agents.id"), nullable=True, index=True)
    hierarchy_level = Column(Integer, default=1)
    team_size = Column(Integer, default=0)

    # Performance metrics
    total_policies_sold = Column(Integer, default=0)
    total_premium_volume = Column(Numeric(15, 2), default=0)
    total_commission_earned = Column(Numeric(12, 2), default=0)
    average_policy_value = Column(Numeric(12, 2), default=0)
    conversion_rate = Column(Numeric(5, 2), default=0)  # 0-100%
    retention_rate = Column(Numeric(5, 2), default=0)  # 0-100%
    customer_satisfaction_score = Column(Numeric(3, 2), default=0)  # 0-10

    # Dates
    onboarding_date = Column(DateTime, default=datetime.utcnow)
    last_sale_date = Column(DateTime, nullable=True)
    contract_start_date = Column(DateTime, nullable=False)
    contract_end_date = Column(DateTime, nullable=True)

    # Commission settings (defaults)
    default_commission_rate = Column(Numeric(5, 4), default=0.05)  # 5%
    payment_method = Column(String(50), default="BANK_TRANSFER")
    bank_account = Column(String(100), nullable=True)
    bank_name = Column(String(100), nullable=True)

    # Status
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    parent_agent = relationship("Agent", remote_side=[id], backref="child_agents")
    commission_structures = relationship("CommissionStructure", back_populates="agent")
    commission_payments = relationship("CommissionPayment", back_populates="agent")
    interactions = relationship("CustomerInteraction", back_populates="agent")

    # Indexes
    __table_args__ = (
        Index("idx_agent_tenant", "tenant_id"),
        Index("idx_agent_code", "agent_code"),
        Index("idx_agent_status", "status"),
        Index("idx_agent_type", "type"),
    )

    def __repr__(self):
        return f"<Agent {self.agent_code} - {self.first_name} {self.last_name}>"

    @property
    def full_name(self):
        """Get full name"""
        parts = [self.last_name, self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        return " ".join(parts)

    def calculate_kpi_score(self) -> Decimal:
        """Calculate overall KPI score 0-100"""
        # Weighted scoring
        conversion_weight = 0.3
        retention_weight = 0.3
        satisfaction_weight = 0.2
        volume_weight = 0.2

        # Normalize volume (assume 1M KZT monthly as benchmark)
        volume_score = min(float(self.total_premium_volume) / 1000000 * 100, 100)

        score = (
            float(self.conversion_rate) * conversion_weight +
            float(self.retention_rate) * retention_weight +
            float(self.customer_satisfaction_score) * 10 * satisfaction_weight +
            volume_score * volume_weight
        )

        return Decimal(str(round(score, 2)))


class CommissionStructure(Base):
    """Commission structure for agents"""
    __tablename__ = "commission_structures"

    # Primary key
    id = Column(String, primary_key=True, default=lambda: f"comm_struct_{datetime.now().timestamp()}")
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)
    agent_id = Column(String, ForeignKey("agents.id"), nullable=True)

    # Structure details
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    insurance_type = Column(String(20), nullable=True, index=True)
    product_code = Column(String(50), nullable=True)

    # Commission rates
    base_commission_rate = Column(Numeric(5, 4), nullable=False)  # 0-1
    renewal_commission_rate = Column(Numeric(5, 4), default=0)

    # Tier-based rates (JSON)
    tier_rates = Column(JSON, nullable=True)

    # Bonus structure
    has_bonus = Column(Boolean, default=False)
    bonus_threshold = Column(Numeric(12, 2), nullable=True)
    bonus_rate = Column(Numeric(5, 4), nullable=True)

    # Validity
    effective_from = Column(DateTime, default=datetime.utcnow, index=True)
    effective_to = Column(DateTime, nullable=True, index=True)
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    agent = relationship("Agent", back_populates="commission_structures")

    # Indexes
    __table_args__ = (
        Index("idx_commstruct_tenant", "tenant_id"),
        Index("idx_commstruct_agent", "agent_id"),
        Index("idx_commstruct_validity", "effective_from", "effective_to"),
    )

    def __repr__(self):
        return f"<CommissionStructure {self.name} - {self.base_commission_rate}>"

    def calculate_commission(self, premium_amount: Decimal, is_renewal: bool = False) -> Decimal:
        """Calculate commission amount"""
        if is_renewal:
            rate = self.renewal_commission_rate
        else:
            rate = self.base_commission_rate

        commission = premium_amount * rate

        # Check for bonus
        if self.has_bonus and self.bonus_threshold and premium_amount >= self.bonus_threshold:
            bonus = premium_amount * (self.bonus_rate or Decimal(0))
            commission += bonus

        return commission


class CommissionPayment(Base):
    """Commission payment tracking"""
    __tablename__ = "commission_payments"

    # Primary key
    id = Column(String, primary_key=True, default=lambda: f"comm_pay_{datetime.now().timestamp()}")
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)
    agent_id = Column(String, ForeignKey("agents.id"), nullable=False)

    # Payment period
    period_start = Column(DateTime, nullable=False, index=True)
    period_end = Column(DateTime, nullable=False, index=True)
    payment_date = Column(DateTime, nullable=True, index=True)

    # Calculation basis
    policies_count = Column(Integer, nullable=False)
    total_premium_volume = Column(Numeric(15, 2), nullable=False)

    # Commission amounts
    base_commission = Column(Numeric(12, 2), nullable=False)
    renewal_commission = Column(Numeric(12, 2), default=0)
    bonus_commission = Column(Numeric(12, 2), default=0)
    total_commission = Column(Numeric(12, 2), nullable=False)

    # Adjustments
    adjustments = Column(Numeric(10, 2), default=0)
    adjustment_notes = Column(Text, nullable=True)

    # Tax and deductions
    tax_amount = Column(Numeric(10, 2), default=0)
    deductions = Column(Numeric(10, 2), default=0)
    net_payable = Column(Numeric(12, 2), nullable=False)

    # Payment status
    status = Column(String(20), default="PENDING", index=True)
    approved_by = Column(String, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    paid_at = Column(DateTime, nullable=True)

    # Payment details
    payment_method = Column(String(50), nullable=True)
    transaction_reference = Column(String(100), nullable=True)
    payment_notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    agent = relationship("Agent", back_populates="commission_payments")

    # Indexes
    __table_args__ = (
        Index("idx_commpay_tenant", "tenant_id"),
        Index("idx_commpay_agent", "agent_id"),
        Index("idx_commpay_period", "period_start", "period_end"),
        Index("idx_commpay_status", "status"),
    )

    def __repr__(self):
        return f"<CommissionPayment {self.agent_id} - {self.total_commission} KZT ({self.status})>"

    def calculate_net_payable(self):
        """Calculate net payable amount"""
        self.net_payable = (
            self.total_commission +
            self.adjustments -
            self.tax_amount -
            self.deductions
        )
