import { useState, useRef, useEffect } from "react";
import * as XLSX from "xlsx";

// ─────────────────────────────────────────────────────────
// CONSTANTS
// ─────────────────────────────────────────────────────────
const STEPS = [
  { id: 1, label: "Identification",    icon: "📋" },
  { id: 2, label: "Parties",           icon: "🏛️" },
  { id: 3, label: "Calendrier",        icon: "📅" },
  { id: 4, label: "Financier",         icon: "💰" },
  { id: 5, label: "Avenants",          icon: "📝" },
  { id: 6, label: "Décomptes",         icon: "🧾" },
  { id: 7, label: "Suivi & Réception", icon: "✅" },
];

const EMPTY_FORM = {
  // Step 1
  numMarche: "", numMarcheEdited: false,
  numAO: "",     numAOEdited: false,
  objetMarche: "", typeMarche: "", modePassation: "", portee: "",
  // Step 2
  maitreOuvrage: "", organisme: "", maitreOeuvre: "",
  attributaire: "", qualiteAttributaire: "",
  // Step 3 — ORDER CORRIGÉ: lancement → ouverturePlis → notification → ordreService → delai → achevement → commissionOuverture → approbation → receptionProv → receptionDef → cautDef → mainlevee
  dateLancement: "",
  dateOuverturePlis: "",
  dateNotification: "",
  dateOrdreService: "",
  delaiExecution: "",
  dateAchevement: "",
  commissionOuverturePlis: "",   // NOUVEAU CHAMP
  dateApprobation: "",            // DÉPLACÉ APRÈS achèvement + commission
  dateReceptionProv: "",
  dateReceptionDef: "",
  dateConstitutionCautDef: "",
  dateMainlevee: "",
  // Step 4
  montantEstimatif: "", montantMarche: "",
  cautionnementProv: "", cautionnementDef: "",
  retenueGarantie: "", avanceForfaitaire: "",
  tauxPenalite: "1", seuilResiliation: "10",
  // Step 5
  avenants: [],
  // Step 6
  decomptes: [],
  // Step 7
  pvReceptionProv: "", pvReceptionDef: "",
  reservesALever: "", delaiGarantie: "12",
  statut: "", observations: "",
};

function fmt(d) {
  if (!d) return "—";
  const [y, m, day] = d.split("-");
  return `${day}/${m}/${y}`;
}
function money(v) {
  if (!v && v !== 0) return "—";
  return Number(v).toLocaleString("fr-MA") + " DH";
}
function daysBetween(a, b) {
  if (!a || !b) return null;
  return Math.round((new Date(b) - new Date(a)) / 86400000);
}

// ─────────────────────────────────────────────────────────
// LOCKED FIELD COMPONENT
// ─────────────────────────────────────────────────────────
function LockedField({ label, fieldKey, value, locked, onBlur, onChange, placeholder, error }) {
  const inputStyle = {
    width: "100%", background: locked ? "#0d1f3c" : "#0f2044",
    border: `1px solid ${error ? "#ef4444" : locked ? "#1e40af" : "#1e3a5f"}`,
    borderRadius: "10px", padding: "11px 14px", color: locked ? "#38bdf8" : "#e2e8f0",
    fontSize: "14px", outline: "none",
    fontFamily: "'IBM Plex Mono',monospace", boxSizing: "border-box",
    cursor: locked ? "not-allowed" : "text",
    paddingRight: locked ? "120px" : "14px",
  };
  return (
    <div>
      <label style={{ color: "#64748b", fontSize: "11px", textTransform: "uppercase", letterSpacing: "0.8px", marginBottom: "6px", display: "block" }}>{label} *</label>
      <div style={{ position: "relative" }}>
        <input
          value={value}
          onChange={e => !locked && onChange(fieldKey, e.target.value)}
          onBlur={() => !locked && value.trim() && onBlur(fieldKey)}
          readOnly={locked}
          placeholder={locked ? "" : placeholder}
          style={inputStyle}
        />
        {locked && (
          <div style={{ position: "absolute", right: "10px", top: "50%", transform: "translateY(-50%)", fontSize: "10px", color: "#ef4444", background: "rgba(239,68,68,0.08)", border: "1px solid rgba(239,68,68,0.2)", padding: "2px 8px", borderRadius: "20px", display: "flex", alignItems: "center", gap: "4px" }}>
            🔒 VERROUILLÉ
          </div>
        )}
      </div>
      {!locked && value.trim() && <div style={{ color: "#f59e0b", fontSize: "11px", marginTop: "4px" }}>⚠ Quittez le champ pour verrouiller définitivement</div>}
      {!locked && !value.trim() && <div style={{ color: "#475569", fontSize: "11px", marginTop: "4px" }}>Saisissez puis quittez le champ — verrouillage définitif</div>}
      {error && <div style={{ color: "#ef4444", fontSize: "11px", marginTop: "4px" }}>● {error}</div>}
    </div>
  );
}

