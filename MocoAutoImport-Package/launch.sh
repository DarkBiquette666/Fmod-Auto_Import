#!/bin/bash
# ============================================
# Moco Auto Import - Lanceur macOS/Linux
# ============================================

echo ""
echo "========================================"
echo "   Moco Auto Import pour FMOD Studio"
echo "========================================"
echo ""

# Vérifier que Python est installé
if ! command -v python3 &> /dev/null; then
    echo "ERREUR: Python 3 n'est pas installé"
    echo ""
    echo "Installation:"
    echo "  - macOS: brew install python3"
    echo "  - Ubuntu/Debian: sudo apt-get install python3"
    echo "  - Fedora: sudo dnf install python3"
    echo ""
    exit 1
fi

echo "Python détecté:"
python3 --version
echo ""

# Vérifier tkinter (Linux uniquement)
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    python3 -c "import tkinter" 2>/dev/null
    if [ $? -ne 0 ]; then
        echo "ATTENTION: tkinter n'est pas installé"
        echo "Installez-le avec:"
        echo "  Ubuntu/Debian: sudo apt-get install python3-tk"
        echo "  Fedora: sudo dnf install python3-tkinter"
        echo ""
        exit 1
    fi
fi

# Lancer l'application
echo "Lancement de Moco Auto Import..."
echo ""
python3 moco_auto_import.py

# Vérifier le code de sortie
if [ $? -ne 0 ]; then
    echo ""
    echo "ERREUR lors du lancement de l'application"
    echo ""
    read -p "Appuyez sur Entrée pour continuer..."
fi
