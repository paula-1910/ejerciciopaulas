import networkx as nx
import matplotlib.pyplot as plt

# PRÁCTICA AVANZADA: SMARTCOFFEE MULTICAFETERÍAS

def practica_smartcoffee_avanzada():
    # Crear ubicaciones (3 cafeterías + 5 clientes)
    cafeterias = ["Cafetería Norte", "Cafetería Centro", "Cafetería Sur"]
    clientes = ["Cliente A", "Cliente B", "Cliente C", "Cliente D", "Cliente E"]

    # Rutas con distancias (simuladas en km)
    rutas = [
        ("Cafetería Norte", "Cliente A", 4),
        ("Cafetería Norte", "Cliente B", 6),
        ("Cafetería Centro", "Cliente B", 3),
        ("Cafetería Centro", "Cliente C", 4),
        ("Cafetería Centro", "Cliente D", 5),
        ("Cafetería Sur", "Cliente D", 3),
        ("Cafetería Sur", "Cliente E", 4),
        ("Cliente A", "Cliente B", 2),
        ("Cliente B", "Cliente C", 3),
        ("Cliente C", "Cliente D", 4),
        ("Cliente D", "Cliente E", 5),
    ]

    # Construir grafo
    G = nx.Graph()
    G.add_weighted_edges_from(rutas)

    # Determinar qué cafetería atiende a qué cliente (por menor distancia)
    asignaciones = {}
    for cliente in clientes:
        mejor_cafeteria = None
        menor_distancia = float("inf")
        for cafe in cafeterias:
            try:
                distancia = nx.shortest_path_length(G, cafe, cliente, weight="weight")
                if distancia < menor_distancia:
                    menor_distancia = distancia
                    mejor_cafeteria = cafe
            except nx.NetworkXNoPath:
                continue
        asignaciones[cliente] = (mejor_cafeteria, menor_distancia)

    print("=== Asignación de clientes a cafeterías ===")
    for cliente, (cafe, dist) in asignaciones.items():
        print(f"{cliente} ← {cafe} ({dist} km)")

    # Calcular y mostrar camino más corto de cada cafetería a sus clientes
    print("\n=== Rutas más cortas ===")
    rutas_cortas = {}
    for cliente, (cafe, _) in asignaciones.items():
        camino = nx.shortest_path(G, cafe, cliente, weight="weight")
        rutas_cortas[(cafe, cliente)] = camino
        print(f"{cafe} → {cliente}: {' -> '.join(camino)}")

    # BONUS: Visualización
    pos = nx.spring_layout(G, seed=42)
    plt.figure(figsize=(10, 8))

    # Dibujar todo el grafo
    nx.draw(G, pos, with_labels=True, node_color="lightblue", node_size=1200, font_size=9)
    nx.draw_networkx_edge_labels(G, pos, edge_labels=nx.get_edge_attributes(G, 'weight'))

    # Colorear cafeterías y clientes
    nx.draw_networkx_nodes(G, pos, nodelist=cafeterias, node_color="orange", node_size=1300)
    nx.draw_networkx_nodes(G, pos, nodelist=clientes, node_color="lightgreen", node_size=1100)

    # Colorear rutas más cortas
    for (cafe, cliente), camino in rutas_cortas.items():
        edges_path = list(zip(camino[:-1], camino[1:]))
        nx.draw_networkx_edges(G, pos, edgelist=edges_path, edge_color="red", width=3)

    plt.title("SmartCoffee: rutas más cortas por cafetería")
    plt.show()

    # Optimización del reparto (concepto)
    print("\n=== Optimización del reparto ===")
    print("Cada cafetería entregará a sus clientes asignados por menor distancia.")
    print("Para optimizar rutas múltiples, se puede usar un algoritmo tipo TSP (Traveling Salesman Problem).")

    # Ejemplo simple: cafetería centro entrega a sus clientes de forma óptima
    cafe = "Cafetería Centro"
    clientes_centro = [c for c, (caf, _) in asignaciones.items() if caf == cafe]

    if len(clientes_centro) > 1:
        subgrafo = G.subgraph([cafe] + clientes_centro)
        mejor_ruta = nx.approximation.traveling_salesman_problem(subgrafo, cycle=False, weight="weight")
        print(f"Ruta optimizada para {cafe}: {' -> '.join(mejor_ruta)}")
    else:
        print(f"{cafe} tiene un solo cliente asignado.")



# EJECUCIÓN
if __name__ == "__main__":
    print("\n=== Práctica avanzada: SmartCoffee multicafeterías ===\n")
    practica_smartcoffee_avanzada()
