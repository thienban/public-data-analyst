import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "data.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.executescript("""
        CREATE TABLE IF NOT EXISTS companies (
            id TEXT PRIMARY KEY,
            siren TEXT UNIQUE NOT NULL,
            nom_complet TEXT,
            naf_code TEXT,
            naf_libelle TEXT,
            date_creation TEXT,
            tranche_effectif TEXT,
            nature_juridique TEXT,
            capital_social INTEGER,
            departement TEXT,
            ville TEXT,
            etat_administratif TEXT DEFAULT 'A',
            bodacc_alerts INTEGER DEFAULT 0,
            fragility_score INTEGER DEFAULT 0,
            cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_companies_naf ON companies(naf_code);
        CREATE INDEX IF NOT EXISTS idx_companies_dept ON companies(departement);

        CREATE TABLE IF NOT EXISTS dpe_records (
            id TEXT PRIMARY KEY,
            adresse TEXT,
            code_postal TEXT,
            ville TEXT,
            departement TEXT,
            classe_energie TEXT,
            etiquette_ges TEXT,
            annee_construction INTEGER,
            surface_habitable REAL,
            date_etablissement TEXT,
            cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_dpe_dept ON dpe_records(departement);
        CREATE INDEX IF NOT EXISTS idx_dpe_classe ON dpe_records(classe_energie);

        CREATE TABLE IF NOT EXISTS dvf_transactions (
            id TEXT PRIMARY KEY,
            date_mutation TEXT,
            type_local TEXT,
            commune TEXT,
            code_postal TEXT,
            departement TEXT,
            valeur_fonciere REAL,
            surface_reelle_bati REAL,
            nombre_pieces_principales INTEGER,
            latitude REAL,
            longitude REAL,
            cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_dvf_dept ON dvf_transactions(departement);
        CREATE INDEX IF NOT EXISTS idx_dvf_date ON dvf_transactions(date_mutation);

        CREATE TABLE IF NOT EXISTS analysis_reports (
            id TEXT PRIMARY KEY,
            query TEXT NOT NULL,
            query_params TEXT,
            report_markdown TEXT,
            companies_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    conn.commit()
    conn.close()
