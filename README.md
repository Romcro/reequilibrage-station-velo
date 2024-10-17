# Rééquilibrage des Stations de Vélo

Ce projet est une application web interactive affichant une carte des trajets entre différentes stations de vélos pour aider à équilibrer les vélos dans une ville donnée.

## Fonctionnalités

- **Visualisation sur carte** : Affichage des trajets de vélo et camion entre les stations.
- **Données dynamiques** : Possibilité d'actualiser les données affichées.
- **Interactivité** : Choix des trajets à afficher (vélo ou camion) via des boutons interactifs.

## Technologies utilisées

- **HTML5 / CSS3** : Structure et style de l'application.
- **JavaScript / jQuery** : Gestion des interactions et du chargement des données JSON.
- **Leaflet.js** : Bibliothèque de cartographie pour l'affichage des trajets sur la carte.
- **Font Awesome** : Icônes utilisées dans l'interface utilisateur.

## Installation

1. Clonez le dépôt sur votre machine locale :

   ```bash
   git clone https://github.com/Romcro/reequilibrage-station-velo.git
   ```

2. Naviguez dans le répertoire du projet :

   ```bash
   cd reequilibrage-station-velo
   ```

3. Ouvrez `index.html` dans votre navigateur pour visualiser l'application.

## Utilisation

- **Affichage de la carte** : La carte se centre sur la ville définie par défaut (coordonnées : Nancy, France).
- **Affichage des trajets** : Cliquez sur les boutons vélo ou camion pour afficher les trajets correspondants. Vous pouvez également actualiser les données avec le bouton **Actualiser**.

## Problèmes potentiels

Si vous hébergez cette application sur **GitHub Pages** et rencontrez des problèmes de chargement des données JSON, cela peut être dû à des restrictions CORS (Cross-Origin Resource Sharing). Assurez-vous que les fichiers JSON sont bien accessibles via un serveur public.

## Contribution

Les contributions sont les bienvenues. Pour proposer des améliorations ou des corrections, veuillez créer une "issue" ou soumettre une "pull request".

