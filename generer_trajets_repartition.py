import requests
import networkx as nx
import osmnx as ox
import json
import os
import time

# Fonction pour appeler l'API JCDecaux et récupérer les stations en temps réel
def appeler_api_jcdecaux(api_key, contract_name):
    url = f"https://api.jcdecaux.com/vls/v1/stations?contract={contract_name}&apiKey={api_key}"

    try:
        response = requests.get(url)
        if response.status_code == 200:
            print(f"Stations récupérées avec succès : {len(response.json())} stations trouvées.")
            return response.json()  # Retourner les données au format JSON
        else:
            print(f"Erreur {response.status_code} : {response.text}")
            return None
    except Exception as e:
        print(f"Une erreur s'est produite lors de l'appel à l'API : {e}")
        return None

# Fonction pour définir la couleur et l'icône en fonction du taux d'occupation des vélos
def definir_couleur_station(available_bikes, bike_stands, status):
    total_places = available_bikes + bike_stands

    # Si la station est fermée ou en travaux
    if status == "CLOSED":
        return 'gray', '⚠️'  # Icône travaux
    if total_places == 0:
        return 'gray', '❓'  # Icône sans données

    taux_occupation = available_bikes / total_places
    if taux_occupation < 0.25:
        return 'red', '🔴'  # Moins de 25% des places occupées
    elif 0.25 <= taux_occupation < 0.5:
        return 'orange', '🟠'  # Entre 25% et 50% des places occupées
    else:
        return 'green', '🟢'  # Plus de 50% des places occupées

# Fonction pour identifier les stations sources (vertes) et cibles (rouges/grises)
def identifier_stations(stations):
    sources = []  # Stations vertes (sources de vélos)
    cibles = []   # Stations rouges ou grises (destinataires de vélos)

    for station in stations:
        available_bikes = station['available_bikes']
        available_bike_stands = station['available_bike_stands']
        status = station['status']
        
        # Utiliser la nouvelle fonction pour la couleur et l'icône
        couleur, icone = definir_couleur_station(available_bikes, available_bike_stands, status)

        # Ajouter la couleur et l'icône dans la station
        station['couleur'] = couleur
        station['icone'] = icone

        if couleur == 'green':
            sources.append(station)
        elif couleur in ['red', 'orange', 'gray']:
            cibles.append(station)

    print(f"Stations sources : {len(sources)}, Stations cibles : {len(cibles)}")
    return sources, cibles

# Fonction pour récupérer les réseaux routiers (pour camions) ou cyclables (pour vélos)
def recuperer_reseau(place_name="Nancy, France", mode_transport='velo'):
    network_type = 'bike' if mode_transport == 'velo' else 'drive'
    try:
        graph = ox.graph_from_place(place_name, network_type=network_type)
        print(f"Réseau {network_type} récupéré avec succès.")
        return graph
    except Exception as e:
        print(f"Erreur lors de la récupération du réseau {network_type}: {e}")
        return None

