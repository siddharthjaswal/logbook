"""
Expense models for trip expense tracking and budget management.

Includes:
- Expense: Individual expense entries
- ExpenseSplit: For splitting expenses among travelers
- BudgetCategory: Budget allocation by category
"""

from sqlalchemy import Column, String, Text, Integer, DECIMAL, Boolean, TIMESTAMP, ForeignKey, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import ENUM, JSON

from app.core.database import Base
from app.shared.enums import ExpenseCategory, PaymentMethod


class Expense(Base):
    """Expense model for trip expenses."""

    __tablename__ = "expenses"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Foreign Keys
    trip_id = Column(Integer, ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True)
    trip_day_id = Column(Integer, ForeignKey("trip_days.id", ondelete="CASCADE"), nullable=True, index=True)

    # Optional links to existing entities
    accommodation_id = Column(Integer, ForeignKey("accommodations.id", ondelete="SET NULL"), nullable=True)
    transit_id = Column(Integer, ForeignKey("transits.id", ondelete="SET NULL"), nullable=True)
    activity_id = Column(Integer, ForeignKey("activities.id", ondelete="SET NULL"), nullable=True)
    booking_id = Column(Integer, ForeignKey("bookings.id", ondelete="SET NULL"), nullable=True)

    # Expense Details
    category = Column(
        ENUM(ExpenseCategory, name="expense_category", create_type=True),
        nullable=False,
        index=True
    )
    description = Column(String(500), nullable=False)

    # Amount (primary currency - trip currency)
    amount = Column(DECIMAL(10, 2), nullable=False)
    currency = Column(String(3), default="USD", nullable=False)

    # Original amount (if paid in different currency)
    original_amount = Column(DECIMAL(10, 2), nullable=True)
    original_currency = Column(String(3), nullable=True)
    exchange_rate = Column(DECIMAL(10, 6), nullable=True)

    # Payment Details
    payment_method = Column(
        ENUM(PaymentMethod, name="payment_method", create_type=True),
        nullable=True
    )
    paid_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    is_shared = Column(Boolean, default=False, nullable=False)

    # Date/Time
    expense_date = Column(Date, nullable=False, index=True)
    expense_time = Column(String(5), nullable=True)  # HH:MM format

    # Metadata
    notes = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)  # Array of tags for categorization

    # Timestamps
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(TIMESTAMP, nullable=True)  # Soft delete

    # Relationships
    trip = relationship("Trip", back_populates="expenses")
    trip_day = relationship("TripDay", back_populates="expenses")
    paid_by = relationship("User", foreign_keys=[paid_by_user_id])
    splits = relationship("ExpenseSplit", back_populates="expense", cascade="all, delete-orphan")

    # Optional entity relationships
    accommodation = relationship("Accommodation", foreign_keys=[accommodation_id])
    transit = relationship("Transit", foreign_keys=[transit_id])
    activity = relationship("Activity", foreign_keys=[activity_id])
    booking = relationship("Booking", foreign_keys=[booking_id])

    def __repr__(self):
        return f"<Expense(id={self.id}, description='{self.description}', amount={self.amount} {self.currency})>"


class ExpenseSplit(Base):
    """Expense split model for sharing expenses among travelers."""

    __tablename__ = "expense_splits"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Foreign Keys
    expense_id = Column(Integer, ForeignKey("expenses.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Split Details
    amount = Column(DECIMAL(10, 2), nullable=False)
    percentage = Column(DECIMAL(5, 2), nullable=True)  # Optional percentage

    # Settlement
    is_settled = Column(Boolean, default=False, nullable=False)
    settled_at = Column(TIMESTAMP, nullable=True)

    # Timestamps
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)

    # Relationships
    expense = relationship("Expense", back_populates="splits")
    user = relationship("User")

    def __repr__(self):
        return f"<ExpenseSplit(id={self.id}, expense_id={self.expense_id}, user_id={self.user_id}, amount={self.amount})>"


class BudgetCategory(Base):
    """Budget category model for trip budget planning."""

    __tablename__ = "budget_categories"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Foreign Key
    trip_id = Column(Integer, ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True)

    # Budget Details
    category = Column(
        ENUM(ExpenseCategory, name="expense_category", create_type=False),  # Reuse existing enum
        nullable=False,
        index=True
    )
    budgeted_amount = Column(DECIMAL(10, 2), nullable=False)
    currency = Column(String(3), default="USD", nullable=False)

    # Metadata
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    trip = relationship("Trip", back_populates="budget_categories")

    def __repr__(self):
        return f"<BudgetCategory(id={self.id}, trip_id={self.trip_id}, category='{self.category}', budget={self.budgeted_amount})>"