// ─────────────────────────────────────────────────────────
// LOCK MODAL
// ─────────────────────────────────────────────────────────
function LockModal({ fieldLabel, value, onConfirm, onCancel }) {
  return (
    <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.75)", backdropFilter: "blur(6px)", zIndex: 3000, display: "flex", alignItems: "center", justifyContent: "center" }}>
      <div style={{ background: "#0a1628", border: "1px solid #d97706", borderRadius: "18px", padding: "36px", maxWidth: "420px", width: "90%", boxShadow: "0 20px 60px rgba(0,0,0,0.7)" }}>
        <div style={{ fontSize: "40px", textAlign: "center", marginBottom: "14px" }}>⚠️</div>
        <div style={{ fontFamily: "'Playfair Display',serif", color: "#fbbf24", fontSize: "18px", fontWeight: 700, textAlign: "center", marginBottom: "12px" }}>Action irréversible</div>
        <div style={{ background: "rgba(251,191,36,0.06)", border: "1px solid rgba(251,191,36,0.15)", borderRadius: "10px", padding: "14px", marginBottom: "18px", textAlign: "center" }}>
          <div style={{ color: "#64748b", fontSize: "11px", marginBottom: "4px" }}>{fieldLabel}</div>
          <div style={{ fontFamily: "'IBM Plex Mono',monospace", color: "#38bdf8", fontSize: "16px", fontWeight: 700 }}>{value}</div>
        </div>
        <div style={{ color: "#94a3b8", fontSize: "13px", textAlign: "center", lineHeight: "1.8", marginBottom: "22px" }}>
          Ce champ sera <strong style={{ color: "#ef4444" }}>définitivement verrouillé</strong>.<br />Aucune modification ne sera possible après confirmation.
        </div>
        <div style={{ display: "flex", gap: "12px" }}>
          <button onClick={onCancel} style={{ flex: 1, background: "#1e3a5f", border: "none", borderRadius: "10px", padding: "13px", color: "#94a3b8", cursor: "pointer", fontSize: "13px" }}>Annuler</button>
          <button onClick={onConfirm} style={{ flex: 1, background: "linear-gradient(135deg,#d97706,#f59e0b)", border: "none", borderRadius: "10px", padding: "13px", color: "white", cursor: "pointer", fontSize: "13px", fontWeight: 700 }}>✓ Confirmer le verrouillage</button>
        </div>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────
// SEARCH MODAL
// ─────────────────────────────────────────────────────────
function SearchModal({ marches, onClose, onView }) {
  const [q, setQ] = useState("");
  const [results, setResults] = useState([]);
  const [searched, setSearched] = useState(false);
  const ref = useRef();
  useEffect(() => { ref.current?.focus(); }, []);

  function doSearch() {
    const t = q.trim().toLowerCase();
    if (!t) return;
    setResults(marches.filter(m =>
      m.numMarche.toLowerCase().includes(t) ||
      m.numAO.toLowerCase().includes(t) ||
      m.objetMarche.toLowerCase().includes(t) ||
      m.attributaire.toLowerCase().includes(t) ||
      m.maitreOuvrage.toLowerCase().includes(t)
    ));
    setSearched(true);
  }

  const SC = { "En cours": "#f59e0b", "Clôturé": "#10b981", "Réceptionné": "#3b82f6", "Résilié": "#ef4444" };

  return (
    <div style={{ position: "fixed", inset: 0, background: "rgba(0,16,40,0.88)", backdropFilter: "blur(8px)", zIndex: 1000, display: "flex", alignItems: "center", justifyContent: "center", padding: "20px" }}>
      <div style={{ background: "#0a1628", border: "1px solid #1e3a5f", borderRadius: "20px", width: "100%", maxWidth: "700px", maxHeight: "90vh", overflow: "hidden", display: "flex", flexDirection: "column" }}>
        <div style={{ padding: "24px 28px 18px", borderBottom: "1px solid #1e3a5f", display: "flex", alignItems: "center", gap: "14px" }}>
          <div style={{ width: "42px", height: "42px", borderRadius: "11px", background: "linear-gradient(135deg,#1e40af,#0ea5e9)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "18px" }}>🔍</div>
          <div style={{ flex: 1 }}>
            <div style={{ color: "#e2e8f0", fontFamily: "'Playfair Display',serif", fontSize: "17px", fontWeight: 700 }}>Rechercher un Marché</div>
            <div style={{ color: "#64748b", fontSize: "12px" }}>N° Marché, N° AO, objet, attributaire, maître d'ouvrage</div>
          </div>
          <button onClick={onClose} style={{ background: "#1e3a5f", border: "none", color: "#94a3b8", width: "34px", height: "34px", borderRadius: "9px", cursor: "pointer", fontSize: "16px" }}>✕</button>
        </div>
        <div style={{ padding: "16px 28px", borderBottom: "1px solid #1e3a5f", display: "flex", gap: "10px" }}>
          <input ref={ref} value={q} onChange={e => setQ(e.target.value)} onKeyDown={e => e.key === "Enter" && doSearch()} placeholder="Tapez votre recherche..." style={{ flex: 1, background: "#0f2044", border: "1px solid #1e3a5f", borderRadius: "10px", padding: "10px 14px", color: "#e2e8f0", fontSize: "14px", fontFamily: "'IBM Plex Mono',monospace", outline: "none" }} />
          <button onClick={doSearch} style={{ background: "linear-gradient(135deg,#1e40af,#0ea5e9)", border: "none", borderRadius: "10px", padding: "10px 22px", color: "white", fontWeight: 600, cursor: "pointer", fontSize: "14px" }}>Chercher</button>
        </div>
        <div style={{ flex: 1, overflowY: "auto", padding: "16px 28px 24px" }}>
          {!searched && <div style={{ textAlign: "center", color: "#475569", padding: "36px 0", fontSize: "13px" }}>Entrez un terme de recherche</div>}
          {searched && results.length === 0 && <div style={{ textAlign: "center", color: "#ef4444", padding: "36px 0", fontSize: "13px", background: "rgba(239,68,68,0.05)", borderRadius: "10px", border: "1px solid rgba(239,68,68,0.15)" }}>❌ Aucun marché trouvé pour « {q} »</div>}
          {results.map(r => (
            <div key={r.id} onClick={() => { onView(r); onClose(); }}
              style={{ background: "#0f2044", border: "1px solid #1e3a5f", borderRadius: "12px", padding: "14px 18px", marginBottom: "10px", cursor: "pointer", transition: "all 0.2s" }}
              onMouseEnter={e => e.currentTarget.style.borderColor = "#3b82f6"}
              onMouseLeave={e => e.currentTarget.style.borderColor = "#1e3a5f"}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
                <div style={{ fontFamily: "'IBM Plex Mono',monospace", color: "#38bdf8", fontSize: "13px", fontWeight: 700 }}>{r.numMarche}</div>
                {r.statut && <div style={{ background: `${SC[r.statut] || "#64748b"}18`, border: `1px solid ${SC[r.statut] || "#64748b"}40`, color: SC[r.statut] || "#64748b", padding: "2px 9px", borderRadius: "20px", fontSize: "11px" }}>{r.statut}</div>}
              </div>
              <div style={{ color: "#e2e8f0", fontSize: "13px", marginBottom: "4px" }}>{r.objetMarche || "—"}</div>
              <div style={{ color: "#64748b", fontSize: "11px" }}>AO: {r.numAO || "—"} · {r.maitreOuvrage || "—"}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────
// DETAIL MODAL (avec boutons modifier pour champs vides)
// ─────────────────────────────────────────────────────────
function DetailModal({ marche: m, onClose, onUpdate }) {
  const SC = { "En cours": "#f59e0b", "Clôturé": "#10b981", "Réceptionné": "#3b82f6", "Résilié": "#ef4444" };
  const color = SC[m.statut] || "#64748b";

  const [editField, setEditField] = useState(null);
  const [editValue, setEditValue] = useState("");

  const retard = daysBetween(m.dateAchevement, m.dateReceptionProv);
  const retardPositif = retard !== null && retard > 0 ? retard : 0;
  const penalites = retardPositif && m.montantMarche && m.tauxPenalite
    ? (retardPositif * (Number(m.tauxPenalite) / 1000) * Number(m.montantMarche)).toFixed(2) : null;
  const seuilAlert = m.montantMarche && penalites
    ? (Number(penalites) / Number(m.montantMarche) * 100).toFixed(2) : null;
  const totalAvenants = m.avenants?.reduce((s, a) => s + Number(a.montant || 0), 0) || 0;
  const totalDecomptes = m.decomptes?.reduce((s, d) => s + Number(d.montant || 0), 0) || 0;
  const montantActualise = Number(m.montantMarche || 0) + totalAvenants;

  function openEdit(field, currentVal) {
    setEditField(field);
    setEditValue(currentVal || "");
  }
  function saveEdit() {
    if (!editField) return;
    onUpdate({ ...m, [editField]: editValue });
    setEditField(null);
  }

  // Rendu d'une ligne avec bouton "Compléter" si vide
  const Row = ({ label, value, rawKey, highlight, isDate }) => {
    const isEmpty = !value || value === "—";
    return (
      <div style={{ display: "flex", padding: "9px 18px", borderBottom: "1px solid rgba(30,58,95,0.4)", alignItems: "center" }}>
        <div style={{ color: "#475569", fontSize: "11px", width: "200px", flexShrink: 0, textTransform: "uppercase", letterSpacing: "0.5px" }}>{label}</div>
        <div style={{ color: highlight || "#e2e8f0", fontSize: "13px", flex: 1 }}>{value || "—"}</div>
        {isEmpty && rawKey && (
          <button onClick={() => openEdit(rawKey, "")}
            style={{ background: "rgba(14,165,233,0.12)", border: "1px solid rgba(14,165,233,0.3)", color: "#38bdf8", borderRadius: "7px", padding: "3px 10px", fontSize: "11px", cursor: "pointer", whiteSpace: "nowrap", marginLeft: "8px" }}>
            + Compléter
          </button>
        )}
      </div>
    );
  };

  const Section = ({ title, icon, children }) => (
    <div style={{ background: "#0f2044", borderRadius: "14px", border: "1px solid #1e3a5f", overflow: "hidden", marginBottom: "16px" }}>
      <div style={{ padding: "11px 18px", borderBottom: "1px solid #1e3a5f", display: "flex", alignItems: "center", gap: "8px", background: "rgba(30,64,175,0.1)" }}>
        <span>{icon}</span>
        <span style={{ color: "#93c5fd", fontSize: "11px", fontWeight: 700, textTransform: "uppercase", letterSpacing: "1px" }}>{title}</span>
      </div>
      {children}
    </div>
  );

  return (
    <div style={{ position: "fixed", inset: 0, background: "rgba(0,16,40,0.9)", backdropFilter: "blur(8px)", zIndex: 1000, display: "flex", alignItems: "center", justifyContent: "center", padding: "16px" }}>
      <div style={{ background: "#0a1628", border: "1px solid #1e3a5f", borderRadius: "20px", width: "100%", maxWidth: "860px", maxHeight: "94vh", overflow: "hidden", display: "flex", flexDirection: "column" }}>
        <div style={{ padding: "22px 28px", borderBottom: "1px solid #1e3a5f", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <div style={{ fontFamily: "'IBM Plex Mono',monospace", color: "#38bdf8", fontSize: "12px", letterSpacing: "1.5px", marginBottom: "4px" }}>
              {m.numMarche} {m.numAO ? `· AO: ${m.numAO}` : ""}
            </div>
            <div style={{ fontFamily: "'Playfair Display',serif", color: "#e2e8f0", fontSize: "19px", fontWeight: 700 }}>{m.objetMarche || "Détails du marché"}</div>
          </div>
          <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
            {m.statut && <div style={{ background: `${color}18`, border: `1px solid ${color}40`, color, padding: "4px 13px", borderRadius: "20px", fontSize: "12px", fontWeight: 600 }}>{m.statut}</div>}
            <button onClick={onClose} style={{ background: "#1e3a5f", border: "none", color: "#94a3b8", width: "34px", height: "34px", borderRadius: "9px", cursor: "pointer", fontSize: "16px" }}>✕</button>
          </div>
        </div>

        <div style={{ flex: 1, overflowY: "auto", padding: "22px 28px" }}>
          {/* BANDEAU INFO suivi */}
          <div style={{ background: "rgba(14,165,233,0.06)", border: "1px solid rgba(14,165,233,0.2)", borderRadius: "10px", padding: "10px 16px", marginBottom: "16px", fontSize: "12px", color: "#7dd3fc", display: "flex", alignItems: "center", gap: "8px" }}>
            <span>ℹ️</span>
            <span>Les champs non renseignés peuvent être complétés au fil de l'avancement du marché. Cliquez sur <strong>+ Compléter</strong> pour renseigner un champ vide.</span>
          </div>

          {seuilAlert && Number(seuilAlert) >= 8 && (
            <div style={{ background: "rgba(239,68,68,0.08)", border: "1px solid rgba(239,68,68,0.3)", borderRadius: "12px", padding: "14px 18px", marginBottom: "16px", display: "flex", gap: "12px", alignItems: "center" }}>
              <span style={{ fontSize: "20px" }}>🚨</span>
              <div>
                <div style={{ color: "#ef4444", fontWeight: 700, fontSize: "13px" }}>Alerte pénalités — {seuilAlert}% du montant marché</div>
                <div style={{ color: "#94a3b8", fontSize: "12px", marginTop: "2px" }}>Seuil résiliation : {m.seuilResiliation || 10}% — Pénalités cumulées : {money(penalites)}</div>
              </div>
            </div>
          )}

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
            <div>
              <Section title="Identification" icon="📋">
                <Row label="N° Marché" value={m.numMarche} />
                <Row label="N° AO" value={m.numAO} />
                <Row label="Objet" value={m.objetMarche} />
                <Row label="Type" value={m.typeMarche} rawKey="typeMarche" />
                <Row label="Mode passation" value={m.modePassation} rawKey="modePassation" />
                <Row label="Portée" value={m.portee} rawKey="portee" />
              </Section>
              <Section title="Parties" icon="🏛️">
                <Row label="Maître d'ouvrage" value={m.maitreOuvrage} rawKey="maitreOuvrage" />
                <Row label="Organisme" value={m.organisme} rawKey="organisme" />
                <Row label="Maître d'œuvre" value={m.maitreOeuvre} rawKey="maitreOeuvre" />
                <Row label="Attributaire" value={m.attributaire} rawKey="attributaire" />
                <Row label="Qualité" value={m.qualiteAttributaire} rawKey="qualiteAttributaire" />
              </Section>
            </div>
            <div>
              {/* CALENDRIER — ordre corrigé */}
              <Section title="Calendrier" icon="📅">
                <Row label="Date lancement" value={fmt(m.dateLancement)} rawKey="dateLancement" />
                <Row label="Ouverture des plis" value={fmt(m.dateOuverturePlis)} rawKey="dateOuverturePlis" />
                <Row label="Notification" value={fmt(m.dateNotification)} rawKey="dateNotification" />
                <Row label="Ordre de service" value={fmt(m.dateOrdreService)} rawKey="dateOrdreService" />
                <Row label="Délai exécution (j)" value={m.delaiExecution ? m.delaiExecution + " jours" : null} rawKey="delaiExecution" />
                <Row label="Date achèvement" value={fmt(m.dateAchevement)} rawKey="dateAchevement" />
                <Row label="Commission ouverture plis" value={m.commissionOuverturePlis} rawKey="commissionOuverturePlis" />
                <Row label="Date approbation" value={fmt(m.dateApprobation)} rawKey="dateApprobation" />
                <Row label="Réception provisoire" value={fmt(m.dateReceptionProv)} rawKey="dateReceptionProv" />
                <Row label="Réception définitive" value={fmt(m.dateReceptionDef)} rawKey="dateReceptionDef" />
                <Row label="Caution déf. constituée" value={fmt(m.dateConstitutionCautDef)} rawKey="dateConstitutionCautDef" />
                <Row label="Mainlevée" value={fmt(m.dateMainlevee)} rawKey="dateMainlevee" />
              </Section>
            </div>
          </div>

          <Section title="Situation Financière" icon="💰">
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr" }}>
              {[
                ["Montant estimatif", money(m.montan
