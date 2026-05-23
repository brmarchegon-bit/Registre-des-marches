import streamlit as st
import pandas as pd
from datetime import date, datetime
import io

# ─── CONFIG ───
st.set_page_config(
    page_title="Registre des Marchés Publics",
    page_icon="🏛️",
    layout="wide"
)

# ─── CSS ───
st.markdown("""
<style>
    .main { background-color: #060f1e; }
    .stApp { background-color: #060f1e; color: #e2e8f0; }
    .block-container { padding-top: 1rem; }
    h1, h2, h3 { color: #e2e8f0 !important; font-family: Georgia, serif; }
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stDateInput > div > div > input,
    .stSelectbox > div > div { background-color: #0f2044 !important; color: #e2e8f0 !important; border: 1px solid #1e3a5f !important; border-radius: 8px !important; }
    .stTextArea > div > div > textarea { background-color: #0f2044 !important; color: #e2e8f0 !important; border: 1px solid #1e3a5f !important; }
    .stButton > button { background: linear-gradient(135deg, #1e40af, #0ea5e9) !important; color: white !important; border: none !important; border-radius: 10px !important; font-weight: 600 !important; }
    .stButton > button:hover { opacity: 0.85 !important; }
    div[data-testid="metric-container"] { background-color: #0f2044; border: 1px solid #1e3a5f; border-radius: 12px; padding: 12px; }
    .stDataFrame { background-color: #0f2044; }
    label { color: #94a3b8 !important; font-size: 12px !important; text-transform: uppercase !important; letter-spacing: 0.5px !important; }
    .stTabs [data-baseweb="tab"] { background-color: #0f2044; color: #94a3b8; border-radius: 8px 8px 0 0; }
    .stTabs [aria-selected="true"] { background: linear-gradient(135deg, #1e40af, #0ea5e9) !important; color: white !important; }
    .stSuccess { background-color: rgba(16,185,129,0.1) !important; border: 1px solid rgba(16,185,129,0.3) !important; }
    .stWarning { background-color: rgba(251,191,36,0.1) !important; }
    .stError { background-color: rgba(239,68,68,0.1) !important; }
    .card { background: #0f2044; border: 1px solid #1e3a5f; border-radius: 14px; padding: 18px; margin-bottom: 12px; }
    .badge { display: inline-block; padding: 2px 10px; border-radius: 20px; font-size: 11px; font-weight: 600; }
    .badge-encours { background: rgba(245,158,11,0.15); color: #f59e0b; border: 1px solid rgba(245,158,11,0.3); }
    .badge-cloture { background: rgba(16,185,129,0.15); color: #10b981; border: 1px solid rgba(16,185,129,0.3); }
    .badge-receptionne { background: rgba(59,130,246,0.15); color: #3b82f6; border: 1px solid rgba(59,130,246,0.3); }
    .badge-resilie { background: rgba(239,68,68,0.15); color: #ef4444; border: 1px solid rgba(239,68,68,0.3); }
    .marche-card { background: #0f2044; border: 1px solid #1e3a5f; border-radius: 14px; padding: 16px 20px; margin-bottom: 10px; cursor: pointer; transition: border-color 0.2s; }
    .marche-card:hover { border-color: #3b82f6; }
    .num-marche { font-family: monospace; color: #38bdf8; font-size: 15px; font-weight: 700; }
    .montant { font-family: monospace; color: #fbbf24; font-size: 14px; font-weight: 700; }
    .separator { border: none; border-top: 1px solid #1e3a5f; margin: 16px 0; }
</style>
""", unsafe_allow_html=True)

# ─── SESSION STATE ───
if "marches" not in st.session_state:
    st.session_state.marches = []
if "view" not in st.session_state:
    st.session_state.view = "liste"
if "selected_marche" not in st.session_state:
    st.session_state.selected_marche = None

# ─── HELPERS ───
def fmt_date(d):
    if not d:
        return "—"
    if isinstance(d, str) and d:
        try:
            dt = datetime.strptime(d, "%Y-%m-%d")
            return dt.strftime("%d/%m/%Y")
        except:
            return d
    if hasattr(d, "strftime"):
        return d.strftime("%d/%m/%Y")
    return "—"

