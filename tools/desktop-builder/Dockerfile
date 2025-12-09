FROM python:3.11-slim

# Reproducible desktop builder for Linux single-file binary
# - Copies the repository into /src
# - Installs system deps required by PyInstaller and GUI libs
# - Installs Python deps from requirements.txt and PyInstaller
# - Runs the build helper and the studio packager, leaving artifacts in /src/release

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
     && apt-get install -y --no-install-recommends \
         build-essential \
         gcc \
         libssl-dev \
         libgtk-3-dev \
         libgdk-pixbuf-xlib-2.0-dev \
         libglib2.0-dev \
         libx11-dev \
         tk-dev \
         ca-certificates \
         unzip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /src

COPY . /src

# Use pip to install requirements and PyInstaller. Pin PyInstaller to 5.x for compatibility.
RUN python -m pip install --upgrade pip setuptools wheel \
 && python -m pip install -r requirements.txt \
 && python -m pip install "pyinstaller>=5.0,<6.0"

VOLUME ["/src/release"]

CMD ["/bin/bash", "-lc", "sh ./build-desktop.sh || true"]
