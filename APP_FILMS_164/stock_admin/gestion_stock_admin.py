from __future__ import annotations

from datetime import datetime
from decimal import Decimal
import time

from flask import flash, redirect, render_template, request, session, url_for

from APP_FILMS_164 import app
from APP_FILMS_164.database.database_tools import DBconnection
from APP_FILMS_164.stock_admin.stock_config import FieldSpec, STOCK_NAV_TABLE_KEYS, TABLES, TableSpec
from APP_FILMS_164.stock_admin.stock_queries import (
    count_sessions,
    fetch_connexions_enriched,
    fetch_produits,
    fetch_session_by_id,
    fetch_sessions_by_password,
    fetch_sessions_list,
    fetch_tailles,
)

LIST_COLUMN_LABELS: dict[str, str] = {
    "id_session": "N° session",
    "id_connexion": "N°",
    "id_produit": "N° produit",
    "id_taille": "N°",
    "nom": "Nom",
    "prenom": "Prénom",
    "mot_de_passe_masked": "Mot de passe",
    "session_lib": "Session",
    "date_debut": "Début",
    "date_fin": "Fin",
    "type_produit": "Produit",
    "taille_lib": "Taille",
    "marque_lib": "Marque",
    "annee_produit": "Année du produit",
    "prix": "Prix",
    "quantite_stock": "Stock",
    "taille": "Taille",
    "type_action": "Action",
    "quantite": "Quantité",
    "date": "Date",
    "produit_lib": "Produit",
    "produit_nom": "Produit",
}


def _bq(name: str) -> str:
    return "`" + name.replace("`", "") + "`"


def _col_list(columns: tuple[str, ...]) -> str:
    return ", ".join(_bq(c) for c in columns)


def _column_label(key: str) -> str:
    return LIST_COLUMN_LABELS.get(key, key.replace("_", " ").capitalize())


def _clear_active_session() -> None:
    session.pop("active_session_id", None)
    session.pop("active_session_nom", None)
    session.pop("active_session_prenom", None)
    session.modified = True


def _set_active_session(shop_session: dict) -> None:
    session.permanent = False
    session["active_session_id"] = shop_session["id_session"]
    session["active_session_nom"] = shop_session["nom"]
    session["active_session_prenom"] = shop_session["prenom"]
    session.modified = True


def _get_active_session() -> dict | None:
    session_id = session.get("active_session_id")
    if not session_id:
        return None
    return fetch_session_by_id(int(session_id))


def _is_session_authenticated() -> bool:
    return _get_active_session() is not None


def _redirect_list(table_key: str, **kwargs):
    kwargs.setdefault("_", int(time.time() * 1000))
    return redirect(url_for("stock_table_list", table_key=table_key, **kwargs), code=303)


def _bootstrap_allowed() -> bool:
    """Première session : accès à t_session sans connexion si la base est vide."""
    return count_sessions() == 0 and (
        request.endpoint in {"stock_table_list", "stock_table_add"}
        and request.view_args
        and request.view_args.get("table_key") == "t_session"
    )


@app.context_processor
def inject_stock_nav():
    active = _get_active_session()
    label = None
    if active:
        label = f"{active['prenom']} {active['nom']}"
    return {
        "stock_nav_tables": [(k, TABLES[k]) for k in STOCK_NAV_TABLE_KEYS if k in TABLES],
        "list_column_label": _column_label,
        "active_session_label": label,
        "is_session_logged_in": active is not None,
    }


