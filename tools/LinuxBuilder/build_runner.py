from pathlib import Path
import subprocess
import os
from typing import Optional


def run_local_build(script: Path) -> bool:
    if not script.exists():
        print('build script not found:', script)
        return False
    cmd = ['sh', str(script)]
    print('Running local build:', ' '.join(cmd))
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print('Build failed:', e)
        return False
    return True


def run_docker_builder(version: Optional[str], cwd: Path, image: str = 'myrhythm-desktop-builder:latest', dockerfile: Path = Path('tools/desktop-builder/Dockerfile')) -> bool:
    # Builds the docker builder image and runs it, mapping cwd/dist and cwd/release
    print('Building Docker image for builder...')
    cmd_build = ['docker', 'build', '-t', image, '-f', str(dockerfile), '.']
    try:
        subprocess.run(cmd_build, check=True)
    except subprocess.CalledProcessError as e:
        print('Docker build failed:', e)
        return False

    dist_host = str(cwd / 'dist')
    release_host = str(cwd / 'release')
    os.makedirs(dist_host, exist_ok=True)
    os.makedirs(release_host, exist_ok=True)
    # Always mount release directory so built artifacts are available to host
    mounts = ['-e', f'VERSION={version}', '-v', f'{dist_host}:/src/dist', '-v', f'{str(cwd)}:/src', '-v', f'{release_host}:/src/release']
    cmd_run = ['docker', 'run', '--rm'] + mounts + [image, '/bin/bash', '-lc', './build-desktop.sh']
    print('Running Docker builder...')
    try:
        subprocess.run(cmd_run, check=True)
    except subprocess.CalledProcessError as e:
        print('Docker run failed:', e)
        return False
    return True
