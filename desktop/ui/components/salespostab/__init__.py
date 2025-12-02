"""
SalesPOSTab Components Package
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Modular components specifically designed for the SalesPOS tab.
These components handle member selection, payment details, date selection,
package selection, class event scheduling, and submission.
"""

from .member_selector import MemberSelector
from desktop.core.locale import _
from .payment_details import PaymentDetails
from .date_selector import DateSelector
from .package_selector import PackageSelector
from .class_event_scheduler import ClassEventScheduler
from .submission_handler import SubmissionHandler

__all__ = [
    "MemberSelector",
    "PaymentDetails",
    "DateSelector",
    "PackageSelector",
    "ClassEventScheduler",
    "SubmissionHandler",
]