# Fonction pour générer les trajets entre les stations sources et cibles pour vélo et camion
def generer_trajets_repartition(sources, cibles, graph_velo, graph_camion):
    trajets_velo = []
    trajets_camion = []

    for cible in cibles:
        if sources:
            source = sources.pop(0)  # Prendre une source
            lat_source, lng_source = source['position']['lat'], source['position']['lng']
            lat_cible, lng_cible = cible['position']['lat'], cible['position']['lng']

            # Générer le trajet pour le vélo (piste cyclable si dispo, route sinon)
            try:
                # Essayer d'abord avec le réseau cyclable
                node_source = ox.distance.nearest_nodes(graph_velo, lng_source, lat_source)
                node_cible = ox.distance.nearest_nodes(graph_velo, lng_cible, lat_cible)

                # Calculer le plus court chemin dans le graphe cyclable
                shortest_path = nx.shortest_path(graph_velo, node_source, node_cible, weight='length')
                path_coords = [(graph_velo.nodes[node]['y'], graph_velo.nodes[node]['x']) for node in shortest_path]
                
                # Ajouter le trajet vélo si réussi
                trajets_velo.append({
                    'source': source['name'],
                    'destination': cible['name'],
                    'source_color': source['couleur'],
                    'destination_color': cible['couleur'],
                    'source_icon': source['icone'],
                    'destination_icon': cible['icone'],
                    'path': path_coords,
                    'mode_transport': 'velo'  # Trajet en vélo
                })

            except (nx.NetworkXNoPath, KeyError):
                # Si le trajet cyclable échoue, basculer sur la route
                try:
                    print(f"Bascule sur le réseau routier pour le trajet vélo entre {source['name']} et {cible['name']}")
                    node_source = ox.distance.nearest_nodes(graph_camion, lng_source, lat_source)
                    node_cible = ox.distance.nearest_nodes(graph_camion, lng_cible, lat_cible)

                    # Calculer le plus court chemin dans le graphe routier
                    shortest_path = nx.shortest_path(graph_camion, node_source, node_cible, weight='length')
                    path_coords = [(graph_camion.nodes[node]['y'], graph_camion.nodes[node]['x']) for node in shortest_path]

                    # Ajouter le trajet routier comme version vélo si pas de piste cyclable
                    trajets_velo.append({
                        'source': source['name'],
                        'destination': cible['name'],
                        'source_color': source['couleur'],
                        'destination_color': cible['couleur'],
                        'source_icon': source['icone'],
                        'destination_icon': cible['icone'],
                        'path': path_coords,
                        'mode_transport': 'velo'  # Trajet vélo sur route
                    })

                except (nx.NetworkXNoPath, KeyError):
                    print(f"Aucun chemin trouvé pour le trajet vélo entre {source['name']} et {cible['name']}")

            # Générer le trajet camion sur le réseau routier
            try:
                print(f"Génération du trajet camion entre {source['name']} et {cible['name']}")
                node_source = ox.distance.nearest_nodes(graph_camion, lng_source, lat_source)
                node_cible = ox.distance.nearest_nodes(graph_camion, lng_cible, lat_cible)

                # Calculer le plus court chemin dans le graphe routier
                shortest_path = nx.shortest_path(graph_camion, node_source, node_cible, weight='length')
                path_coords = [(graph_camion.nodes[node]['y'], graph_camion.nodes[node]['x']) for node in shortest_path]

                # Ajouter le trajet camion
                trajets_camion.append({
                    'source': source['name'],
                    'destination': cible['name'],
                    'source_color': source['couleur'],
                    'destination_color': cible['couleur'],
                    'source_icon': source['icone'],
                    'destination_icon': cible['icone'],
                    'path': path_coords,
                    'mode_transport': 'camion'  # Trajet en camion
                })

            except (nx.NetworkXNoPath, KeyError):
                print(f"Aucun chemin trouvé pour le trajet camion entre {source['name']} et {cible['name']}")

    print(f"{len(trajets_velo)} trajets vélo générés, {len(trajets_camion)} trajets camion générés.")
    return trajets_velo, trajets_camion

# Fonction pour générer un fichier JSON avec les trajets de répartition
def generer_json_trajets(stations, trajets_velo, trajets_camion, fichier_json='trajets_repartition.json'):
    with open(fichier_json, 'w') as file:
        json.dump({
            'stations': stations,
            'trajets_velo': trajets_velo,
            'trajets_camion': trajets_camion
        }, file, indent=4)
    print(f"Fichier JSON des trajets et des stations généré sous {fichier_json}")

# Fonction pour appeler la génération des données
def generer_donnees():
    # Clé API et contrat pour l'API JCDecaux
    api_key = "7967e55f58492463189c6b2d17ccb21343a559b3"
    contract_name = "nancy"

    # Appeler l'API JCDecaux pour récupérer les stations
    stations = appeler_api_jcdecaux(api_key, contract_name)

    # Vérifier si les stations ont été correctement récupérées
    if stations:
        print(f"{len(stations)} stations récupérées depuis l'API JCDecaux.")
        
        # Identifier les sources (stations vertes) et cibles (stations rouges ou grises)
        sources, cibles = identifier_stations(stations)

        # Récupérer les réseaux
        graph_velo = recuperer_reseau(mode_transport='velo')  # Réseau cyclable
        graph_camion = recuperer_reseau(mode_transport='drive')  # Réseau routier

        if graph_velo and graph_camion:
            # Générer les trajets pour vélo et camion
            trajets_velo, trajets_camion = generer_trajets_repartition(sources[:], cibles[:], graph_velo, graph_camion)

            # Générer un fichier JSON des trajets
            generer_json_trajets(stations, trajets_velo, trajets_camion)
        else:
            print("Erreur lors de la récupération des réseaux de transport.")
    else:
        print("Erreur : Impossible de récupérer les stations depuis l'API JCDecaux.")

# Boucle principale pour régénérer toutes les 2 minutes
def main():
    try:
        while True:
            print("Début de la génération des données.")
            generer_donnees()
            print("Données générées. Attente de 2 minutes avant la prochaine exécution.")
            time.sleep(120)  # Attendre 2 minutes (120 secondes) avant de régénérer
    except KeyboardInterrupt:
        print("Processus interrompu par l'utilisateur.")

# Exécution
if __name__ == "__main__":
    main()
