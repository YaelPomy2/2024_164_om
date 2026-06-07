from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Literal

InputKind = Literal[
    "text",
    "int",
    "decimal",
    "year",
    "datetime",
    "timestamp",
    "enum",
    "fk",
    "password",
]


@dataclass(frozen=True)
class FieldSpec:
    name: str
    label: str
    kind: InputKind
    required: bool = True
    ref_table: str | None = None
    ref_pk: str | None = None
    ref_label_cols: tuple[str, ...] | None = None
    enum_values: tuple[str, ...] | None = None
    readonly: bool = False


@dataclass(frozen=True)
class TableSpec:
    table: str
    label: str
    pk: str | None
    list_columns: tuple[str, ...]
    fields: tuple[FieldSpec, ...]


STOCK_NAV_TABLE_KEYS: Final[tuple[str, ...]] = (
    "t_session",
    "t_produit",
    "t_connexion",
)

TABLES: dict[str, TableSpec] = {
    "t_session": TableSpec(
        table="t_session",
        label="Sessions",
        pk="id_session",
        list_columns=("id_session", "nom", "prenom", "mot_de_passe_masked"),
        fields=(
            FieldSpec("nom", "Nom de la session", "text", required=True),
            FieldSpec("prenom", "Prénom de la session", "text", required=True),
            FieldSpec("mot_de_passe", "Mot de passe de session", "password", required=True),
        ),
    ),
    "t_connexion": TableSpec(
        table="t_connexion",
        label="Historique de connexion",
        pk="id_connexion",
        list_columns=("id_connexion", "session_lib", "date_debut", "date_fin"),
        fields=(
            FieldSpec(
                "fk_session",
                "Session",
                "fk",
                required=True,
                ref_table="t_session",
                ref_pk="id_session",
                ref_label_cols=("nom", "prenom"),
            ),
            FieldSpec("date_debut", "Date début", "datetime", required=True),
            FieldSpec("date_fin", "Date fin", "datetime", required=False),
        ),
    ),
    "t_produit": TableSpec(
        table="t_produit",
        label="Produits",
        pk="id_produit",
        list_columns=("id_produit", "type_produit", "taille_lib", "marque_lib", "annee_produit", "prix", "quantite_stock"),
        fields=(
            FieldSpec("type", "Produit", "text", required=True),
            FieldSpec("marque_nom", "Marque", "text", required=False),
            FieldSpec("modele_nom", "Modèle", "text", required=False),
            FieldSpec("modele_annee", "Année du produit", "year", required=False),
            FieldSpec("taille_lib", "Taille", "text", required=False),
            FieldSpec("prix", "Prix", "decimal", required=True),
            FieldSpec("quantite_stock", "Quantité en stock", "int", required=True),
        ),
    ),
    "t_taille": TableSpec(
        table="t_taille",
        label="Tailles",
        pk="id_taille",
        list_columns=("id_taille", "taille"),
        fields=(FieldSpec("taille", "Taille", "text", required=True),),
    ),
    "t_mouvement": TableSpec(
        table="t_mouvement",
        label="Mouvements",
        pk="id_action",
        list_columns=(
            "id_action",
            "session_lib",
            "produit_lib",
            "type_action",
            "quantite",
            "date",
        ),
        fields=(
            FieldSpec(
                "fk_session",
                "Session",
                "fk",
                required=True,
                ref_table="t_session",
                ref_pk="id_session",
                ref_label_cols=("nom", "prenom"),
            ),
            FieldSpec(
                "fk_produit",
                "Produit",
                "fk",
                required=True,
                ref_table="t_produit",
                ref_pk="id_produit",
                ref_label_cols=("type",),
            ),
            FieldSpec(
                "type_action",
                "Type d'action",
                "enum",
                required=True,
                enum_values=("DEPOT", "RETRAIT"),
            ),
            FieldSpec("quantite", "Quantité", "int", required=True),
            FieldSpec("date", "Date", "datetime", required=True),
        ),
    ),
    "t_link_produit_taille": TableSpec(
        table="t_link_produit_taille",
        label="Produit ↔ Taille",
        pk=None,
        list_columns=("produit_nom", "taille_lib"),
        fields=(
            FieldSpec(
                "fk_produit",
                "Produit",
                "fk",
                required=True,
                ref_table="t_produit",
                ref_pk="id_produit",
                ref_label_cols=("type",),
            ),
            FieldSpec(
                "fk_taille",
                "Taille",
                "fk",
                required=True,
                ref_table="t_taille",
                ref_pk="id_taille",
                ref_label_cols=("taille",),
            ),
        ),
    ),
}
