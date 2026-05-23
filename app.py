from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import date
import json, os

app = FastAPI(
    title="Registre des Marchés Publics",
    description="API de gestion des marchés publics d'un établissement public",
    version="1.0.0"
)

# ─── CORS (autorise le frontend React) ───
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── STOCKAGE SIMPLE JSON ───
DB_FILE = "marches.json"

def load_db():
    if not os.path.exists(DB_FILE):
        return []
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ─── MODÈLES ───
class Avenant(BaseModel):
    numero: Optional[str] = ""
    date: Optional[str] = ""
    montant: Optional[float] = 0
    objet: Optional[str] = ""

class Decompte(BaseModel):
    type: Optional[str] = "Provisoire"
    date: Optional[str] = ""
    montant: Optional[float] = 0

class Marche(BaseModel):
    # Identification
    numMarche: str
    numAO: Optional[str] = ""
    objetMarche: str
    typeMarche: Optional[str] = ""
    modePassation: Optional[str] = ""
    portee: Optional[str] = ""
    # Parties
    maitreOuvrage: Optional[str] = ""
    organisme: Optional[str] = ""
    maitreOeuvre: Optional[str] = ""
    attributaire: Optional[str] = ""
    qualiteAttributaire: Optional[str] = ""
    # Calendrier (ordre décrets)
    dateLancement: Optional[str] = ""
    dateOuverturePlis: Optional[str] = ""
    dateNotification: Optional[str] = ""
    dateOrdreService: Optional[str] = ""
    delaiExecution: Optional[str] = ""
    dateAchevement: Optional[str] = ""
    commissionOuverturePlis: Optional[str] = ""   # Commission ouverture des plis
    dateApprobation: Optional[str] = ""            # Après achèvement + commission
    dateReceptionProv: Optional[str] = ""
    dateReceptionDef: Optional[str] = ""
    dateConstitutionCautDef: Optional[str] = ""
    dateMainlevee: Optional[str] = ""
    # Financier
    montantEstimatif: Optional[float] = None
    montantMarche: Optional[float] = None
    cautionnementProv: Optional[float] = None
    cautionnementDef: Optional[float] = None
    retenueGarantie: Optional[float] = None
    avanceForfaitaire: Optional[float] = None
    tauxPenalite: Optional[float] = 1
    seuilResiliation: Optional[float] = 10
    # Avenants & Décomptes
    avenants: Optional[List[Avenant]] = []
    decomptes: Optional[List[Decompte]] = []
    # Suivi
    pvReceptionProv: Optional[str] = ""
    pvReceptionDef: Optional[str] = ""
    reservesALever: Optional[str] = ""
    delaiGarantie: Optional[str] = "12"
    statut: Optional[str] = ""
    observations: Optional[str] = ""

class MarcheInDB(Marche):
    id: int

# ─── ROUTES ───

@app.get("/", tags=["Accueil"])
def root():
    return {
        "message": "API Registre des Marchés Publics",
        "version": "1.0.0",
        "docs": "/docs"
    }

# Lister tous les marchés
@app.get("/marches", response_model=List[MarcheInDB], tags=["Marchés"])
def get_marches():
    return load_db()

# Créer un marché
@app.post("/marches", response_model=MarcheInDB, tags=["Marchés"])
def create_marche(marche: Marche):
    db = load_db()
    # Vérifier unicité du N° marché
    if any(m["numMarche"] == marche.numMarche for m in db):
        raise HTTPException(status_code=400, detail=f"Le marché {marche.numMarche} existe déjà")
    new_id = max((m["id"] for m in db), default=0) + 1
    new_marche = {"id": new_id, **marche.dict()}
    db.append(new_marche)
    save_db(db)
    return new_marche

# Obtenir un marché par ID
@app.get("/marches/{marche_id}", response_model=MarcheInDB, tags=["Marchés"])
def get_marche(marche_id: int):
    db = load_db()
    for m in db:
        if m["id"] == marche_id:
            return m
    raise HTTPException(status_code=404, detail="Marché non trouvé")

# Mettre à jour uniquement les champs vides (suivi progressif)
@app.patch("/marches/{marche_id}", response_model=MarcheInDB, tags=["Marchés"])
def update_marche(marche_id: int, updates: dict):
    db = load_db()
    for i, m in enumerate(db):
        if m["id"] == marche_id:
            for key, value in updates.items():
                # On ne modifie que les champs vides ou inexistants
                if key in m and m[key] in [None, "", [], 0]:
                    m[key] = value
                elif key not in m:
                    m[key] = value
            db[i] = m
            save_db(db)
            return m
    raise HTTPException(status_code=404, detail="Marché non trouvé")

# Forcer la mise à jour complète (admin)
@app.put("/marches/{marche_id}", response_model=MarcheInDB, tags=["Marchés"])
def replace_marche(marche_id: int, marche: Marche):
    db = load_db()
    for i, m in enumerate(db):
        if m["id"] == marche_id:
            updated = {"id": marche_id, **marche.dict()}
            db[i] = updated
            save_db(db)
            return updated
    raise HTTPException(status_code=404, detail="Marché non trouvé")

# Supprimer un marché
@app.delete("/marches/{marche_id}", tags=["Marchés"])
def delete_marche(marche_id: int):
    db = load_db()
    new_db = [m for m in db if m["id"] != marche_id]
    if len(new_db) == len(db):
        raise HTTPException(status_code=404, detail="Marché non trouvé")
    save_db(new_db)
    return {"message": f"Marché {marche_id} supprimé"}

# Recherche
@app.get("/marches/search/{query}", response_model=List[MarcheInDB], tags=["Recherche"])
def search_marches(query: str):
    db = load_db()
    q = query.lower()
    results = [
        m for m in db
        if q in m.get("numMarche", "").lower()
        or q in m.get("numAO", "").lower()
        or q in m.get("objetMarche", "").lower()
        or q in m.get("attributaire", "").lower()
        or q in m.get("maitreOuvrage", "").lower()
    ]
    return results

# Statistiques
@app.get("/stats", tags=["Statistiques"])
def get_stats():
    db = load_db()
    total = len(db)
    par_statut = {}
    montant_total = 0
    for m in db:
        s = m.get("statut") or "Non défini"
        par_statut[s] = par_statut.get(s, 0) + 1
        montant_total += m.get("montantMarche") or 0
    return {
        "total_marches": total,
        "par_statut": par_statut,
        "montant_total_dh": montant_total,
        "moyenne_montant_dh": round(montant_total / total, 2) if total > 0 else 0
    }

# Ajouter un avenant à un marché existant
@app.post("/marches/{marche_id}/avenants", response_model=MarcheInDB, tags=["Avenants"])
def add_avenant(marche_id: int, avenant: Avenant):
    db = load_db()
    for i, m in enumerate(db):
        if m["id"] == marche_id:
            m.setdefault("avenants", []).append(avenant.dict())
            db[i] = m
            save_db(db)
            return m
    raise HTTPException(status_code=404, detail="Marché non trouvé")

# Ajouter un décompte à un marché existant
@app.post("/marches/{marche_id}/decomptes", response_model=MarcheInDB, tags=["Décomptes"])
def add_decompte(marche_id: int, decompte: Decompte):
    db = load_db()
    for i, m in enumerate(db):
        if m["id"] == marche_id:
            m.setdefault("decomptes", []).append(decompte.dict())
            db[i] = m
            save_db(db)
            return m
    raise HTTPException(status_code=404, detail="Marché non trouvé")