def fmt_money(v):
    if not v and v != 0:
        return "—"
    try:
        return f"{float(v):,.2f} DH".replace(",", " ")
    except:
        return "—"

def days_between(a, b):
    if not a or not b:
        return None
    try:
        if isinstance(a, str):
            a = datetime.strptime(a, "%Y-%m-%d").date()
        if isinstance(b, str):
            b = datetime.strptime(b, "%Y-%m-%d").date()
        return (b - a).days
    except:
        return None

def statut_badge(statut):
    colors = {
        "En cours": ("🟡", "#f59e0b"),
        "Clôturé": ("🟢", "#10b981"),
        "Réceptionné": ("🔵", "#3b82f6"),
        "Résilié": ("🔴", "#ef4444"),
    }
    icon, _ = colors.get(statut, ("⚪", "#64748b"))
    return f"{icon} {statut}" if statut else "—"

# ─── HEADER ───
col1, col2, col3 = st.columns([3, 1, 1])
with col1:
    st.markdown("## 🏛️ Registre des Marchés Publics")
    st.markdown("<small style='color:#475569'>Établissement Public — Gestion & Suivi</small>", unsafe_allow_html=True)
with col2:
    nb = len(st.session_state.marches)
    st.metric("Marchés enregistrés", nb)
with col3:
    if st.session_state.view == "liste":
        if st.button("➕ Nouveau marché", use_container_width=True):
            st.session_state.view = "formulaire"
            st.session_state.selected_marche = None
            st.rerun()
    else:
        if st.button("📋 Voir la liste", use_container_width=True):
            st.session_state.view = "liste"
            st.rerun()

