"""
Claude tool definitions for the intelligence analyst agent.
Each tool maps to a real French public API call.
"""

TOOLS = [
    {
        "name": "search_companies",
        "description": (
            "Recherche des entreprises actives dans la base SIRENE par code NAF et département. "
            "Retourne la liste des entreprises avec leur profil (taille, date création, capital, nature juridique)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "naf_code": {
                    "type": "string",
                    "description": "Code NAF (ex: 43.39Z, 41.20A, 71.11Z)",
                },
                "departement": {
                    "type": "string",
                    "description": "Numéro de département (ex: 91, 92)",
                },
                "per_page": {
                    "type": "integer",
                    "description": "Nombre de résultats par page (max 25)",
                    "default": 25,
                },
            },
            "required": ["naf_code", "departement"],
        },
    },
    {
        "name": "get_dpe_stats",
        "description": (
            "Récupère les statistiques DPE (Diagnostic de Performance Énergétique) pour un département. "
            "Identifie le nombre de passoires thermiques (classes E, F, G) = potentiel de rénovation énergétique."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "departement": {
                    "type": "string",
                    "description": "Numéro de département (ex: 91, 92)",
                },
            },
            "required": ["departement"],
        },
    },
    {
        "name": "get_dvf_stats",
        "description": (
            "Récupère les statistiques des transactions immobilières DVF récentes pour un département. "
            "Un volume élevé de ventes de maisons = fort indicateur de projets de rénovation à venir."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "departement": {
                    "type": "string",
                    "description": "Numéro de département (ex: 91, 92)",
                },
                "months_back": {
                    "type": "integer",
                    "description": "Fenêtre temporelle en mois (défaut: 6)",
                    "default": 6,
                },
            },
            "required": ["departement"],
        },
    },
    {
        "name": "generate_report",
        "description": (
            "Génère et sauvegarde un rapport d'analyse stratégique complet au format Markdown. "
            "Inclut l'audit concurrence, la segmentation stratégique et les recommandations business."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Titre du rapport"},
                "content": {"type": "string", "description": "Contenu Markdown du rapport"},
                "query_params": {"type": "object", "description": "Paramètres de la requête"},
            },
            "required": ["title", "content"],
        },
    },
]
