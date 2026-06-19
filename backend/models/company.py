from pydantic import BaseModel
from typing import Optional


NAF_LABELS = {
    "71.11Z": "Architecture",
    "41.20A": "Contractant général / Maisons individuelles",
    "43.39Z": "Rénovation TCE / Autres travaux finition",
    "43.21A": "Travaux installation électrique",
    "43.22A": "Travaux installation eau / gaz",
    "62.01Z": "Programmation informatique",
    "62.02A": "Conseil systèmes informatiques",
    "63.11Z": "Traitement données hébergement",
}

FRAGILITY_THRESHOLDS = {
    "41.20A": 50_000,   # Contractant général : capital minimal attendu
    "43.39Z": 10_000,
    "71.11Z": 5_000,
}


class Company(BaseModel):
    id: str
    siren: str
    nom_complet: Optional[str] = None
    naf_code: Optional[str] = None
    naf_libelle: Optional[str] = None
    date_creation: Optional[str] = None
    tranche_effectif: Optional[str] = None
    nature_juridique: Optional[str] = None
    capital_social: Optional[int] = None
    departement: Optional[str] = None
    ville: Optional[str] = None
    etat_administratif: str = "A"
    bodacc_alerts: int = 0
    fragility_score: int = 0

    @property
    def is_fragile(self) -> bool:
        threshold = FRAGILITY_THRESHOLDS.get(self.naf_code or "", 0)
        if threshold and self.capital_social and self.capital_social < threshold:
            return True
        if self.bodacc_alerts > 0:
            return True
        return False

    @property
    def maturity_label(self) -> str:
        if not self.date_creation:
            return "Inconnue"
        year = int(self.date_creation[:4])
        age = 2026 - year
        if age < 3:
            return "Startup (<3 ans)"
        if age < 7:
            return "Croissance (3-7 ans)"
        if age < 15:
            return "Etablie (7-15 ans)"
        return "Senior (15+ ans)"


class CompanySearchParams(BaseModel):
    naf_codes: list[str] = ["43.39Z"]
    departements: list[str] = ["91", "92"]
    page: int = 1
    per_page: int = 25
    etat_administratif: str = "A"
