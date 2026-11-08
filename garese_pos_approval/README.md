# GARESE POS Approvals (`garese_pos_approval`) — Odoo 17.0 — version 17.0.1.0.0

Remplace `garese_pos_secure_cash`. Dépend de `garese_pos` (>= 17.0.1.7.2).

Dans Paramètres du point de vente > bloc « Approbations des responsables » (par caisse) :
remises, changements de prix, remboursements, annulations (ligne ou commande). Le caissier fait saisir
à un responsable son mot de passe Odoo sur la caisse. Les responsables ne sont pas concernés.

- Remises et remboursements : contrôlés aussi par le serveur à l'enregistrement de la commande
  (une caisse modifiée ne peut pas les contourner).
- Changements de prix et annulations : contrôlés sur la caisse seulement (le serveur ne voit pas
  une ligne supprimée avant l'enregistrement).
- Journal : Point de vente > Rapports > Approbations des responsables (qui, quand, quelle commande).
- Clôture, commandes payées masquées, totaux masqués : voir `garese_pos` 1.7.x (inchangés).

Licence OPL-1 — © GARESE.
