# smartcoffee_full_practice.py
# Versión extendida del script SmartCoffee para cubrir:
# - carga/filtrado de pedidos por período
# - construir grafo solo con clientes activos
# - Bellman-Ford por cafetería (rutas, costes, detección de ciclos negativos)
# - Floyd-Warshall (matriz global de distancias)
# - análisis: cliente más alejado, cliente con más pedidos, pares inusuales (z-score)
# - sugerencias para reorganizar rutas / posible nuevo punto de entrega
#
# Requiere: networkx, matplotlib, numpy, scipy (opcional)
# Ejecutar: python smartcoffee_full_practice.py

import networkx as nx
import matplotlib.pyplot as plt
import random
from datetime import datetime, timedelta
from collections import Counter, defaultdict
import statistics
import math

random.seed(42)

# -------------------------
# Datos base (tus nodos/edges originales)
# -------------------------
cafeterias = ["Cafetería Norte", "Cafetería Centro", "Cafetería Sur"]
clientes = ["Cliente A", "Cliente B", "Cliente C", "Cliente D", "Cliente E", "Cliente F"]

# Rutas con distancias (en km) - grafo dirigido implícitamente (usamos como no-dirigido y también añadimos ambos sentidos)
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

def construir_grafo_base(rutas):
    G = nx.DiGraph()  # uso dirigido: dejamos la posibilidad de pesos distintos por sentido
    for u, v, w in rutas:
        G.add_edge(u, v, weight=float(w))
        G.add_edge(v, u, weight=float(w))  # añadir opuesto con mismo peso (simétrico)
    return G

# -------------------------
# 1) Simular / cargar pedidos y filtrar por periodo
# -------------------------
def simular_pedidos(num_min=5, num_max=10, start_dt=None):
    """
    Genera pedidos con timestamps para la demo.
    Cada pedido: id, cliente, producto, datetime
    """
    productos = ["Café Latte", "Capuccino", "Croissant", "Muffin", "Americano"]
    pedidos = []
    n = random.randint(num_min, num_max)
    now = start_dt or datetime.now()
    for i in range(n):
        # repartir timestamps en los últimos 7 días
        dt = now - timedelta(days=random.random()*7)
        pedidos.append({
            "id": i+1,
            "cliente": random.choice(clientes),
            "producto": random.choice(productos),
            "datetime": dt
        })
    return pedidos

def filtrar_pedidos_periodo(pedidos, start_dt, end_dt):
    return [p for p in pedidos if start_dt <= p["datetime"] < end_dt]

# -------------------------
# 2) Construir grafo 'activo' con solo clientes del periodo
# -------------------------
def grafo_con_clientes_activos(G_base, pedidos_periodo):
    clientes_activos = sorted({p["cliente"] for p in pedidos_periodo})
    # Tomamos todos los cafeterías + clientes activos como vértices; mantenemos aristas entre ellos si existen
    G = nx.DiGraph()
    # Añadir nodos (cafeterías siempre incluidas)
    for c in cafeterias:
        G.add_node(c)
    for cl in clientes_activos:
        G.add_node(cl)
    # Añadir aristas del grafo base que conecten nodos presentes
    for u, v, data in G_base.edges(data=True):
        if u in G.nodes and v in G.nodes:
            G.add_edge(u, v, **data)
    return G, clientes_activos

# -------------------------
# 3) Bellman-Ford por cafetería (rutas, costes, detección de ciclos negativos)
# -------------------------
def bellman_ford_por_cafeteria(G_activo, cafeterias, clientes_activos):
    """
    Para cada cafetería, calcula Bellman-Ford (rutas y costes) hacia cada cliente activo.
    Detecta ciclos negativos en el subgrafo alcanzable.
    Devuelve dict con rutas y coste por (cafe -> cliente) y lista de cafés con ciclos negativos detectados.
    """
    resultados = {}
    cafes_con_ciclo_negativo = set()
    for cafe in cafeterias:
        if cafe not in G_activo:
            continue
        # detecta ciclo negativo en todo el grafo alcanzable desde cafe
        try:
            # networkx tiene función para detectar ciclo negativo global en direccionado
            # hay que comprobar solo la componente alcanzable desde cafe
            reachable = nx.descendants(G_activo, cafe) | {cafe}
            sub = G_activo.subgraph(reachable)
            has_neg = nx.negative_edge_cycle(sub, weight="weight")
        except Exception:
            has_neg = False
        if has_neg:
            cafes_con_ciclo_negativo.add(cafe)

        # calcular rutas y distancias con Bellman-Ford (NetworkX)
        try:
            # obtiene distancias y rutas
            dist = nx.single_source_bellman_ford_path_length(G_activo, cafe, weight="weight")
            paths = nx.single_source_bellman_ford_path(G_activo, cafe, weight="weight")
        except Exception:
            # fallback a Dijkstra si no hay pesos negativos pero BF falla
            dist = nx.single_source_dijkstra_path_length(G_activo, cafe, weight="weight")
            paths = nx.single_source_dijkstra_path(G_activo, cafe, weight="weight")

        resultados[cafe] = {}
        for cl in clientes_activos:
            d = dist.get(cl, math.inf)
            ruta = paths.get(cl, None)
            resultados[cafe][cl] = {"distancia": d, "ruta": ruta}
    return resultados, sorted(list(cafes_con_ciclo_negativo))

