-- =======================
-- Requêtes SQL commentées¨
-- =======================

-- FILMS 

INSERT INTO t_film (id_film, nom_film) VALUES (NULL, %(value_nom_film)s);  -- Ajoute un nouveau film

SELECT * FROM t_film WHERE id_film = %(value_id_film)s;  -- Sélectionne le film à modifier ou à effacer

UPDATE t_film SET nom_film = %(value_nom_film)s, duree_film = %(value_duree_film)s, description_film = %(value_description_film)s, cover_link_film = %(value_cover_link_film)s, date_sortie_film = %(value_datesortie_film)s WHERE id_film = %(value_id_film)s;  -- Modifie un film existant

DELETE FROM t_genre_film WHERE fk_film = %(value_id_film)s;  -- Supprime les liaisons du film avant de pouvoir l'effacer

DELETE FROM t_film WHERE id_film = %(value_id_film)s;  -- Supprime définitivement le film

-- GENRES / PRODUITS 

SELECT id_produit, prix, quantite_stock, `type` AS nom, fk_modele FROM t_produit ORDER BY id_produit ASC;  -- Sélectionne tous les produits triés par id ascendant

SELECT id_produit, prix, quantite_stock, `type` AS nom, fk_modele FROM t_produit WHERE id_produit = %(value_id_selected)s;  -- Sélectionne un produit précis selon son id

SELECT id_produit, prix, quantite_stock, `type` AS nom, fk_modele FROM t_produit ORDER BY id_produit DESC;  -- Sélectionne tous les produits triés par id descendant

INSERT INTO t_produit (prix, quantite_stock, `type`, fk_modele) VALUES (%(value_prix)s, %(value_quantite_stock)s, %(value_nom)s, %(value_fk_modele)s);  -- Ajoute un nouveau produit

SELECT id_produit, `type` AS nom, prix, quantite_stock, fk_modele FROM t_produit WHERE id_produit = %(value_id_produit)s;  -- Sélectionne un produit pour pré-remplir le formulaire UPDATE

UPDATE t_produit SET `type` = %(value_nom)s, prix = %(value_prix)s, quantite_stock = %(value_quantite_stock)s, fk_modele = %(value_fk_modele)s WHERE id_produit = %(value_id_produit)s;  -- Modifie un produit existant

SELECT CONCAT('Mouvement #', id_action, ' (fk_session=', fk_session, ')') AS description_assoc FROM t_mouvement WHERE fk_produit = %(value_id_produit)s UNION ALL SELECT CONCAT('Taille liée fk_taille=', fk_taille) AS description_assoc FROM t_link_produit_taille WHERE fk_produit = %(value_id_produit)s;  -- Liste les objets associés (mouvements + tailles) au produit avant suppression

SELECT id_produit, `type` AS nom FROM t_produit WHERE id_produit = %(value_id_produit)s;  -- Sélectionne le produit à effacer pour confirmation

DELETE FROM t_mouvement WHERE fk_produit = %(value_id_produit)s;  -- Supprime les mouvements liés au produit

DELETE FROM t_link_produit_taille WHERE fk_produit = %(value_id_produit)s;  -- Supprime les liaisons produit/taille du produit

DELETE FROM t_produit WHERE id_produit = %(value_id_produit)s;  -- Supprime définitivement le produit


-- ASSOCIATIONS FILMS 

SELECT id_film, nom_film, duree_film, description_film, cover_link_film, date_sortie_film, GROUP_CONCAT(intitule_genre) as GenresFilms FROM t_genre_film RIGHT JOIN t_film ON t_film.id_film = t_genre_film.fk_film LEFT JOIN t_genre ON t_genre.id_genre = t_genre_film.fk_genre GROUP BY id_film;  -- Sélectionne tous les films avec leurs genres concaténés

