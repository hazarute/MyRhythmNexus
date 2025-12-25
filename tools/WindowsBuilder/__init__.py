"""WindowsBuilder helper package for CI build and release.

Modules:
- build_runner: runs platform-appropriate build scripts
- artifact: finds built artifacts and reads version
- github_release: GitHub release creation/upload helper
"""

__all__ = [
    "build_runner",
    "artifact",
    "github_release",
]
