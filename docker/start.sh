#!/bin/bash

test -f /opt/spacedock/config.ini || cp /opt/spacedock/config.ini.example /opt/spacedock/config.ini
test -f /opt/spacedock/alembic.ini || cp /opt/spacedock/alembic.ini.example /opt/spacedock/alembic.ini

/venv/spacedock/bin/python /opt/spacedock/app.py
