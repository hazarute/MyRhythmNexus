from pathlib import Path
import subprocess
import os
import sys


def run_build_script() -> bool:
    """Run the appropriate build script for the current platform.

    On Windows this runs `build-desktop.bat`. If running on Unix and a
    `build-desktop.sh` exists, it will run that instead.
    """
    if os.name == 'nt':
        script = Path('build-desktop.bat')
        if not script.exists():
            print('build-desktop.bat not found', file=sys.stderr)
            return False
        cmd = ['cmd', '/c', str(script)]
    else:
        script = Path('build-desktop.sh')
        if not script.exists():
            print('build-desktop.sh not found', file=sys.stderr)
            return False
        cmd = ['sh', str(script)]
    print('Running build script:', ' '.join(cmd))
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print('Build failed:', e, file=sys.stderr)
        return False
    return True
