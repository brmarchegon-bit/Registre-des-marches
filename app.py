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
    penalites = retard_positif * (float(m.get('tauxPenalite', 1)) / 1000) * montant_marche if retard_positif and montant_marche else 0

    # Alerte pénalités
    if penalites and montant_marche:
        seuil_pct = (penalites / montant_marche) * 100
        if seuil_pct >= 8:
            st.error(f"🚨 **Alerte pénalités — {seuil_pct:.1f}% du montant marché** | Pénalités cumulées : {fmt_money(penalites)}")

    # Métriques
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Montant initial", fmt_money(montant_marche))
    col2.metric("Avenants cumulés", fmt_money(total_avenants))
    col3.metric("Montant actualisé", fmt_money(montant_actualise))
    col4.metric("Décomptes versés", fmt_money(total_decomptes))

    st.markdown("---")
    tabs_d = st.tabs(["📋 Identification", "🏛️ Parties", "📅 Calendrier", "💰 Financier", "📝 Avenants", "🧾 Décomptes", "✅ Suivi"])

    with tabs_d[0]:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**N° Marché :** `{m.get('numMarche', '—')}`")
            st.markdown(f"**N° AO :** `{m.get('numAO', '—') or '—'}`")
            st.markdown(f"**Type :** {m.get('typeMarche', '—') or '—'}")
        with col2:
            st.markdown(f"**Mode passation :** {m.get('modePassation', '—') or '—'}")
            st.markdown(f"**Portée :** {m.get('portee', '—') or '—'}")
        st.markdown(f"**Objet :** {m.get('objetMarche', '—')}")

    with tabs_d[1]:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Maître d'ouvrage :** {m.get('maitreOuvrage', '—') or '—'}")
            st.markdown(f"**Organisme :** {m.get('organisme', '—') or '—'}")
            st.markdown(f"**Maître d'œuvre :** {m.get('maitreOeuvre', '—') or '—'}")
        with col2:
            st.markdown(f"**Attributaire :** {m.get('attributaire', '—') or '—'}")
            st.markdown(f"**Qualité :** {m.get('qualiteAttributaire', '—') or '—'}")

    with tabs_d[2]:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Date lancement :** {fmt_date(m.get('dateLancement'))}")
            st.markdown(f"**Ouverture des plis :** {fmt_date(m.get('dateOuverturePlis'))}")
            st.markdown(f"**Notification :** {fmt_date(m.get('dateNotification'))}")
            st.markdown(f"**Ordre de service :** {fmt_date(m.get('dateOrdreService'))}")
            st.markdown(f"**Délai exécution :** {m.get('delaiExecution', '—') or '—'} jours")
            st.markdown(f"**Date achèvement :** {fmt_date(m.get('dateAchevement'))}")
        with col2:
            st.markdown(f"**Commission ouverture plis :** {m.get('commissionOuverturePlis', '—') or '—'}")
            st.markdown(f"**Date approbation :** {fmt_date(m.get('dateApprobation'))}")
            st.markdown(f"**Réception provisoire :** {fmt_date(m.get('dateReceptionProv'))}")
            st.markdown(f"**Réception définitive :** {fmt_date(m.get('dateReceptionDef'))}")
            st.markdown(f"**Caution déf. constituée :** {fmt_date(m.get('dateConstitutionCautDef'))}")
            st.markdown(f"**Mainlevée :** {fmt_date(m.get('dateMainlevee'))}")

    with tabs_d[3]:
        col1, col2, col3 = st.columns(3)
        col1.metric("Montant estimatif", fmt_money(m.get('montantEstimatif')))
        col2.metric("Montant initial", fmt_money(m.get('montantMarche')))
        col3.metric("Montant actualisé", fmt_money(montant_actualise))
        col1.metric("Cautionnement prov.", fmt_money(m.get('cautionnementProv')))
        col2.metric("Cautionnement déf.", fmt_money(m.get('cautionnementDef')))
        col3.metric("Retenue de garantie", fmt_money(m.get('retenueGarantie')))
        col1.metric("Avance forfaitaire", fmt_money(m.get('avanceForfaitaire')))
        col2.metric("Taux pénalité", f"{m.get('tauxPenalite', '—')}‰/j")
        col3.metric("Pénalités calculées", fmt_money(penalites) if penalites else "—")

    with tabs_d[4]:
        avs = m.get('avenants', [])
        if avs:
            df_av = pd.DataFrame(avs)
            df_av.columns = ["N°", "Date", "Montant (DH)", "Objet"]
            st.dataframe(df_av, use_container_width=True)
            st.info(f"Total avenants : **{fmt_money(total_avenants)}**")
        else:
            st.info("Aucun avenant pour ce marché")

    with tabs_d[5]:
        dcs = m.get('decomptes', [])
        if dcs:
            df_dc = pd.DataFrame(dcs)
            df_dc.columns = ["Type", "Date", "Montant (DH)"]
            st.dataframe(df_dc, use_container_width=True)
            st.info(f"Total décomptes : **{fmt_money(total_decomptes)}**")
        else:
            st.info("Aucun décompte pour ce marché")

    with tabs_d[6]:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**PV Réception prov. :** {m.get('pvReceptionProv', '—') or '—'}")
            st.markdown(f"**PV Réception déf. :** {m.get('pvReceptionDef', '—') or '—'}")
            st.markdown(f"**Délai garantie :** {m.get('delaiGarantie', '—')} mois")
        with col2:
            st.markdown(f"**Statut :** {statut_badge(m.get('statut'))}")
            st.markdown(f"**Réserves :** {m.get('reservesALever', '—') or '—'}")
            st.markdown(f"**Observations :** {m.get('observations', '—') or '—'}")

