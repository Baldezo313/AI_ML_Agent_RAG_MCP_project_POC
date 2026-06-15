import os
import json
import gradio as gr
from mistralai.client import Mistral
from agents import DocumentAgent, JobAnalysisAgent, ResumeAnalysisAgent, MatchingAgent

# ──────────────────────────────────────────────
# Core pipeline
# ──────────────────────────────────────────────

def score_color(score: float) -> str:
    if score >= 75:
        return "#22c55e"   # green
    elif score >= 50:
        return "#f59e0b"   # amber
    else:
        return "#ef4444"   # red


def score_label(score: float) -> str:
    if score >= 75:
        return "✅ Excellent match"
    elif score >= 50:
        return "⚠️ Partial match"
    else:
        return "❌ Weak match"


def build_candidate_card(name: str, score_data: dict) -> str:
    total = score_data.get("total_score", 0)
    color = score_color(total)
    label = score_label(total)
    strengths = score_data.get("key_strengths", [])
    gaps = score_data.get("key_gaps", [])
    notes = score_data.get("notes", "")
    confidence = score_data.get("confidence", 0)

    tech = score_data.get("technical_skills_score", 0)
    exp  = score_data.get("experience_score", 0)
    edu  = score_data.get("education_score", 0)
    add  = score_data.get("additional_score", 0)

    def mini_bar(val, max_val, color_hex):
        pct = round(val / max_val * 100)
        return (
            f'<div style="display:flex;align-items:center;gap:8px;margin:4px 0">'
            f'<div style="width:120px;background:#1e293b;border-radius:4px;height:8px">'
            f'<div style="width:{pct}%;background:{color_hex};border-radius:4px;height:8px"></div></div>'
            f'<span style="font-size:12px;color:#94a3b8">{val:.1f}</span></div>'
        )

    strengths_html = "".join(f'<li>{s}</li>' for s in strengths) or "<li>—</li>"
    gaps_html      = "".join(f'<li>{g}</li>' for g in gaps)      or "<li>—</li>"

    return f"""
<div style="
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
  border: 1px solid {color}44;
  border-radius: 16px;
  padding: 24px;
  margin: 12px 0;
  font-family: 'Inter', sans-serif;
  box-shadow: 0 4px 24px {color}22;
">
  <!-- Header -->
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
    <div>
      <div style="font-size:18px;font-weight:700;color:#f1f5f9">{name}</div>
      <div style="font-size:12px;color:#64748b;margin-top:2px">Confiance : {confidence*100:.0f}%</div>
    </div>
    <div style="text-align:right">
      <div style="font-size:42px;font-weight:800;color:{color};line-height:1">{total:.0f}</div>
      <div style="font-size:11px;color:#64748b">/100</div>
    </div>
  </div>

  <!-- Score bar -->
  <div style="background:#1e293b;border-radius:8px;height:12px;margin-bottom:8px">
    <div style="width:{total}%;background:linear-gradient(90deg,{color}88,{color});border-radius:8px;height:12px;transition:width 0.8s ease"></div>
  </div>
  <div style="font-size:13px;color:{color};font-weight:600;margin-bottom:20px">{label}</div>

  <!-- Sub-scores -->
  <div style="margin-bottom:16px">
    <div style="font-size:11px;text-transform:uppercase;letter-spacing:1px;color:#475569;margin-bottom:8px">Détail des scores</div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:4px">
      <div><span style="font-size:12px;color:#94a3b8">🛠 Compétences /40</span>{mini_bar(tech, 40, "#6366f1")}</div>
      <div><span style="font-size:12px;color:#94a3b8">💼 Expérience /30</span>{mini_bar(exp, 30, "#8b5cf6")}</div>
      <div><span style="font-size:12px;color:#94a3b8">🎓 Formation /15</span>{mini_bar(edu, 15, "#a78bfa")}</div>
      <div><span style="font-size:12px;color:#94a3b8">⭐ Bonus /15</span>{mini_bar(add, 15, "#c4b5fd")}</div>
    </div>
  </div>

  <!-- Strengths & Gaps -->
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:16px">
    <div style="background:#f0fdf4;border-left:4px solid #16a34a;border-radius:10px;padding:14px">
      <div style="font-size:11px;text-transform:uppercase;letter-spacing:1px;color:#15803d;font-weight:700;margin-bottom:10px">✅ Points forts</div>
      <ul style="margin:0;padding-left:18px;color:#14532d;font-size:13px;line-height:2">{strengths_html}</ul>
    </div>
    <div style="background:#fff1f2;border-left:4px solid #dc2626;border-radius:10px;padding:14px">
      <div style="font-size:11px;text-transform:uppercase;letter-spacing:1px;color:#b91c1c;font-weight:700;margin-bottom:10px">❌ Lacunes</div>
      <ul style="margin:0;padding-left:18px;color:#7f1d1d;font-size:13px;line-height:2">{gaps_html}</ul>
    </div>
  </div>

  <!-- Notes -->
  {f'<div style="background:#1e293b;border-left:3px solid #6366f1;border-radius:6px;padding:12px 16px;font-size:13px;color:#cbd5e1;line-height:1.7">{notes}</div>' if notes else ''}
</div>
"""


