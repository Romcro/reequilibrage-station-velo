import requests
import networkx as nx
import osmnx as ox
import json
import time

# Fonction pour appeler l'API JCDecaux et récupérer les stations en temps réel
def appeler_api_jcdecaux(api_key, contract_name):
    url = f"https://api.jcdecaux.com/vls/v1/stations?contract={contract_name}&apiKey={api_key}"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Vérifie si le statut HTTP est 200
        stations = response.json()
        print(f"Stations récupérées avec succès : {len(stations)} stations trouvées.")
        return stations
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de l'appel à l'API JCDecaux : {e}")
        return None

# Fonction pour définir la couleur et l'icône en fonction du taux d'occupation des vélos
def definir_couleur_station(available_bikes, bike_stands, status):
    total_places = available_bikes + bike_stands

    if status == "CLOSED" or total_places == 0:
        return 'gray', '⚠️' if status == "CLOSED" else '❓'

    taux_occupation = available_bikes / total_places
    if taux_occupation < 0.25:
        return 'red', '🔴'
    elif 0.25 <= taux_occupation < 0.5:
        return 'orange', '🟠'
    else:
        return 'green', '🟢'

# Fonction pour identifier les stations sources (vertes) et cibles (rouges/grises)
def identifier_stations(stations):
    sources = []
    cibles = []

    for station in stations:
        available_bikes = station['available_bikes']
        available_bike_stands = station['available_bike_stands']
        status = station['status']

        couleur, icone = definir_couleur_station(available_bikes, available_bike_stands, status)
        station['couleur'] = couleur
        station['icone'] = icone

        if couleur == 'green':
            sources.append(station)
        elif couleur in ['red', 'orange', 'gray']:
            cibles.append(station)

    print(f"Stations sources : {len(sources)}, Stations cibles : {len(cibles)}")
    return sources, cibles

# Fonction pour récupérer le réseau routier ou cyclable
def recuperer_reseau(place_name="Nancy, France", mode_transport='velo'):
    network_type = 'bike' if mode_transport == 'velo' else 'drive'
    try:
        graph = ox.graph_from_place(place_name, network_type=network_type)
        print(f"Réseau {network_type} récupéré avec succès.")
        return graph
    except Exception as e:
        print(f"Erreur lors de la récupération du réseau {network_type}: {e}")
        return None

# Générer les trajets entre les stations
def generer_trajets_repartition(sources, cibles, graph_velo, graph_camion):
    trajets_velo = []
    trajets_camion = []

    for cible in cibles:
        if not sources:
            break

        source = sources.pop(0)
        lat_source, lng_source = source['position']['lat'], source['position']['lng']
        lat_cible, lng_cible = cible['position']['lat'], cible['position']['lng']

        try:
            node_source = ox.distance.nearest_nodes(graph_velo, lng_source, lat_source)
            node_cible = ox.distance.nearest_nodes(graph_velo, lng_cible, lat_cible)
            shortest_path = nx.shortest_path(graph_velo, node_source, node_cible, weight='length')
            path_coords = [(graph_velo.nodes[node]['y'], graph_velo.nodes[node]['x']) for node in shortest_path]
            trajets_velo.append({
                'source': source['name'],
                'destination': cible['name'],
                'path': path_coords,
                'mode_transport': 'velo'
            })
        except Exception:
            print(f"Bascule sur le réseau routier pour le trajet entre {source['name']} et {cible['name']}")

        try:
            node_source = ox.distance.nearest_nodes(graph_camion, lng_source, lat_source)
            node_cible = ox.distance.nearest_nodes(graph_camion, lng_cible, lat_cible)
            shortest_path = nx.shortest_path(graph_camion, node_source, node_cible, weight='length')
            path_coords = [(graph_camion.nodes[node]['y'], graph_camion.nodes[node]['x']) for node in shortest_path]
            trajets_camion.append({
                'source': source['name'],
                'destination': cible['name'],
                'path': path_coords,
                'mode_transport': 'camion'
            })
        except Exception as e:
            print(f"Erreur pour le trajet camion entre {source['name']} et {cible['name']}: {e}")

    print(f"{len(trajets_velo)} trajets vélo générés, {len(trajets_camion)} trajets camion générés.")
    return trajets_velo, trajets_camion

# Générer et sauvegarder les données dans un fichier JSON
def generer_donnees():
    api_key = "88c1597f631e505d9b5fad4e1773fd956b371bf0"
    contract_name = "nancy"

    stations = appeler_api_jcdecaux(api_key, contract_name)

    if stations:
        sources, cibles = identifier_stations(stations)
        graph_velo = recuperer_reseau(mode_transport='velo')
        graph_camion = recuperer_reseau(mode_transport='drive')

        if graph_velo and graph_camion:
            trajets_velo, trajets_camion = generer_trajets_repartition(sources, cibles, graph_velo, graph_camion)

            # Sauvegarder les données dans un fichier JSON
            with open('trajets_repartition.json', 'w') as f:
                json.dump({
                    "stations": stations,
                    "trajets_velo": trajets_velo,
                    "trajets_camion": trajets_camion
                }, f, indent=4)
            print("Données sauvegardées dans 'trajets_repartition.json'.")
        else:
            print("Erreur : Impossible de récupérer les réseaux.")
    else:
        print("Erreur : Impossible de récupérer les stations depuis l'API JCDecaux.")

# Boucle principale
def main():
    try:
        while True:
            print("Début de la génération des données.")
            generer_donnees()
            print("Données générées. Attente de 2 minutes avant la prochaine exécution.")
            time.sleep(120)
    except KeyboardInterrupt:
        print("Processus interrompu par l'utilisateur.")

# Exécution
if __name__ == "__main__":
    main()