st.markdown("<hr style='border:1px solid #1e3a5f;margin:8px 0 20px 0'>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# VUE: FORMULAIRE NOUVEAU MARCHÉ
# ═══════════════════════════════════════════════════════════
if st.session_state.view == "formulaire":
    st.markdown("### 📝 Enregistrement d'un nouveau marché")

    tabs = st.tabs([
        "📋 Identification",
        "🏛️ Parties",
        "📅 Calendrier",
        "💰 Financier",
        "📝 Avenants",
        "🧾 Décomptes",
        "✅ Suivi & Réception"
    ])

    # ── TAB 1: IDENTIFICATION ──
    with tabs[0]:
        st.markdown("#### Identification du marché")
        c1, c2 = st.columns(2)
        with c1:
            num_marche = st.text_input("N° Marché *", placeholder="Ex: 01/2024/EP", key="num_marche")
        with c2:
            num_ao = st.text_input("N° Appel d'Offres", placeholder="Ex: AO-14/2024", key="num_ao")
        objet = st.text_area("Objet du marché *", placeholder="Description complète de l'objet du marché", key="objet", height=100)
        c3, c4, c5 = st.columns(3)
        with c3:
            type_marche = st.selectbox("Type de marché", ["", "Travaux", "Fournitures", "Services", "Études"], key="type_marche")
        with c4:
            mode_passation = st.selectbox("Mode de passation", ["", "Appel d'offres ouvert", "Appel d'offres restreint", "Bon de commande", "Concours", "Gré à gré", "Marché négocié"], key="mode_passation")
        with c5:
            portee = st.selectbox("Portée", ["", "National", "International", "Régional"], key="portee")

    # ── TAB 2: PARTIES ──
    with tabs[1]:
        st.markdown("#### Parties contractantes")
        c1, c2 = st.columns(2)
        with c1:
            maitre_ouvrage = st.text_input("Maître d'ouvrage", placeholder="Nom de l'établissement", key="maitre_ouvrage")
            maitre_oeuvre = st.text_input("Maître d'œuvre", placeholder="Bureau d'études ou ingénieur", key="maitre_oeuvre")
            qualite_attributaire = st.selectbox("Qualité de l'attributaire", ["", "Entreprise nationale", "Entreprise étrangère", "Groupement d'entreprises", "Personne physique"], key="qualite_attributaire")
        with c2:
            organisme = st.text_input("Organisme / Division", placeholder="Direction concernée", key="organisme")
            attributaire = st.text_input("Attributaire", placeholder="Nom de l'entreprise titulaire", key="attributaire")

    # ── TAB 3: CALENDRIER ──
    with tabs[2]:
        st.markdown("#### Calendrier du marché")
        st.info("📌 Ordre conforme aux décrets : Lancement → Ouverture des plis → Notification → OS → Achèvement → Commission → Approbation → Réception prov. → Réception déf.")
        c1, c2 = st.columns(2)
        with c1:
            date_lancement = st.date_input("Date de lancement", value=None, key="date_lancement")
            date_notification = st.date_input("Date de notification", value=None, key="date_notification")
            delai_execution = st.number_input("Délai d'exécution (jours)", min_value=0, value=0, key="delai_execution")
            commission_ouverture = st.text_input("Commission d'ouverture des plis (membres / N° PV)", key="commission_ouverture")
            date_reception_prov = st.date_input("Date réception provisoire", value=None, key="date_reception_prov")
            date_constitution_caut = st.date_input("Date constitution caution déf.", value=None, key="date_constitution_caut")
        with c2:
            date_ouverture_plis = st.date_input("Date d'ouverture des plis", value=None, key="date_ouverture_plis")
            date_ordre_service = st.date_input("Date ordre de service", value=None, key="date_ordre_service")
            date_achevement = st.date_input("Date d'achèvement", value=None, key="date_achevement")
            date_approbation = st.date_input("Date d'approbation", value=None, key="date_approbation")
            date_reception_def = st.date_input("Date réception définitive", value=None, key="date_reception_def")
            date_mainlevee = st.date_input("Date mainlevée", value=None, key="date_mainlevee")

    # ── TAB 4: FINANCIER ──
    with tabs[3]:
        st.markdown("#### Situation financière")
        c1, c2 = st.columns(2)
        with c1:
            montant_estimatif = st.number_input("Montant estimatif (DH)", min_value=0.0, value=0.0, format="%.2f", key="montant_estimatif")
            cautionnement_prov = st.number_input("Cautionnement provisoire (DH)", min_value=0.0, value=0.0, format="%.2f", key="cautionnement_prov")
            retenue_garantie = st.number_input("Retenue de garantie (DH)", min_value=0.0, value=0.0, format="%.2f", key="retenue_garantie")
            taux_penalite = st.number_input("Taux de pénalité (‰/jour)", min_value=0.0, value=1.0, format="%.2f", key="taux_penalite")
        with c2:
            montant_marche = st.number_input("Montant du marché (DH)", min_value=0.0, value=0.0, format="%.2f", key="montant_marche")
            cautionnement_def = st.number_input("Cautionnement définitif (DH)", min_value=0.0, value=0.0, format="%.2f", key="cautionnement_def")
            avance_forfaitaire = st.number_input("Avance forfaitaire (DH)", min_value=0.0, value=0.0, format="%.2f", key="avance_forfaitaire")
            seuil_resiliation = st.number_input("Seuil de résiliation (%)", min_value=0.0, value=10.0, format="%.1f", key="seuil_resiliation")

    # ── TAB 5: AVENANTS ──
    with tabs[4]:
        st.markdown("#### Avenants")
        if "avenants_temp" not in st.session_state:
            st.session_state.avenants_temp = []

        with st.expander("➕ Ajouter un avenant", expanded=True):
            ca1, ca2, ca3, ca4 = st.columns([1, 2, 2, 3])
            with ca1:
                av_num = st.text_input("N°", key="av_num")
            with ca2:
                av_date = st.date_input("Date", value=None, key="av_date")
            with ca3:
                av_montant = st.number_input("Montant (DH)", min_value=0.0, value=0.0, format="%.2f", key="av_montant")
            with ca4:
                av_objet = st.text_input("Objet", key="av_objet")
            if st.button("✚ Ajouter l'avenant"):
                if av_montant > 0 or av_objet:
                    st.session_state.avenants_temp.append({
                        "numero": av_num, "date": str(av_date) if av_date else "",
                        "montant": av_montant, "objet": av_objet
                    })
                    st.success("Avenant ajouté !")
                    st.rerun()

        if st.session_state.avenants_temp:
            st.markdown("**Avenants saisis :**")
            for i, av in enumerate(st.session_state.avenants_temp):
                col_a, col_b, col_c, col_d, col_e = st.columns([1, 2, 2, 3, 1])
                col_a.write(f"Av.{av['numero'] or i+1}")
                col_b.write(fmt_date(av['date']))
                col_c.write(fmt_money(av['montant']))
                col_d.write(av['objet'] or "—")
                if col_e.button("✕", key=f"del_av_{i}"):
                    st.session_state.avenants_temp.pop(i)
                    st.rerun()
        else:
            st.info("Aucun avenant pour ce marché")

    # ── TAB 6: DÉCOMPTES ──
    with tabs[5]:
        st.markdown("#### Décomptes")
        if "decomptes_temp" not in st.session_state:
            st.session_state.decomptes_temp = []

        with st.expander("➕ Ajouter un décompte", expanded=True):
            cd1, cd2, cd3 = st.columns([2, 2, 2])
            with cd1:
                dc_type = st.selectbox("Type", ["Provisoire", "Définitif"], key="dc_type")
            with cd2:
                dc_date = st.date_input("Date", value=None, key="dc_date")
            with cd3:
                dc_montant = st.number_input("Montant (DH)", min_value=0.0, value=0.0, format="%.2f", key="dc_montant")
            if st.button("✚ Ajouter le décompte"):
                if dc_montant > 0:
                    st.session_state.decomptes_temp.append({
                        "type": dc_type, "date": str(dc_date) if dc_date else "",
                        "montant": dc_montant
                    })
                    st.success("Décompte ajouté !")
                    st.rerun()

        if st.session_state.decomptes_temp:
            st.markdown("**Décomptes saisis :**")
            for i, dc in enumerate(st.session_state.decomptes_temp):
                col_a, col_b, col_c, col_d = st.columns([2, 2, 2, 1])
                col_a.write(f"{'DGD' if dc['type'] == 'Définitif' else f'D.Prov. N°{i+1}'}")
                col_b.write(fmt_date(dc['date']))
                col_c.write(fmt_money(dc['montant']))
                if col_d.button("✕", key=f"del_dc_{i}"):
                    st.session_state.decomptes_temp.pop(i)
                    st.rerun()
        else:
            st.info("Aucun décompte pour ce marché")

    # ── TAB 7: SUIVI ──
    with tabs[6]:
        st.markdown("#### Suivi & Réception")
        c1, c2 = st.columns(2)
        with c1:
            pv_reception_prov = st.text_input("N° PV Réception provisoire", placeholder="Ex: PV-001/2024", key="pv_reception_prov")
            reserves = st.text_area("Réserves à lever", key="reserves", height=100)
            statut = st.selectbox("Statut du marché", ["", "En cours", "Clôturé", "Réceptionné", "Résilié"], key="statut")
        with c2:
            pv_reception_def = st.text_input("N° PV Réception définitive", placeholder="Ex: PV-002/2024", key="pv_reception_def")
            delai_garantie = st.number_input("Délai de garantie (mois)", min_value=0, value=12, key="delai_garantie")
            observations = st.text_area("Observations", key="observations", height=100)

    # ── BOUTON ENREGISTRER ──
    st.markdown("---")
    col_save1, col_save2, col_save3 = st.columns([2, 1, 2])
    with col_save2:
        if st.button("✅ Enregistrer le marché", use_container_width=True, type="primary"):
            if not st.session_state.get("num_marche"):
                st.error("⚠️ Le numéro de marché est obligatoire !")
            elif not st.session_state.get("objet"):
                st.error("⚠️ L'objet du marché est obligatoire !")
            else:
                def to_str(d):
                    return str(d) if d else ""

                new_marche = {
                    "id": int(datetime.now().timestamp() * 1000),
                    "numMarche": st.session_state.num_marche,
                    "numAO": st.session_state.num_ao,
                    "objetMarche": st.session_state.objet,
                    "typeMarche": st.session_state.type_marche,
                    "modePassation": st.session_state.mode_passation,
                    "portee": st.session_state.portee,
                    "maitreOuvrage": st.session_state.maitre_ouvrage,
                    "organisme": st.session_state.organisme,
                    "maitreOeuvre": st.session_state.maitre_oeuvre,
                    "attributaire": st.session_state.attributaire,
                    "qualiteAttributaire": st.session_state.qualite_attributaire,
                    "dateLancement": to_str(st.session_state.date_lancement),
                    "dateOuverturePlis": to_str(st.session_state.date_ouverture_plis),
                    "dateNotification": to_str(st.session_state.date_notification),
                    "dateOrdreService": to_str(st.session_state.date_ordre_service),
                    "delaiExecution": st.session_state.delai_execution,
                    "dateAchevement": to_str(st.session_state.date_achevement),
                    "commissionOuverturePlis": st.session_state.commission_ouverture,
                    "dateApprobation": to_str(st.session_state.date_approbation),
                    "dateReceptionProv": to_str(st.session_state.date_reception_prov),
                    "dateReceptionDef": to_str(st.session_state.date_reception_def),
                    "dateConstitutionCautDef": to_str(st.session_state.date_constitution_caut),
                    "dateMainlevee": to_str(st.session_state.date_mainlevee),
                    "montantEstimatif": st.session_state.montant_estimatif,
                    "montantMarche": st.session_state.montant_marche,
                    "cautionnementProv": st.session_state.cautionnement_prov,
                    "cautionnementDef": st.session_state.cautionnement_def,
                    "retenueGarantie": st.session_state.retenue_garantie,
                    "avanceForfaitaire": st.session_state.avance_forfaitaire,
                    "tauxPenalite": st.session_state.taux_penalite,
                    "seuilResiliation": st.session_state.seuil_resiliation,
                    "avenants": list(st.session_state.avenants_temp),
                    "decomptes": list(st.session_state.decomptes_temp),
                    "pvReceptionProv": st.session_state.pv_reception_prov,
                    "pvReceptionDef": st.session_state.pv_reception_def,
                    "reservesALever": st.session_state.reserves,
                    "delaiGarantie": st.session_state.delai_garantie,
                    "statut": st.session_state.statut,
                    "observations": st.session_state.observations,
                }
                st.session_state.marches.append(new_marche)
                st.session_state.avenants_temp = []
                st.session_state.decomptes_temp = []
                st.session_state.view = "liste"
                st.success("✅ Marché enregistré avec succès !")
                st.rerun()

# ═══════════════════════════════════════════════════════════
# VUE: DÉTAIL D'UN MARCHÉ
# ═══════════════════════════════════════════════════════════
elif st.session_state.view == "detail":
    m = st.session_state.selected_marche
    if not m:
        st.session_state.view = "liste"
        st.rerun()

    if st.button("← Retour à la liste"):
        st.session_state.view = "liste"
        st.session_state.selected_marche = None
        st.rerun()

    st.markdown(f"### 🏛️ {m.get('numMarche', '')} — {m.get('objetMarche', '')}")
    if m.get('statut'):
        st.markdown(f"**Statut :** {statut_badge(m.get('statut'))}")

    # Calculs
    total_avenants = sum(float(a.get('montant', 0)) for a in m.get('avenants', []))
    total_decomptes = sum(float(d.get('montant', 0)) for d in m.get('decomptes', []))
    montant_marche = float(m.get('montantMarche', 0))
    montant_actualise = montant_marche + total_avenants
    retard = days_between(m.get('dateAchevement'), m.get('dateReceptionProv'))
    retard_positif = max(0, retard) if retard else 0
    penalites = retard_positif * (float(m.get('tauxPenalite', 1)) / 1000) * montant_marche i