# -------------------------
# 4) Floyd-Warshall global (matriz de distancias entre todas ubicaciones activas)
# -------------------------
def matriz_floyd_warshall(G_activo):
    # devuelve un dict-of-dict con distancias mínimas (NetworkX floyd_warshall)
    D = dict(nx.floyd_warshall(G_activo, weight="weight"))
    return D

# -------------------------
# 5) Análisis global y sugerencias
# -------------------------
def analisis_y_sugerencias(D_matrix, pedidos_periodo, clientes_activos):
    """
    - Cliente más alejado (media/distancia mínima desde cafeterías)
    - Cliente con más pedidos
    - Pares con distancia inusualmente grande/pequeña (z-score)
    - Sugerencia: si hay cluster de clientes muy lejanos, proponer abrir nuevo punto en su 'centro'
    """
    # Cliente con más pedidos
    contador = Counter([p["cliente"] for p in pedidos_periodo])
    cliente_mas_pedidos, n_pedidos = contador.most_common(1)[0] if contador else (None, 0)

    # Para cada cliente, calcular la distancia mínima desde cualquier cafetería
    dist_min_desde_cafes = {}
    for cl in clientes_activos:
        # buscar mínimos en matriz para nodos que son cafeterías
        min_dist = math.inf
        for cafe in cafeterias:
            d = D_matrix.get(cafe, {}).get(cl, math.inf)
            if d < min_dist:
                min_dist = d
        dist_min_desde_cafes[cl] = min_dist

    # cliente más alejado (mayor distancia mínima desde cafeterías)
    if dist_min_desde_cafes:
        cliente_mas_alejado = max(dist_min_desde_cafes.items(), key=lambda x: x[1])
    else:
        cliente_mas_alejado = (None, math.inf)

    # Analizar pares con distancias: convertir todas las distancias (u<v para no duplicar)
    pares = []
    nodos = list(D_matrix.keys())
    for i in range(len(nodos)):
        for j in range(i+1, len(nodos)):
            u = nodos[i]; v = nodos[j]
            d = D_matrix[u].get(v, math.inf)
            if math.isfinite(d):
                pares.append((u, v, d))
    # medir z-score de las distancias
    dist_vals = [p[2] for p in pares]
    if len(dist_vals) >= 2:
        mean_d = statistics.mean(dist_vals)
        stdev_d = statistics.pstdev(dist_vals)  # población
        inusuales = []
        for u, v, d in pares:
            if stdev_d == 0:
                z = 0
            else:
                z = (d - mean_d) / stdev_d
            # criterio: |z| > 1.5 para 'inusual' (ajustable)
            if abs(z) > 1.5:
                inusuales.append({"u": u, "v": v, "dist": d, "z": z})
    else:
        inusuales = []

    # Sugerencia simple: si cliente_mas_alejado distancia > umbral -> proponer nuevo punto
    sugerencias = []
    umbral_km = 6.0  # heurístico: si alguien está a >6 km de cualquier café, proponer
    if cliente_mas_alejado[1] != math.inf and cliente_mas_alejado[1] > umbral_km:
        sugerencias.append({
            "tipo": "abrir_nuevo_punto",
            "motivo": f"Cliente {cliente_mas_alejado[0]} está lejos ({cliente_mas_alejado[1]:.2f} km).",
            "propuesta": f"Considerar abrir un punto de entrega cercano a {cliente_mas_alejado[0]} o reorganizar rutas."
        })
    # Si hay grupo de clientes con muchos pedidos y están agrupados (detectar por simple conteo)
    cluster_threshold = 2
    cluster_counts = {cl: contador[cl] for cl in clientes_activos}
    grava = [ (cl, cnt) for cl,cnt in cluster_counts.items() if cnt >= cluster_threshold ]
    if grava:
        sugerencias.append({
            "tipo": "reorganizar_rutas",
            "motivo": f"Clientes con múltiples pedidos en la zona: {grava}",
            "propuesta": "Evaluar rutas conjuntas o pick-up point para agrupar entregas y mejorar eficiencia."
        })

    return {
        "cliente_mas_pedidos": (cliente_mas_pedidos, n_pedidos),
        "cliente_mas_alejado": cliente_mas_alejado,
        "pares_inusuales": inusuales,
        "sugerencias": sugerencias,
        "dist_min_desde_cafes": dist_min_desde_cafes
    }

