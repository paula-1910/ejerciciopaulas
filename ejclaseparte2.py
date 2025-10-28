import networkx as nx
import matplotlib.pyplot as plt
import random


# SMARTCOFFEE: MULTICAFETERÍAS + PEDIDOS MÚLTIPLES


def practica_smartcoffee_pedidos():
    # Crear ubicaciones (3 cafeterías + 6 clientes)
    cafeterias = ["Cafetería Norte", "Cafetería Centro", "Cafetería Sur"]
    clientes = ["Cliente A", "Cliente B", "Cliente C", "Cliente D", "Cliente E", "Cliente F"]

    # Rutas con distancias (en km)
    rutas = [
        ("Cafetería Norte", "Cliente A", 4),
        ("Cafetería Norte", "Cliente B", 6),
        ("Cafetería Centro", "Cliente B", 3),
        ("Cafetería Centro", "Cliente C", 4),
        ("Cafetería Centro", "Cliente D", 5),
        ("Cafetería Sur", "Cliente D", 3),
        ("Cafetería Sur", "Cliente E", 4),
        ("Cafetería Sur", "Cliente F", 6),
        ("Cliente A", "Cliente B", 2),
        ("Cliente B", "Cliente C", 3),
        ("Cliente C", "Cliente D", 4),
        ("Cliente D", "Cliente E", 5),
        ("Cliente E", "Cliente F", 2),
    ]

    # Construir grafo
    G = nx.Graph()
    G.add_weighted_edges_from(rutas)

    
    # Simular varios pedidos
    
    pedidos = []
    for i in range(random.randint(5, 10)):
        cliente = random.choice(clientes)
        producto = random.choice(["Café Latte", "Capuccino", "Croissant", "Muffin"])
        pedidos.append({"id": i + 1, "cliente": cliente, "producto": producto})
    print("\n=== Pedidos generados ===")
    for p in pedidos:
        print(f"Pedido #{p['id']}: {p['producto']} para {p['cliente']}")

    
    # Asignar pedidos a la cafetería más cercana
    
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
        if mejor_cafeteria:
            asignaciones[cliente] = (mejor_cafeteria, menor_distancia)

    print("\n=== Asignación de clientes a cafeterías ===")
    for cliente, (cafe, dist) in asignaciones.items():
        print(f"{cliente} ← {cafe} ({dist} km)")

    # Agrupar pedidos por cafetería
    
    pedidos_por_cafeteria = {cafe: [] for cafe in cafeterias}
    for pedido in pedidos:
        cliente = pedido["cliente"]
        if cliente in asignaciones:
            cafe_asignada = asignaciones[cliente][0]
            pedidos_por_cafeteria[cafe_asignada].append(pedido)

    
    # Calcular rutas más cortas y optimizadas
    
    rutas_optimizadas = {}
    print("\n=== Optimización del reparto por cafetería ===")
    for cafe, pedidos_cafe in pedidos_por_cafeteria.items():
        if not pedidos_cafe:
            print(f"{cafe} → No tiene pedidos pendientes.")
            continue

        clientes_destino = list({p["cliente"] for p in pedidos_cafe})
        print(f"\n {cafe} entregará a: {', '.join(clientes_destino)}")

        # Subgrafo con cafetería + clientes asignados
        subgrafo = G.subgraph([cafe] + clientes_destino)
        mejor_ruta = nx.approximation.traveling_salesman_problem(subgrafo, cycle=False, weight="weight")

        rutas_optimizadas[cafe] = mejor_ruta
        print(f"Ruta óptima: {' -> '.join(mejor_ruta)}")

    
    # Visualización del grafo
    
    pos = nx.spring_layout(G, seed=42)
    plt.figure(figsize=(11, 8))
    nx.draw(G, pos, with_labels=True, node_color="lightblue", node_size=1200, font_size=9)
    nx.draw_networkx_edge_labels(G, pos, edge_labels=nx.get_edge_attributes(G, "weight"))

    # Colorear cafeterías y clientes
    nx.draw_networkx_nodes(G, pos, nodelist=cafeterias, node_color="orange", node_size=1300)
    nx.draw_networkx_nodes(G, pos, nodelist=clientes, node_color="lightgreen", node_size=1100)

    # Dibujar rutas óptimas (una por cafetería)
    colores = ["red", "blue", "purple"]
    for i, (cafe, ruta) in enumerate(rutas_optimizadas.items()):
        edges_path = list(zip(ruta[:-1], ruta[1:]))
        nx.draw_networkx_edges(G, pos, edgelist=edges_path, edge_color=colores[i % len(colores)], width=3)

    plt.title("SmartCoffee: rutas óptimas de reparto por cafetería")
    plt.show()



# EJECUCIÓN

if __name__ == "__main__":
    print("\n=== SmartCoffee: Optimización de pedidos múltiples ===\n")
    practica_smartcoffee_pedidos()