@app.after_request
def _no_cache_stock_pages(response):
    if request.path.startswith("/stock"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response


@app.before_request
def _protect_stock_routes():
    if not request.path.startswith("/stock"):
        return None
    if request.endpoint == "stock_login":
        return None
    if _bootstrap_allowed():
        return None
    if _is_session_authenticated():
        return None
    flash("Connexion requise : saisissez le mot de passe d'une session existante.", "warning")
    return redirect(url_for("stock_login", next=request.path))


@app.route("/stock/login", methods=["GET", "POST"])
def stock_login():
    next_url = request.args.get("next") or request.form.get("next") or url_for("stock_home")

    if request.method == "POST":
        password = (request.form.get("password") or "").strip()
        matches = fetch_sessions_by_password(password)
        if len(matches) == 1:
            _set_active_session(matches[0])
            flash(f"Session active : {matches[0]['prenom']} {matches[0]['nom']}.", "success")
            return redirect(next_url, code=303)
        if len(matches) > 1:
            flash("Plusieurs sessions partagent ce mot de passe. Contactez l'administrateur.", "danger")
        else:
            flash("Mot de passe inconnu. Aucune session ne correspond.", "danger")

    return render_template("stock/login.html", next_url=next_url, no_sessions_yet=(count_sessions() == 0))


@app.route("/stock/logout", methods=["POST"])
def stock_logout():
    _clear_active_session()
    flash("Déconnexion effectuée.", "info")
    return redirect(url_for("stock_login"), code=303)


def _fk_choices(field: FieldSpec) -> list[tuple[str, str]]:
    assert field.ref_table and field.ref_pk and field.ref_label_cols
    cols = (field.ref_pk,) + tuple(field.ref_label_cols)
    cols_sql = _col_list(cols)
    sql = f"SELECT {cols_sql} FROM {field.ref_table} ORDER BY {_bq(field.ref_pk)} ASC"
    with DBconnection() as db:
        db.execute(sql)
        rows = db.fetchall()
    choices: list[tuple[str, str]] = [("", "— Aucune —")]
    for r in rows:
        label = " ".join(str(r[c]) for c in field.ref_label_cols if r.get(c) is not None).strip()
        choices.append((str(r[field.ref_pk]), label or str(r[field.ref_pk])))
    return choices


def _parse_value(field: FieldSpec, raw: str | None):
    if raw is None:
        return None
    raw = raw.strip()
    if raw == "":
        return None

    if field.kind == "int" or field.kind == "fk":
        return int(raw)
    if field.kind == "decimal":
        return Decimal(raw)
    if field.kind == "year":
        return int(raw)
    if field.kind == "datetime":
        return datetime.fromisoformat(raw)
    if field.kind in ("timestamp", "text", "enum", "password"):
        return raw
    return raw


def _is_readonly_table(spec: TableSpec) -> bool:
    return spec.table == "t_connexion"


def _fetch_list_rows(spec: TableSpec) -> list[dict]:
    if spec.table == "t_session":
        return fetch_sessions_list()
    if spec.table == "t_connexion":
        return fetch_connexions_enriched()
    if spec.table == "t_produit":
        return fetch_produits()
    if spec.table == "t_taille":
        return fetch_tailles()
    cols = _col_list(spec.list_columns)
    sql = f"SELECT {cols} FROM {spec.table} ORDER BY {_bq(spec.pk)} DESC"
    with DBconnection() as db:
        db.execute(sql)
        return db.fetchall()


def _clean_text(name: str) -> str | None:
    value = (request.form.get(name) or "").strip()
    return value or None


def _fetch_produit_form_row(pk_value: str) -> dict | None:
    sql = f"""
        SELECT p.*,
               ma.nom AS marque_nom,
               mo.nom AS modele_nom,
               mo.annee AS modele_annee,
               t.taille AS taille_lib
        FROM t_produit p
        LEFT JOIN t_marque ma ON p.fk_marque = ma.id_marque
        LEFT JOIN t_modele mo ON p.fk_modele = mo.id_modele
        LEFT JOIN t_taille t ON p.fk_taille = t.id_taille
        WHERE p.id_produit = %(pk)s
    """
    with DBconnection() as db:
        db.execute(sql, {"pk": pk_value})
        return db.fetchone()


def _get_or_create_marque(db, nom: str | None) -> int | None:
    if nom is None:
        return None

    db.execute("SELECT id_marque FROM t_marque WHERE nom = %(nom)s", {"nom": nom})
    row = db.fetchone()
    if row:
        return int(row["id_marque"])

    db.execute("INSERT INTO t_marque (nom) VALUES (%(nom)s)", {"nom": nom})
    db.execute("SELECT LAST_INSERT_ID() AS id")
    return int(db.fetchone()["id"])


def _get_or_create_modele(db, nom: str | None, annee: int | None, marque_id: int | None) -> int | None:
    if nom is None and annee is None:
        return None
    if nom is None or annee is None:
        raise ValueError("Le modèle et l'année du produit doivent être remplis ensemble.")

    db.execute(
        """SELECT id_modele
           FROM t_modele
           WHERE nom = %(nom)s
             AND annee = %(annee)s
             AND fk_marque <=> %(marque_id)s""",
        {"nom": nom, "annee": annee, "marque_id": marque_id},
    )
    row = db.fetchone()
    if row:
        return int(row["id_modele"])

    db.execute(
        """INSERT INTO t_modele (fk_marque, nom, annee)
           VALUES (%(marque_id)s, %(nom)s, %(annee)s)""",
        {"marque_id": marque_id, "nom": nom, "annee": annee},
    )
    db.execute("SELECT LAST_INSERT_ID() AS id")
    return int(db.fetchone()["id"])


def _get_or_create_taille(db, taille: str | None) -> int | None:
    if taille is None:
        return None

    db.execute("SELECT id_taille FROM t_taille WHERE taille = %(taille)s", {"taille": taille})
    row = db.fetchone()
    if row:
        return int(row["id_taille"])

    db.execute("INSERT INTO t_taille (taille) VALUES (%(taille)s)", {"taille": taille})
    db.execute("SELECT LAST_INSERT_ID() AS id")
    return int(db.fetchone()["id"])


def _produit_values_from_form(db) -> dict:
    type_produit = _clean_text("type")
    if type_produit is None:
        raise ValueError("Champ obligatoire : « Produit »")

    prix_raw = _clean_text("prix")
    if prix_raw is None:
        raise ValueError("Champ obligatoire : « Prix »")

    stock_raw = _clean_text("quantite_stock")
    if stock_raw is None:
        raise ValueError("Champ obligatoire : « Quantité en stock »")

    annee_raw = _clean_text("modele_annee")
    annee = int(annee_raw) if annee_raw is not None else None
    marque_id = _get_or_create_marque(db, _clean_text("marque_nom"))
    modele_id = _get_or_create_modele(db, _clean_text("modele_nom"), annee, marque_id)
    taille_id = _get_or_create_taille(db, _clean_text("taille_lib"))

    return {
        "fk_marque": marque_id,
        "fk_modele": modele_id,
        "fk_taille": taille_id,
        "type": type_produit,
        "prix": Decimal(prix_raw),
        "quantite_stock": int(stock_raw),
    }


def _render_produit_add_edit(spec: TableSpec, pk_value: str | None):
    fk_choices = {f.name: _fk_choices(f) for f in spec.fields if f.kind == "fk"}
    row = _fetch_produit_form_row(pk_value) if pk_value is not None else None

    if request.method == "POST":
        try:
            with DBconnection() as db:
                values = _produit_values_from_form(db)
                if pk_value is None:
                    sql = f"""INSERT INTO t_produit
                              (fk_marque, fk_modele, fk_taille, {_bq("type")}, prix, quantite_stock)
                              VALUES (%(fk_marque)s, %(fk_modele)s, %(fk_taille)s,
                                      %(type)s, %(prix)s, %(quantite_stock)s)"""
                    db.execute(sql, values)
                    flash(f"{spec.label} : ajout effectué.", "success")
                else:
                    sql = f"""UPDATE t_produit
                              SET fk_marque = %(fk_marque)s,
                                  fk_modele = %(fk_modele)s,
                                  fk_taille = %(fk_taille)s,
                                  {_bq("type")} = %(type)s,
                                  prix = %(prix)s,
                                  quantite_stock = %(quantite_stock)s
                              WHERE id_produit = %(pk)s"""
                    db.execute(sql, {**values, "pk": pk_value})
                    flash(f"{spec.label} : mise à jour effectuée.", "success")
            return _redirect_list("t_produit")
        except Exception as e:
            flash(f"Erreur : {e}", "danger")
            return render_template("stock/form.html", spec=spec, row=row, fk_choices=fk_choices)

    return render_template("stock/form.html", spec=spec, row=row, fk_choices=fk_choices)


def _render_add_edit(table_key: str, pk_value: str | None):
    spec = TABLES[table_key]
    if spec.table == "t_produit":
        return _render_produit_add_edit(spec, pk_value)

    fk_choices: dict[str, list[tuple[str, str]]] = {}
    for f in spec.fields:
        if f.kind == "fk":
            fk_choices[f.name] = _fk_choices(f)

    row = None
    if pk_value is not None:
        assert spec.pk
        sql = f"SELECT * FROM {spec.table} WHERE {_bq(spec.pk)} = %(pk)s"
        with DBconnection() as db:
            db.execute(sql, {"pk": pk_value})
            row = db.fetchone()

    if request.method == "POST":
        values = {}
        for f in spec.fields:
            if f.readonly:
                continue
            raw = request.form.get(f.name)
            v = _parse_value(f, raw)
            if pk_value is not None and f.kind == "password" and v is None:
                continue
            if f.required and v is None:
                flash(f'Champ obligatoire : « {f.label} »', "warning")
                return render_template("stock/form.html", spec=spec, row=row, fk_choices=fk_choices)
            if v is not None:
                values[f.name] = v

        try:
            if pk_value is None:
                cols = ", ".join(_bq(k) for k in values.keys())
                params = ", ".join([f"%({k})s" for k in values.keys()])
                sql = f"INSERT INTO {spec.table} ({cols}) VALUES ({params})"
                new_id = None
                with DBconnection() as db:
                    db.execute(sql, values)
                    if spec.table == "t_session":
                        db.execute("SELECT LAST_INSERT_ID() AS id")
                        new_id = db.fetchone()["id"]
                flash(f"{spec.label} : ajout effectué.", "success")
                if spec.table == "t_session" and new_id and not _is_session_authenticated():
                    new_session = fetch_session_by_id(int(new_id))
                    if new_session:
                        _set_active_session(new_session)
                        flash("Vous êtes connecté avec cette nouvelle session.", "success")
            else:
                assert spec.pk
                if not values:
                    flash("Aucune modification à enregistrer.", "info")
                    return _redirect_list(table_key)
                sets = ", ".join([f"{_bq(k)} = %({k})s" for k in values.keys()])
                sql = f"UPDATE {spec.table} SET {sets} WHERE {_bq(spec.pk)} = %(pk)s"
                with DBconnection() as db:
                    db.execute(sql, {**values, "pk": pk_value})
                flash(f"{spec.label} : mise à jour effectuée.", "success")
                if spec.table == "t_session" and str(pk_value) == str(session.get("active_session_id")):
                    updated = fetch_session_by_id(int(pk_value))
                    if updated:
                        _set_active_session(updated)
            return _redirect_list(table_key)
        except Exception as e:
            flash(f"Erreur BD : {e}", "danger")
            return render_template("stock/form.html", spec=spec, row=row, fk_choices=fk_choices)

    return render_template("stock/form.html", spec=spec, row=row, fk_choices=fk_choices)


def _handle_session_create_post() -> bool:
    """Création depuis t_session : utilise le contexte de la session active connectée."""
    active = _get_active_session()
    nom = (request.form.get("nom") or "").strip()
    prenom = (request.form.get("prenom") or "").strip()
    mdp = (request.form.get("mot_de_passe") or "").strip()

    if not nom or not prenom or not mdp:
        flash("Nom, prénom et mot de passe sont obligatoires.", "warning")
        return False

    try:
        with DBconnection() as db:
            db.execute(
                """INSERT INTO t_session (nom, prenom, mot_de_passe)
                   VALUES (%(nom)s, %(prenom)s, %(mot_de_passe)s)""",
                {"nom": nom, "prenom": prenom, "mot_de_passe": mdp},
            )
            db.execute("SELECT LAST_INSERT_ID() AS id")
            new_id = db.fetchone()["id"]

        if not active:
            new_session = fetch_session_by_id(int(new_id))
            if new_session:
                _set_active_session(new_session)

        flash("Session créée.", "success")
        if active:
            flash(
                f"Session active inchangée : {active['prenom']} {active['nom']}.",
                "info",
            )
        return True
    except Exception as e:
        flash(f"Erreur création session : {e}", "danger")
        return False


@app.route("/stock")
def stock_home():
    tables = [(k, TABLES[k]) for k in STOCK_NAV_TABLE_KEYS if k in TABLES]
    return render_template("stock/home.html", tables=tables)


@app.route("/stock/<string:table_key>", methods=["GET", "POST"])
def stock_table_list(table_key: str):
    spec = TABLES[table_key]
    if spec.table == "t_link_produit_taille":
        return redirect(url_for("stock_link_list"), code=303)

    if request.method == "POST" and spec.table == "t_session":
        if request.form.get("action") == "create_session":
            if _handle_session_create_post():
                return _redirect_list("t_session")

    rows = _fetch_list_rows(spec)
    active = _get_active_session()

    return render_template(
        "stock/list.html",
        spec=spec,
        rows=rows,
        readonly=_is_readonly_table(spec),
        show_session_panel=(spec.table == "t_session"),
        active_session=active,
    )


@app.route("/stock/<string:table_key>/add", methods=["GET", "POST"])
def stock_table_add(table_key: str):
    if table_key not in TABLES:
        flash("Table inconnue.", "danger")
        return redirect(url_for("stock_home"), code=303)
    spec = TABLES[table_key]
    if spec.table == "t_link_produit_taille":
        return redirect(url_for("stock_link_list"), code=303)
    if _is_readonly_table(spec):
        flash(f"{spec.label} : ajout manuel désactivé.", "info")
        return _redirect_list(table_key)
    return _render_add_edit(table_key, None)


@app.route("/stock/<string:table_key>/edit/<int:pk>", methods=["GET", "POST"])
def stock_table_edit(table_key: str, pk: int):
    if table_key not in TABLES:
        flash("Table inconnue.", "danger")
        return redirect(url_for("stock_home"), code=303)
    spec = TABLES[table_key]
    if spec.table == "t_link_produit_taille":
        return redirect(url_for("stock_link_list"), code=303)
    if _is_readonly_table(spec):
        flash(f"{spec.label} : modification manuelle désactivée.", "info")
        return _redirect_list(table_key)
    return _render_add_edit(table_key, str(pk))


@app.route("/stock/<string:table_key>/delete/<int:pk>", methods=["GET", "POST"])
def stock_table_delete(table_key: str, pk: int):
    if table_key not in TABLES:
        flash("Table inconnue.", "danger")
        return redirect(url_for("stock_home"), code=303)
    spec = TABLES[table_key]
    if spec.table == "t_link_produit_taille":
        return redirect(url_for("stock_link_list"), code=303)
    if _is_readonly_table(spec):
        flash(f"{spec.label} : suppression manuelle désactivée.", "info")
        return _redirect_list(table_key)

    assert spec.pk
    sql_select = f"SELECT * FROM {spec.table} WHERE {_bq(spec.pk)} = %(pk)s"
    with DBconnection() as db:
        db.execute(sql_select, {"pk": pk})
        row = db.fetchone()

    if request.method == "POST":
        try:
            sql_delete = f"DELETE FROM {spec.table} WHERE {_bq(spec.pk)} = %(pk)s"
            with DBconnection() as db:
                db.execute(sql_delete, {"pk": pk})
            if spec.table == "t_session" and session.get("active_session_id") == pk:
                _clear_active_session()
                flash("La session supprimée était active : vous êtes déconnecté.", "warning")
            flash(f"{spec.label} : suppression effectuée.", "success")
            return _redirect_list(table_key)
        except Exception as e:
            flash(
                "Suppression impossible (élément lié ailleurs). Supprimez d'abord les dépendances.",
                "danger",
            )
            flash(f"Détail : {e}", "danger")

    return render_template("stock/delete.html", spec=spec, row=row, back_table_key=table_key)


@app.route("/stock/sessions/new", methods=["GET", "POST"])
def stock_create_session():
    return redirect(url_for("stock_table_list", table_key="t_session"), code=303)


@app.route("/stock/liens-produit-taille", methods=["GET", "POST"])
def stock_link_list():
    spec = TABLES["t_link_produit_taille"]
    produit_field = spec.fields[0]
    taille_field = spec.fields[1]
    produits = _fk_choices(produit_field)
    tailles = _fk_choices(taille_field)

    if request.method == "POST":
        fk_produit = request.form.get("fk_produit")
        fk_taille = request.form.get("fk_taille")
        if not fk_produit or not fk_taille:
            flash("Produit et taille obligatoires.", "warning")
        else:
            try:
                sql = """INSERT INTO t_link_produit_taille (fk_produit, fk_taille)
                         VALUES (%(fk_produit)s, %(fk_taille)s)"""
                with DBconnection() as db:
                    db.execute(sql, {"fk_produit": int(fk_produit), "fk_taille": int(fk_taille)})
                flash("Association ajoutée.", "success")
                return redirect(url_for("stock_link_list", _=int(time.time() * 1000)), code=303)
            except Exception as e:
                flash(f"Erreur : {e}", "danger")

    sql = f"""SELECT l.fk_produit, p.{_bq("type")} AS produit_nom,
                    l.fk_taille, t.taille AS taille_lib
             FROM t_link_produit_taille l
             INNER JOIN t_produit p ON l.fk_produit = p.id_produit
             INNER JOIN t_taille t ON l.fk_taille = t.id_taille
             ORDER BY l.fk_produit DESC, l.fk_taille DESC"""
    with DBconnection() as db:
        db.execute(sql)
        links = db.fetchall()

    return render_template(
        "stock/link_list.html",
        spec=spec,
        links=links,
        produits=produits,
        tailles=tailles,
    )


@app.route("/stock/liens-produit-taille/delete/<int:fk_produit>/<int:fk_taille>", methods=["POST"])
def stock_link_delete(fk_produit: int, fk_taille: int):
    try:
        sql = """DELETE FROM t_link_produit_taille
                 WHERE fk_produit = %(fk_produit)s AND fk_taille = %(fk_taille)s"""
        with DBconnection() as db:
            db.execute(sql, {"fk_produit": fk_produit, "fk_taille": fk_taille})
        flash("Association supprimée.", "success")
    except Exception as e:
        flash(f"Erreur : {e}", "danger")
    return redirect(url_for("stock_link_list", _=int(time.time() * 1000)), code=303)
