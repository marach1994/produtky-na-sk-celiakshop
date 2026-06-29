#!/bin/bash
cd "$(dirname "$0")"
python3 transform.py
echo ""
echo "Hotovo! Soubor celiakshop_sk.csv je připraven k importu."
read -p "Stiskni Enter pro zavření..."