SELECT id_film, nom_film, duree_film, description_film, cover_link_film, date_sortie_film, GROUP_CONCAT(intitule_genre) as GenresFilms FROM t_genre_film RIGHT JOIN t_film ON t_film.id_film = t_genre_film.fk_film LEFT JOIN t_genre ON t_genre.id_genre = t_genre_film.fk_genre GROUP BY id_film HAVING id_film = %(value_id_film_selected)s;  -- Sélectionne un film précis avec ses genres associés

SELECT id_genre, intitule_genre FROM t_genre ORDER BY id_genre ASC;  -- Sélectionne tous les genres existants pour la liste déroulante

SELECT id_film, nom_film, duree_film, description_film, cover_link_film, date_sortie_film, GROUP_CONCAT(id_genre) as GenresFilms FROM t_genre_film INNER JOIN t_film ON t_film.id_film = t_genre_film.fk_film INNER JOIN t_genre ON t_genre.id_genre = t_genre_film.fk_genre WHERE id_film = %(value_id_film_selected)s;  -- Sélectionne le film et la liste des ids de genres qui lui sont attribués

SELECT id_genre, intitule_genre FROM t_genre WHERE id_genre NOT IN (SELECT id_genre AS idGenresFilms FROM t_genre_film INNER JOIN t_film ON t_film.id_film = t_genre_film.fk_film INNER JOIN t_genre ON t_genre.id_genre = t_genre_film.fk_genre WHERE id_film = %(value_id_film_selected)s);  -- Sélectionne les genres NON attribués au film

SELECT id_film, id_genre, intitule_genre FROM t_genre_film INNER JOIN t_film ON t_film.id_film = t_genre_film.fk_film INNER JOIN t_genre ON t_genre.id_genre = t_genre_film.fk_genre WHERE id_film = %(value_id_film_selected)s;  -- Sélectionne les genres déjà attribués au film

INSERT INTO t_genre_film (id_genre_film, fk_genre, fk_film) VALUES (NULL, %(value_fk_genre)s, %(value_fk_film)s);  -- Ajoute une nouvelle association entre un film et un genre

DELETE FROM t_genre_film WHERE fk_genre = %(value_fk_genre)s AND fk_film = %(value_fk_film)s;  -- Retire une association film/genre


-- STOCK

SELECT DAY(m.`date`) AS jour, m.type_action, COALESCE(SUM(m.quantite * p.prix), 0) AS montant FROM t_mouvement m INNER JOIN t_produit p ON m.fk_produit = p.id_produit WHERE YEAR(m.`date`) = %(year)s AND MONTH(m.`date`) = %(month)s AND m.type_action IN ('DEPOT', 'RETRAIT') GROUP BY DAY(m.`date`), m.type_action ORDER BY jour ASC;  -- Calcule les totaux journaliers (dépenses/bénéfices) pour un mois donné

SELECT p.id_produit, p.`type` AS type_produit, t.taille AS taille_lib, m.nom AS marque_lib, mo.annee AS annee_produit, p.prix, p.quantite_stock FROM t_produit p LEFT JOIN t_modele mo ON p.fk_modele = mo.id_modele LEFT JOIN t_taille t ON p.fk_taille = t.id_taille LEFT JOIN t_marque m ON p.fk_marque = m.id_marque ORDER BY p.id_produit DESC;  -- Sélectionne la liste enrichie des produits (marque, modèle, taille)

SELECT COUNT(*) AS n FROM t_session;  -- Compte le nombre total de sessions

SELECT id_session, nom, prenom FROM t_session ORDER BY id_session DESC;  -- Sélectionne toutes les sessions (sans le mot de passe)

SELECT id_session, nom, prenom, mot_de_passe FROM t_session WHERE id_session = %(id)s;  -- Sélectionne une session par son id

SELECT id_session, nom, prenom, mot_de_passe FROM t_session WHERE mot_de_passe = %(mdp)s;  -- Sélectionne les sessions correspondant à un mot de passe (login)

SELECT c.id_connexion, c.date_debut, c.date_fin, CONCAT(s.prenom, ' ', s.nom) AS session_lib FROM t_connexion c INNER JOIN t_session s ON c.fk_session = s.id_session ORDER BY c.id_connexion DESC;  -- Sélectionne la liste des connexions enrichie avec la session

