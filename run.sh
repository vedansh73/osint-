#!/bin/bash
set -e

echo "=========================================="
echo "   SETTING UP & STARTING OSINT SUITE      "
echo "=========================================="

if ! command -v python3 &> /dev/null; then
    echo "[!] Python3 is not installed. Please install Python3 first."
    exit 1
fi

if [ ! -d "venv" ]; then
    echo "[*] Creating virtual environment (venv)..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt

echo "[+] Starting scanner.py..."
python3 scanner.py