# -------------------------
# 6) Visualización (grafo + rutas óptimas por cafetería)
# -------------------------
def dibujar_resultados(G_full, rutas_optimizadas, G_activo):
    pos = nx.spring_layout(G_full, seed=42)
    plt.figure(figsize=(11,8))
    # Nodos base: cafeterías y clientes (todos)
    nx.draw_networkx_nodes(G_full, pos, nodelist=cafeterias, node_color="orange", node_size=1200)
    # color clientes (todos en G_full, si algunos no activos quedan igual)
    clientes_all = [n for n in G_full.nodes if n not in cafeterias]
    nx.draw_networkx_nodes(G_full, pos, nodelist=clientes_all, node_color="lightgreen", node_size=1000)
    nx.draw_networkx_labels(G_full, pos, font_size=9)
    nx.draw_networkx_edges(G_full, pos, alpha=0.4)
    nx.draw_networkx_edge_labels(G_full, pos, edge_labels=nx.get_edge_attributes(G_full, "weight"))
    # Resaltar subgrafo activo
    if G_activo is not None:
        nx.draw_networkx_nodes(G_full, pos, nodelist=list(G_activo.nodes), node_size=1400, node_color="none", edgecolors="black", linewidths=1.2)
    # Dibujar rutas optimizadas (si las hay)
    colores = ["red", "blue", "purple", "brown", "cyan"]
    for i, (cafe, ruta) in enumerate(rutas_optimizadas.items()):
        if ruta is None: 
            continue
        edges_path = list(zip(ruta[:-1], ruta[1:])) if len(ruta) >= 2 else []
        nx.draw_networkx_edges(G_full, pos, edgelist=edges_path, edge_color=colores[i % len(colores)], width=3)
    plt.title("SmartCoffee: grafo y rutas optimizadas por cafetería")
    plt.axis("off")
    plt.show()