SELECT id_taille, taille FROM t_taille ORDER BY id_taille DESC;  -- Sélectionne toutes les tailles

SELECT p.*, ma.nom AS marque_nom, mo.nom AS modele_nom, mo.annee AS modele_annee, t.taille AS taille_lib FROM t_produit p LEFT JOIN t_marque ma ON p.fk_marque = ma.id_marque LEFT JOIN t_modele mo ON p.fk_modele = mo.id_modele LEFT JOIN t_taille t ON p.fk_taille = t.id_taille WHERE p.id_produit = %(pk)s;  -- Sélectionne un produit avec marque, modèle et taille pour pré-remplir le formulaire

SELECT id_marque FROM t_marque WHERE nom = %(nom)s;  -- Sélectionne une marque par son nom (pour éviter les doublons)

INSERT INTO t_marque (nom) VALUES (%(nom)s);  -- Ajoute une nouvelle marque

SELECT LAST_INSERT_ID() AS id;  -- Récupère l'id auto-incrémenté généré par le dernier INSERT

SELECT id_modele FROM t_modele WHERE nom = %(nom)s AND annee = %(annee)s AND fk_marque <=> %(marque_id)s;  -- Sélectionne un modèle existant (clé fonctionnelle nom+année+marque)

INSERT INTO t_modele (fk_marque, nom, annee) VALUES (%(marque_id)s, %(nom)s, %(annee)s);  -- Ajoute un nouveau modèle

SELECT id_taille FROM t_taille WHERE taille = %(taille)s;  -- Sélectionne une taille par son libellé

INSERT INTO t_taille (taille) VALUES (%(taille)s);  -- Ajoute une nouvelle taille

INSERT INTO t_produit (fk_marque, fk_modele, fk_taille, `type`, prix, quantite_stock) VALUES (%(fk_marque)s, %(fk_modele)s, %(fk_taille)s, %(type)s, %(prix)s, %(quantite_stock)s);  -- Ajoute un nouveau produit (formulaire stock_admin)

UPDATE t_produit SET fk_marque = %(fk_marque)s, fk_modele = %(fk_modele)s, fk_taille = %(fk_taille)s, `type` = %(type)s, prix = %(prix)s, quantite_stock = %(quantite_stock)s WHERE id_produit = %(pk)s;  -- Modifie un produit (formulaire stock_admin)

INSERT INTO t_session (nom, prenom, mot_de_passe) VALUES (%(nom)s, %(prenom)s, %(mot_de_passe)s);  -- Ajoute une nouvelle session

UPDATE t_session SET nom = %(nom)s, prenom = %(prenom)s, mot_de_passe = %(mot_de_passe)s WHERE id_session = %(pk)s;  -- Modifie une session existante

SELECT id_marque, nom FROM t_marque ORDER BY id_marque ASC;  -- Sélectionne les choix possibles pour une liste déroulante de clé étrangère

DELETE FROM t_marque WHERE id_marque = %(pk)s;  -- Supprime une ligne par sa clé primaire (suppression générique)

-- TABLE INTERMEDIAIRE PRODUIT 

INSERT INTO t_link_produit_taille (fk_produit, fk_taille) VALUES (%(fk_produit)s, %(fk_taille)s);  -- Ajoute une association produit/taille

SELECT l.fk_produit, p.`type` AS produit_nom, l.fk_taille, t.taille AS taille_lib FROM t_link_produit_taille l INNER JOIN t_produit p ON l.fk_produit = p.id_produit INNER JOIN t_taille t ON l.fk_taille = t.id_taille ORDER BY l.fk_produit DESC, l.fk_taille DESC;  -- Sélectionne la liste des associations produit/taille avec leurs libellés

DELETE FROM t_link_produit_taille WHERE fk_produit = %(fk_produit)s AND fk_taille = %(fk_taille)s;  -- Supprime une association produit/taille