def run_pipeline(resume_files, job_pdf, job_text: str) -> str:
    # ── Clé API depuis variable d'environnement ──
    api_key = os.environ.get("MISTRAL_API_KEY", "")
    if not api_key:
        return _error_card(
            "Clé API manquante",
            "La variable d'environnement <code>MISTRAL_API_KEY</code> n'est pas définie dans les secrets du Space."
        )

    has_pdfs   = resume_files and len(resume_files) > 0
    has_job_pdf  = job_pdf is not None
    has_job_text = job_text and job_text.strip()

    if not has_pdfs:
        return _error_card("Aucun CV fourni", "Uploadez au moins un CV en PDF.")
    if not has_job_pdf and not has_job_text:
        return _error_card("Offre manquante", "Uploadez un PDF ou collez le texte de l'offre d'emploi.")

    try:
        client = Mistral(api_key=api_key.strip())
        doc_agent    = DocumentAgent(client)
        job_agent    = JobAnalysisAgent(client)
        resume_agent = ResumeAnalysisAgent(client)
        match_agent  = MatchingAgent(client)

        # ── Job description ──────────────────────
        if has_job_text:
            jd_text = job_text.strip()
        else:
            jd_text = doc_agent.extract_text(job_pdf, os.path.basename(job_pdf))
            if jd_text.startswith("[OCR error"):
                return _error_card("Erreur OCR (offre)", jd_text)

        job_requirements = job_agent.extract_requirements(jd_text)

        # ── Process each CV ──────────────────────
        cards_html = []
        scores_for_ranking = []

        for resume_path in resume_files:
            file_name = os.path.basename(resume_path)
            resume_text = doc_agent.extract_text(resume_path, file_name)

            if resume_text.startswith("[OCR error"):
                cards_html.append(_error_card(f"Erreur OCR ({file_name})", resume_text))
                continue

            candidate_profile = resume_agent.extract_profile(resume_text)
            score_data        = match_agent.evaluate(job_requirements, candidate_profile)

            name = candidate_profile.get("contact_details", {}).get("name", file_name)
            cards_html.append((score_data.get("total_score", 0), name, build_candidate_card(name, score_data)))
            scores_for_ranking.append((score_data.get("total_score", 0), name))

        # ── Sort by score descending ──────────────
        cards_html.sort(key=lambda x: x[0] if isinstance(x, tuple) else -1, reverse=True)

        ranking_rows = ""
        for i, (sc, nm) in enumerate(sorted(scores_for_ranking, reverse=True), 1):
            medal = ["🥇", "🥈", "🥉"][i - 1] if i <= 3 else f"#{i}"
            color = score_color(sc)
            ranking_rows += (
                f'<tr>'
                f'<td style="padding:8px 12px;color:#94a3b8">{medal}</td>'
                f'<td style="padding:8px 12px;color:#f1f5f9;font-weight:500">{nm}</td>'
                f'<td style="padding:8px 12px;color:{color};font-weight:700">{sc:.0f}/100</td>'
                f'<td style="padding:8px 12px;color:{color};font-size:12px">{score_label(sc)}</td>'
                f'</tr>'
            )

        ranking_html = f"""
<div style="
  background:#0f172a;border:1px solid #1e293b;border-radius:14px;
  padding:20px;margin-bottom:24px;font-family:'Inter',sans-serif
">
  <div style="font-size:14px;font-weight:700;color:#a5b4fc;text-transform:uppercase;
              letter-spacing:1px;margin-bottom:14px">🏆 Classement des candidats</div>
  <table style="width:100%;border-collapse:collapse">
    <thead>
      <tr style="border-bottom:1px solid #1e293b">
        <th style="padding:6px 12px;text-align:left;font-size:11px;color:#475569">Rang</th>
        <th style="padding:6px 12px;text-align:left;font-size:11px;color:#475569">Candidat</th>
        <th style="padding:6px 12px;text-align:left;font-size:11px;color:#475569">Score</th>
        <th style="padding:6px 12px;text-align:left;font-size:11px;color:#475569">Résultat</th>
      </tr>
    </thead>
    <tbody>{ranking_rows}</tbody>
  </table>
</div>
"""

        individual_cards = "\n".join(c for _, __, c in cards_html)
        return ranking_html + individual_cards

    except Exception as e:
        return _error_card("Erreur inattendue", str(e))


