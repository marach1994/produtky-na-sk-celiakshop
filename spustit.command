#!/bin/bash
cd "$(dirname "$0")"
python3 transform.py
echo ""
read -p "Stiskni Enter pro zavření..."
