"""
Member-related dialog modules
Each dialog is in its own file for better maintainability
"""

from .add_member_dialog import AddMemberDialog
from desktop.core.locale import _
from .update_member_dialog import UpdateMemberDialog
from .update_password_dialog import UpdatePasswordDialog
from .add_measurement_dialog import AddMeasurementDialog
from .finance.debt_payment_dialog import DebtPaymentDialog
from .finance.debt_members_dialog import DebtMembersDialog
from .package_detail_dialog import PackageDetailDialog
from .add_package_dialog import AddPackageDialog
from .add_category_dialog import AddCategoryDialog
from .add_offering_dialog import AddOfferingDialog
from .add_plan_dialog import AddPlanDialog

__all__ = [
    'AddMemberDialog',
    'UpdateMemberDialog',
    'UpdatePasswordDialog',
    'AddMeasurementDialog',
    'DebtPaymentDialog',
    'DebtMembersDialog',
    'PackageDetailDialog',
    'AddPackageDialog',
    'AddCategoryDialog',
    'AddOfferingDialog',
    'AddPlanDialog',
]
