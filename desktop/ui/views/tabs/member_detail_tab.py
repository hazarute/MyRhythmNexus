"""Compatibility alias: keep imports to tabs.member_detail_tab working.

This module exposes `MemberDetailTab` name by importing the canonical
`MemberDetailView` from `desktop.ui.views.member_detail` and aliasing it.
Do not keep two divergent implementations — `desktop/ui/views/member_detail.py`
is the single source of truth.
"""

from desktop.ui.views.member_detail import MemberDetailView as MemberDetailTab

__all__ = ["MemberDetailTab"]