def _error_card(title: str, message: str) -> str:
    return f"""
<div style="
  background:#450a0a;border:1px solid #ef4444;border-radius:12px;
  padding:20px;font-family:'Inter',sans-serif
">
  <div style="font-size:16px;font-weight:700;color:#fca5a5;margin-bottom:8px">⚠️ {title}</div>
  <div style="font-size:13px;color:#fecaca">{message}</div>
</div>
"""


# ──────────────────────────────────────────────
# Gradio UI
# ──────────────────────────────────────────────

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Syne:wght@700;800&display=swap');

body, .gradio-container {
    background: #020617 !important;
    font-family: 'Inter', sans-serif !important;
}

/* Hero */
.hero-title {
    font-family: 'Syne', sans-serif;
    font-size: 2.4rem;
    font-weight: 800;
    background: linear-gradient(135deg, #818cf8, #c084fc, #38bdf8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-align: center;
    margin-bottom: 0.25rem;
}
.hero-sub {
    text-align: center;
    color: #64748b;
    font-size: 0.95rem;
    margin-bottom: 2rem;
}

/* Panels */
.panel-box {
    background: #0f172a !important;
    border: 1px solid #1e293b !important;
    border-radius: 14px !important;
    padding: 20px !important;
}

/* Labels */
label span {
    color: #94a3b8 !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.8px !important;
}

/* Inputs */
input[type="password"], textarea {
    background: #1e293b !important;
    border: 1px solid #334155 !important;
    color: #f1f5f9 !important;
    border-radius: 8px !important;
}
input[type="password"]:focus, textarea:focus {
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 2px #6366f144 !important;
}

/* Upload zone */
.upload-box {
    border: 2px dashed #334155 !important;
    background: #0f172a !important;
    border-radius: 12px !important;
    transition: border-color 0.2s;
}
.upload-box:hover {
    border-color: #6366f1 !important;
}

/* Button */
.run-btn {
    background: linear-gradient(135deg, #4f46e5, #7c3aed) !important;
    border: none !important;
    color: white !important;
    font-weight: 600 !important;
    font-size: 15px !important;
    padding: 14px 0 !important;
    border-radius: 10px !important;
    width: 100% !important;
    cursor: pointer !important;
    transition: opacity 0.2s;
}
.run-btn:hover { opacity: 0.9; }

/* Tab pill style */
.tab-nav button {
    background: transparent !important;
    color: #64748b !important;
    border: none !important;
    font-size: 13px !important;
    padding: 6px 16px !important;
}
.tab-nav button.selected {
    background: #1e293b !important;
    color: #a5b4fc !important;
    border-radius: 8px !important;
}

/* Result area */
.result-area {
    background: transparent !important;
    border: none !important;
}
"""

HEADER = """
<div class="hero-title">🤖 Recrutement IA</div>
<div class="hero-sub">Analysez et classez vos candidats avec l'IA — multi-CV en un clic</div>
"""

STEPS_HTML = """
<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:0 0 8px 0">
  <div style="background:#0f172a;border:1px solid #1e293b;border-radius:10px;padding:12px;text-align:center">
    <div style="font-size:20px">📄</div>
    <div style="font-size:11px;font-weight:700;color:#818cf8;margin:4px 0">1. OCR</div>
    <div style="font-size:11px;color:#475569">Extraction texte PDF</div>
  </div>
  <div style="background:#0f172a;border:1px solid #1e293b;border-radius:10px;padding:12px;text-align:center">
    <div style="font-size:20px">🔍</div>
    <div style="font-size:11px;font-weight:700;color:#818cf8;margin:4px 0">2. Analyse offre</div>
    <div style="font-size:11px;color:#475569">Exigences structurées</div>
  </div>
  <div style="background:#0f172a;border:1px solid #1e293b;border-radius:10px;padding:12px;text-align:center">
    <div style="font-size:20px">👤</div>
    <div style="font-size:11px;font-weight:700;color:#818cf8;margin:4px 0">3. Profil candidat</div>
    <div style="font-size:11px;color:#475569">Extraction CV</div>
  </div>
  <div style="background:#0f172a;border:1px solid #1e293b;border-radius:10px;padding:12px;text-align:center">
    <div style="font-size:20px">🏆</div>
    <div style="font-size:11px;font-weight:700;color:#818cf8;margin:4px 0">4. Matching</div>
    <div style="font-size:11px;color:#475569">Score & classement</div>
  </div>
</div>
"""

with gr.Blocks(css=CSS, title="Recrutement IA") as demo:
    gr.HTML(HEADER)
    gr.HTML(STEPS_HTML)

    with gr.Row():
        # ── Left column: inputs ───────────────────────
        with gr.Column(scale=1, elem_classes=["panel-box"]):
            gr.Markdown("### 📋 Offre d'emploi")
            with gr.Tabs(elem_classes=["tab-nav"]):
                with gr.Tab("📎 Upload PDF"):
                    job_pdf = gr.File(
                        label="Offre en PDF",
                        file_types=[".pdf"],
                        elem_classes=["upload-box"],
                    )
                with gr.Tab("✏️ Coller le texte"):
                    job_text = gr.Textbox(
                        label="Texte de l'offre",
                        placeholder="Copiez-collez la description du poste ici…",
                        lines=10,
                    )

            gr.Markdown("### 📁 CV des candidats")
            resume_files = gr.File(
                label="CVs en PDF (1 à N fichiers)",
                file_types=[".pdf"],
                file_count="multiple",
                elem_classes=["upload-box"],
            )

            run_btn = gr.Button("🚀 Analyser les candidats", elem_classes=["run-btn"])

        # ── Right column: results ─────────────────────
        with gr.Column(scale=2):
            gr.Markdown("### 📊 Résultats")
            output = gr.HTML(
                value='<div style="color:#334155;text-align:center;padding:60px 0;font-size:14px">'
                      '⬅️ Renseignez les informations et cliquez sur <strong style="color:#6366f1">Analyser</strong></div>',
                elem_classes=["result-area"],
            )

    run_btn.click(
        fn=run_pipeline,
        inputs=[resume_files, job_pdf, job_text],
        outputs=output,
    )

if __name__ == "__main__":
    demo.launch()