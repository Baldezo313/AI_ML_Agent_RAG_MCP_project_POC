---
title: Recrutement IA — Multi-Agent Workflow
emoji: 🤖
colorFrom: indigo
colorTo: purple
sdk: gradio
sdk_version: 6.17.3
app_file: app.py
pinned: false
---

<div align="center">

# 🤖 Recrutement IA — Multi-Agent Workflow

**Analysez et classez automatiquement vos candidats grâce à l'IA Mistral**

[![Mistral AI](https://img.shields.io/badge/Powered%20by-Mistral%20AI-ff7000?style=flat-square&logo=data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0id2hpdGUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHBhdGggZD0iTTEyIDJMMiA3bDEwIDUgMTAtNS0xMC01ek0yIDE3bDEwIDUgMTAtNS0xMC01LTEwIDV6TTIgMTJsMTAgNSAxMC01LTEwLTUtMTAgNXoiLz48L3N2Zz4=)](https://mistral.ai)
[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Gradio](https://img.shields.io/badge/UI-Gradio-FF6B35?style=flat-square)](https://gradio.app)
[![License](https://img.shields.io/badge/License-MIT-22c55e?style=flat-square)](LICENSE)

---

*Upload plusieurs CVs, saisissez l'offre d'emploi — obtenez un classement instantané avec scores détaillés.*

</div>

---

## ✨ Fonctionnalités

| Fonctionnalité | Description |
|---|---|
| 📁 **Multi-CV** | Analysez 1 à N CVs en un seul passage |
| 📋 **Offre flexible** | Upload PDF **ou** copier-coller le texte |
| 🏆 **Classement automatique** | Les candidats sont triés par score décroissant |
| 📊 **Scores détaillés** | Compétences, expérience, formation, bonus |
| ✅❌ **Forces & lacunes** | Synthèse qualitative par candidat |
| 🎨 **Interface moderne** | UI sombre, barres de score colorées, responsive |

---

## 🏗️ Architecture multi-agents

```
PDF(s) candidats         Offre d'emploi (PDF ou texte)
       │                          │
       ▼                          ▼
┌─────────────────┐    ┌──────────────────────┐
│  DocumentAgent  │    │   DocumentAgent (OCR) │  ← mistral-ocr-latest
│  OCR sur chaque │    │   (si PDF uploadé)    │
│  CV             │    └──────────┬───────────┘
└───────┬─────────┘               │
        │                         ▼
        │              ┌──────────────────────┐
        │              │   JobAnalysisAgent   │  ← mistral-small-latest
        │              │   Extraction         │
        │              │   structurée du poste│
        │              └──────────┬───────────┘
        │                         │
        ▼                         │
┌─────────────────┐               │
│ ResumeAnalysis  │               │
│ Agent           │               │  ← mistral-small-latest
│ (x N candidats) │               │
└───────┬─────────┘               │
        │                         │
        └──────────┬──────────────┘
                   ▼
         ┌──────────────────┐
         │  MatchingAgent   │  ← mistral-small-latest
         │  Score /100 par  │
         │  candidat        │
         └──────────────────┘
                   │
                   ▼
         🏆 Classement + cartes candidats
```

### Détail des agents

| Agent | Modèle | Rôle |
|---|---|---|
| `DocumentAgent` | `mistral-ocr-latest` | Extraction texte depuis les PDFs |
| `JobAnalysisAgent` | `mistral-small-latest` | Parse l'offre → `JobRequirements` |
| `ResumeAnalysisAgent` | `mistral-small-latest` | Parse chaque CV → `CandidateProfile` |
| `MatchingAgent` | `mistral-small-latest` | Évalue et score le matching |

---

## 📊 Grille de scoring

```
┌──────────────────────────────┬──────────┐
│ Critère                      │ Max pts  │
├──────────────────────────────┼──────────┤
│ 🛠  Compétences techniques   │  40 pts  │
│ 💼  Expérience professionnelle│  30 pts  │
│ 🎓  Formation / Diplômes     │  15 pts  │
│ ⭐  Critères supplémentaires │  15 pts  │
├──────────────────────────────┼──────────┤
│ 🏆  Total                    │ 100 pts  │
└──────────────────────────────┴──────────┘

🟢 ≥ 75 pts  → Excellent match
🟡 ≥ 50 pts  → Correspondance partielle
🔴 < 50 pts  → Faible correspondance
```

---

## 🚀 Utilisation

### 1. Obtenez une clé API Mistral

→ [console.mistral.ai](https://console.mistral.ai/) (gratuit pour débuter)

### 2. Préparez vos fichiers

- **CVs** : un ou plusieurs fichiers PDF
- **Offre d'emploi** : PDF **ou** texte à coller directement

### 3. Lancez l'analyse

1. Collez votre clé API dans le champ prévu
2. Uploadez les CVs (bouton multi-sélection)
3. Choisissez le mode offre : PDF ou texte
4. Cliquez sur **🚀 Analyser les candidats**

### 4. Lisez les résultats

- Un **tableau de classement** apparaît en tête
- Chaque candidat a sa **carte détaillée** avec scores, forces et lacunes

---

## 📂 Structure du projet

```
.
├── app.py          # Interface Gradio + orchestration du pipeline
├── agents.py       # Les 4 agents Mistral
├── models.py       # Schémas Pydantic (JobRequirements, CandidateProfile, CandidateScore)
├── requirements.txt
└── README.md
```

---

## ⚙️ Installation locale

```bash
git clone https://huggingface.co/spaces/<your-username>/recrutement-ia
cd recrutement-ia
pip install -r requirements.txt
python app.py
```

---

## 📦 Dépendances

```
mistralai>=1.0.0
pydantic>=2.0.0
gradio>=4.0.0
```

---

## 🔒 Confidentialité

- Votre clé API n'est **jamais stockée** — elle est utilisée uniquement pendant la session
- Les fichiers uploadés sont traités en mémoire et supprimés après analyse
- L'API Mistral est soumise à sa [politique de confidentialité](https://mistral.ai/privacy-policy/)

---

## 🤝 Contribuer

Les PRs sont les bienvenues ! Idées d'améliorations :

- [ ] Export PDF / CSV du rapport de classement
- [ ] Support de formats supplémentaires (DOCX, LinkedIn)
- [ ] Mode comparaison côte-à-côte
- [ ] Filtrage par seuil de score minimum
- [ ] Génération de mail de réponse automatique

---

<div align="center">

Fait avec ❤️ et [Mistral AI](https://mistral.ai) · [Signaler un bug](https://huggingface.co/spaces/<your-username>/recrutement-ia/discussions)

</div>