# ═══════════════════════════════════════════════════════════
# VUE: LISTE DES MARCHÉS
# ═══════════════════════════════════════════════════════════
else:
    marches = st.session_state.marches

    # ── RECHERCHE ──
    search_col, export_col = st.columns([3, 1])
    with search_col:
        search_q = st.text_input("🔍 Rechercher", placeholder="N° marché, objet, attributaire, maître d'ouvrage...", label_visibility="collapsed")
    with export_col:
        export_btn = st.button("📥 Export Excel", use_container_width=True, disabled=len(marches) == 0)

    # Export Excel
    if export_btn and marches:
        rows = []
        for m in marches:
            total_av = sum(float(a.get('montant', 0)) for a in m.get('avenants', []))
            total_dc = sum(float(d.get('montant', 0)) for d in m.get('decomptes', []))
            rows.append({
                "N° Marché": m.get('numMarche'),
                "N° AO": m.get('numAO'),
                "Objet": m.get('objetMarche'),
                "Type": m.get('typeMarche'),
                "Mode passation": m.get('modePassation'),
                "Portée": m.get('portee'),
                "Maître d'ouvrage": m.get('maitreOuvrage'),
                "Organisme": m.get('organisme'),
                "Maître d'œuvre": m.get('maitreOeuvre'),
                "Attributaire": m.get('attributaire'),
                "Qualité attributaire": m.get('qualiteAttributaire'),
                "Date lancement": m.get('dateLancement'),
                "Date ouverture plis": m.get('dateOuverturePlis'),
                "Date notification": m.get('dateNotification'),
                "Date ordre de service": m.get('dateOrdreService'),
                "Délai exécution (j)": m.get('delaiExecution'),
                "Date achèvement": m.get('dateAchevement'),
                "Commission ouverture plis": m.get('commissionOuverturePlis'),
                "Date approbation": m.get('dateApprobation'),
                "Date réception provisoire": m.get('dateReceptionProv'),
                "Date réception définitive": m.get('dateReceptionDef'),
                "Date constitution caution déf.": m.get('dateConstitutionCautDef'),
                "Date mainlevée": m.get('dateMainlevee'),
                "Montant estimatif (DH)": m.get('montantEstimatif'),
                "Montant marché (DH)": m.get('montantMarche'),
                "Cautionnement prov. (DH)": m.get('cautionnementProv'),
                "Cautionnement déf. (DH)": m.get('cautionnementDef'),
                "Retenue garantie (DH)": m.get('retenueGarantie'),
                "Avance forfaitaire (DH)": m.get('avanceForfaitaire'),
                "Taux pénalité (‰)": m.get('tauxPenalite'),
                "Seuil résiliation (%)": m.get('seuilResiliation'),
                "Nb avenants": len(m.get('avenants', [])),
                "Total avenants (DH)": total_av,
                "Nb décomptes": len(m.get('decomptes', [])),
                "Total décomptes (DH)": total_dc,
                "Statut": m.get('statut'),
                "PV réception prov.": m.get('pvReceptionProv'),
                "PV réception déf.": m.get('pvReceptionDef'),
                "Délai garantie (mois)": m.get('delaiGarantie'),
                "Observations": m.get('observations'),
            })
        df_export = pd.DataFrame(rows)
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            df_export.to_excel(writer, index=False, sheet_name="Marchés")
        buf.seek(0)
        st.download_button(
            label="⬇️ Télécharger Excel",
            data=buf,
            file_name=f"Marches_Publics_{date.today().isoformat()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    st.markdown("---")

    # ── FILTRES RAPIDES ──
    if marches:
        statuts_dispo = list(set(m.get('statut', '') for m in marches if m.get('statut')))
        filtre_statut = st.multiselect("Filtrer par statut", statuts_dispo, label_visibility="visible")

    # ── LISTE ──
    if not marches:
        st.markdown("""
        <div style='text-align:center; padding:60px 20px; color:#475569; background:#0f2044; border-radius:16px; border:1px dashed #1e3a5f'>
            <div style='font-size:48px; margin-bottom:16px'>📂</div>
            <div style='font-size:16px'>Aucun marché enregistré.</div>
            <div style='font-size:13px; margin-top:8px'>Cliquez sur <b style='color:#38bdf8'>➕ Nouveau marché</b> pour commencer.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Filtrage
        filtered = marches
        if search_q:
            q = search_q.lower()
            filtered = [m for m in filtered if
                q in (m.get('numMarche', '') or '').lower() or
                q in (m.get('numAO', '') or '').lower() or
                q in (m.get('objetMarche', '') or '').lower() or
                q in (m.get('attributaire', '') or '').lower() or
                q in (m.get('maitreOuvrage', '') or '').lower()
            ]
        if 'filtre_statut' in dir() and filtre_statut:
            filtered = [m for m in filtered if m.get('statut') in filtre_statut]

        if not filtered:
            st.warning(f"Aucun marché trouvé pour « {search_q} »")
        else:
            st.markdown(f"<small style='color:#475569'>{len(filtered)} marché(s) affiché(s)</small>", unsafe_allow_html=True)
            for m in filtered:
                total_av = sum(float(a.get('montant', 0)) for a in m.get('avenants', []))
                montant_marche = float(m.get('montantMarche', 0))
                c1, c2, c3 = st.columns([4, 2, 1])
                with c1:
                    st.markdown(f"""
                    <div style='background:#0f2044; border:1px solid #1e3a5f; border-radius:14px; padding:14px 18px; margin-bottom:6px'>
                        <div style='display:flex; align-items:center; gap:12px; margin-bottom:6px'>
                            <span style='font-family:monospace; color:#38bdf8; font-size:14px; font-weight:700'>{m.get('numMarche', '')}</span>
                            <span style='color:#475569; font-size:12px'>AO: {m.get('numAO', '') or '—'}</span>
                            <span style='color:#64748b; font-size:11px'>{statut_badge(m.get('statut', ''))}</span>
                        </div>
                        <div style='color:#e2e8f0; font-size:13px; margin-bottom:4px'>{m.get('objetMarche', '—')}</div>
                        <div style='color:#64748b; font-size:11px'>{m.get('attributaire', '') or '—'} · {m.get('maitreOuvrage', '') or '—'}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with c2:
                    st.markdown(f"""
                    <div style='text-align:right; padding-top:14px'>
                        <div style='font-family:monospace; color:#fbbf24; font-size:14px; font-weight:700'>{fmt_money(montant_marche) if montant_marche else '—'}</div>
                        {'<div style="color:#10b981; font-size:11px">+' + fmt_money(total_av) + ' (avenants)</div>' if total_av > 0 else ''}
                    </div>
                    """, unsafe_allow_html=True)
                with c3:
                    st.markdown("<div style='padding-top:18px'>", unsafe_allow_html=True)
                    if st.button("👁️ Détails", key=f"view_{m['id']}", use_container_width=True):
                        st.session_state.selected_marche = m
                        st.session_state.view = "detail"
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
