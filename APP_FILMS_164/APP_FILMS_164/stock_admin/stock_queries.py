"""Requêtes SQL pour listes enrichies et statistiques homepage."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from APP_FILMS_164.database.database_tools import DBconnection


def _bq(name: str) -> str:
    return "`" + name.replace("`", "") + "`"


def monthly_movement_totals(year: int | None = None, month: int | None = None) -> dict[str, Any]:
    now = datetime.now()
    year = year or now.year
    month = month or now.month

    sql = f"""
        SELECT DAY(m.{_bq("date")}) AS jour,
               m.type_action,
               COALESCE(SUM(m.quantite * p.prix), 0) AS montant
        FROM t_mouvement m
        INNER JOIN t_produit p ON m.fk_produit = p.id_produit
        WHERE YEAR(m.{_bq("date")}) = %(year)s
          AND MONTH(m.{_bq("date")}) = %(month)s
          AND m.type_action IN ('DEPOT', 'RETRAIT')
        GROUP BY DAY(m.{_bq("date")}), m.type_action
        ORDER BY jour ASC
    """
    depenses_by_day: dict[int, float] = {}
    benefices_by_day: dict[int, float] = {}

    with DBconnection() as db:
        db.execute(sql, {"year": year, "month": month})
        for row in db.fetchall():
            jour = int(row["jour"])
            montant = float(row["montant"] or 0)
            if row["type_action"] == "DEPOT":
                depenses_by_day[jour] = depenses_by_day.get(jour, 0) + montant
            else:
                benefices_by_day[jour] = benefices_by_day.get(jour, 0) + montant

    days_in_month = _days_in_month(year, month)
    labels = [str(d) for d in range(1, days_in_month + 1)]
    depenses = [round(depenses_by_day.get(d, 0), 2) for d in range(1, days_in_month + 1)]
    benefices = [round(benefices_by_day.get(d, 0), 2) for d in range(1, days_in_month + 1)]

    return {
        "year": year,
        "month": month,
        "labels": labels,
        "depenses": depenses,
        "benefices": benefices,
        "total_depenses": round(sum(depenses), 2),
        "total_benefices": round(sum(benefices), 2),
    }


def _days_in_month(year: int, month: int) -> int:
    if month == 12:
        nxt = datetime(year + 1, 1, 1)
    else:
        nxt = datetime(year, month + 1, 1)
    cur = datetime(year, month, 1)
    return (nxt - cur).days


def fetch_produits() -> list[dict[str, Any]]:
    sql = f"""
        SELECT p.id_produit, 
               p.{_bq("type")} AS type_produit, 
               t.taille AS taille_lib,
               m.nom AS marque_lib,
               mo.annee AS annee_produit,
               p.prix, 
               p.quantite_stock
        FROM t_produit p
        LEFT JOIN t_modele mo ON p.fk_modele = mo.id_modele
        LEFT JOIN t_taille t ON p.fk_taille = t.id_taille
        LEFT JOIN t_marque m ON p.fk_marque = m.id_marque
        ORDER BY p.id_produit DESC
    """
    with DBconnection() as db:
        db.execute(sql)
        return db.fetchall()


def count_sessions() -> int:
    with DBconnection() as db:
        db.execute("SELECT COUNT(*) AS n FROM t_session")
        return int(db.fetchone()["n"])


def fetch_sessions_list() -> list[dict[str, Any]]:
    sql = """
        SELECT id_session, nom, prenom
        FROM t_session
        ORDER BY id_session DESC
    """
    with DBconnection() as db:
        db.execute(sql)
        rows = db.fetchall()
    for row in rows:
        row["mot_de_passe_masked"] = "******"
    return rows


def fetch_session_by_id(session_id: int) -> dict[str, Any] | None:
    with DBconnection() as db:
        db.execute(
            "SELECT id_session, nom, prenom, mot_de_passe FROM t_session WHERE id_session = %(id)s",
            {"id": session_id},
        )
        return db.fetchone()


def fetch_sessions_by_password(mot_de_passe: str) -> list[dict[str, Any]]:
    with DBconnection() as db:
        db.execute(
            "SELECT id_session, nom, prenom, mot_de_passe FROM t_session WHERE mot_de_passe = %(mdp)s",
            {"mdp": mot_de_passe},
        )
        return db.fetchall()


def fetch_connexions_enriched() -> list[dict[str, Any]]:
    sql = """
        SELECT c.id_connexion, c.date_debut, c.date_fin,
               CONCAT(s.prenom, ' ', s.nom) AS session_lib
        FROM t_connexion c
        INNER JOIN t_session s ON c.fk_session = s.id_session
        ORDER BY c.id_connexion DESC
    """
    with DBconnection() as db:
        db.execute(sql)
        return db.fetchall()


def inserer_connexion(fk_session: int) -> int:
    with DBconnection() as db:
        db.execute(
            """UPDATE t_connexion
               SET date_fin = NOW()
               WHERE fk_session = %(fk_session)s
                 AND date_fin IS NULL""",
            {"fk_session": fk_session},
        )
        db.execute(
            """INSERT INTO t_connexion (fk_session, date_debut)
               VALUES (%(fk_session)s, NOW())""",
            {"fk_session": fk_session},
        )
        db.execute("SELECT LAST_INSERT_ID() AS id")
        return int(db.fetchone()["id"])


def cloturer_connexion(id_connexion: int) -> None:
    with DBconnection() as db:
        db.execute(
            """UPDATE t_connexion
               SET date_fin = NOW()
               WHERE id_connexion = %(id)s
                 AND date_fin IS NULL""",
            {"id": id_connexion},
        )


def fetch_tailles() -> list[dict[str, Any]]:
    with DBconnection() as db:
        db.execute("SELECT id_taille, taille FROM t_taille ORDER BY id_taille DESC")
        return db.fetchall()