# -------------------------
# 7) Flujo principal que une todo
# -------------------------
def practica_smartcoffee_pedidos_avanzada():
    print("\n=== SmartCoffee: Optimización avanzada con pedidos reales (simulados) ===\n")
    # construir grafo base
    G_base = construir_grafo_base(rutas)

    # simular pedidos
    pedidos = simular_pedidos(num_min=6, num_max=12, start_dt=datetime.now())
    print("Pedidos simulados (con timestamp):")
    for p in pedidos:
        print(f"  #{p['id']} - {p['producto']} para {p['cliente']} @ {p['datetime'].strftime('%Y-%m-%d %H:%M:%S')}")
    # definir periodo (por ejemplo últimos 7 días)
    ahora = datetime.now()
    hace_7_dias = ahora - timedelta(days=7)
    pedidos_periodo = filtrar_pedidos_periodo(pedidos, hace_7_dias, ahora)
    print(f"\nPedidos considerados en periodo (desde {hace_7_dias.date()} hasta {ahora.date()}): {len(pedidos_periodo)} pedidos")

    # construir grafo activo (solo clientes con pedidos)
    G_activo, clientes_activos = grafo_con_clientes_activos(G_base, pedidos_periodo)
    print(f"Clientes activos en periodo: {clientes_activos}")

    # asignar cada cliente al café más cercano (por shortest path)
    asignaciones = {}
    for cliente in clientes_activos:
        mejor_cafe = None
        menor = math.inf
        for cafe in cafeterias:
            if cafe not in G_activo:
                continue
            try:
                d = nx.shortest_path_length(G_activo, cafe, cliente, weight="weight")
                if d < menor:
                    menor = d
                    mejor_cafe = cafe
            except nx.NetworkXNoPath:
                continue
        if mejor_cafe:
            asignaciones[cliente] = (mejor_cafe, menor)
    print("\nAsignaciones cafetería -> cliente (según grafo activo):")
    for cl, (caf, d) in asignaciones.items():
        print(f"  {cl} <- {caf} ({d:.2f} km)")

    # Bellman-Ford por cafetería
    resultados_bf, cafes_con_ciclo_neg = bellman_ford_por_cafeteria(G_activo, cafeterias, clientes_activos)
    if cafes_con_ciclo_neg:
        print("\nWARNING: Ciclos negativos detectados en cafeterías:", cafes_con_ciclo_neg)
        print("Significado: si hay ciclos negativos, Bellman-Ford no devuelve rutas fiables para todos los nodos alcanzables.")
        print("Cómo gestionarlo: revisar y sanear pesos negativos o restringir cálculo a subgrafo sin ciclos negativos.")
    else:
        print("\nNo se detectaron ciclos negativos en el subgrafo activo.")

    # Mostrar coste/ruta por pedido
    print("\nRutas y costes desde la cafetería asignada para cada pedido:")
    for p in pedidos_periodo:
        cl = p["cliente"]
        # usar la caf asignada si existe
        if cl in asignaciones:
            caf = asignaciones[cl][0]
            ruta_info = resultados_bf.get(caf, {}).get(cl, None)
            if ruta_info:
                d = ruta_info["distancia"]
                ruta = ruta_info["ruta"]
                print(f" Pedido #{p['id']}: {p['producto']} para {cl} <- {caf} | distancia: {d:.2f} km | ruta: {ruta}")
            else:
                print(f" Pedido #{p['id']}: {p['producto']} para {cl} <- {caf} | ruta NO encontrada")
        else:
            print(f" Pedido #{p['id']}: {p['producto']} para {cl} | sin asignación (no conectado)")

    # Floyd-Warshall global sobre nodos activos (cafeterías + clientes activos)
    D = matriz_floyd_warshall(G_activo)
    print("\nMatriz de distancias mínima (parcial; sólo nodos activos):")
    # imprimir algunas distancias relevantes
    for cafe in cafeterias:
        if cafe in D:
            for cl in clientes_activos:
                d = D[cafe].get(cl, math.inf)
                if d < math.inf:
                    print(f"  {cafe} -> {cl}: {d:.2f} km")

    # Análisis y sugerencias
    analisis = analisis_y_sugerencias(D, pedidos_periodo, clientes_activos)
    print("\n--- ANÁLISIS GLOBAL ---")
    print("Cliente con más pedidos:", analisis["cliente_mas_pedidos"])
    print("Cliente más alejado (desde cafeterías):", analisis["cliente_mas_alejado"])
    print("Pares con distancia inusual (z-score):")
    for p in analisis["pares_inusuales"]:
        print(f"  {p['u']} <-> {p['v']}: {p['dist']:.2f} km (z={p['z']:.2f})")
    print("\nSugerencias:")
    for s in analisis["sugerencias"]:
        print(" ", s["tipo"], "-", s["motivo"], "|", s["propuesta"])

    # Rutas optimizadas por cafetería (TSP aproximado) sobre subgrafo (si hay pedidos)
    rutas_optimizadas = {}
    print("\n=== Optimización del reparto por cafetería (TSP aproximado en subgrafo activo) ===")
    for cafe in cafeterias:
        pedidos_cafe = [p for p in pedidos_periodo if asignaciones.get(p["cliente"], (None,))[0] == cafe]
        if not pedidos_cafe:
            print(f" {cafe} → No tiene pedidos pendientes.")
            rutas_optimizadas[cafe] = None
            continue
        clientes_destino = list({p["cliente"] for p in pedidos_cafe})
        subnodes = [cafe] + clientes_destino
        subgrafo = G_activo.subgraph(subnodes).copy()
        # si el subgrafo no está fuertemente conectado para TSP, fallback: ordenar por distancia desde cafe
        try:
            tsp_route = nx.approximation.traveling_salesman_problem(subgrafo, cycle=False, weight="weight")
            rutas_optimizadas[cafe] = tsp_route
            print(f" {cafe} entregará a: {', '.join(clientes_destino)}")
            print(f"  Ruta TSP aproximada: {' -> '.join(tsp_route)}")
        except Exception:
            # fallback simple: ordenar por distancia desde cafe (greedy)
            dist_map = {}
            for cl in clientes_destino:
                try:
                    d = nx.shortest_path_length(subgrafo, cafe, cl, weight="weight")
                except:
                    d = math.inf
                dist_map[cl] = d
            orden = sorted(clientes_destino, key=lambda x: dist_map[x])
            rutas_optimizadas[cafe] = [cafe] + orden
            print(f"  Fallback ruta ordenada por distancia: {' -> '.join([cafe]+orden)}")

    # Dibujar resultados
    dibujar_resultados(G_base, rutas_optimizadas, G_activo)

# -------------------------
# MAIN
# -------------------------
if __name__ == "__main__":
    practica_smartcoffee_pedidos_avanzada()
