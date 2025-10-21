from datetime import datetime
from typing import List

# ----------------------------
# Clase Cliente
# ----------------------------
class Cliente:
    def __init__(self, id_cliente: int, nombre: str, email: str, puntos_fidelidad: int = 0):
        self.id_cliente = id_cliente
        self.nombre = nombre
        self.email = email
        self.puntos_fidelidad = puntos_fidelidad
        self.pedidos: List['Pedido'] = []

    def realizar_pedido(self, pedido: 'Pedido'):
        self.pedidos.append(pedido)

    def __str__(self):
        return f"Cliente({self.nombre}, {self.email}, Puntos: {self.puntos_fidelidad})"


# ----------------------------
# Clase Empleado
# ----------------------------
class Empleado:
    def __init__(self, id_empleado: int, nombre: str, rol: str, turno: str):
        self.id_empleado = id_empleado
        self.nombre = nombre
        self.rol = rol
        self.turno = turno
        self.pedidos_atendidos: List['Pedido'] = []

    def atender_pedido(self, pedido: 'Pedido'):
        self.pedidos_atendidos.append(pedido)

    def __str__(self):
        return f"Empleado({self.nombre}, Rol: {self.rol}, Turno: {self.turno})"


# ----------------------------
# Clase Producto
# ----------------------------
class Producto:
    def __init__(self, id_producto: int, nombre: str, tipo: str, precio: float):
        self.id_producto = id_producto
        self.nombre = nombre
        self.tipo = tipo
        self.precio = precio

    def __str__(self):
        return f"Producto({self.nombre}, {self.tipo}, {self.precio:.2f}€)"


# ----------------------------
# Clase intermedia PedidoProducto (N:M)
# ----------------------------
class PedidoProducto:
    def __init__(self, producto: Producto, cantidad: int):
        self.producto = producto
        self.cantidad = cantidad

    def subtotal(self) -> float:
        return self.producto.precio * self.cantidad

    def __str__(self):
        return f"{self.producto.nombre} x{self.cantidad} = {self.subtotal():.2f}€"


# ----------------------------
# Clase Pedido
# ----------------------------
class Pedido:
    def __init__(self, id_pedido: int, cliente: Cliente, empleado: Empleado):
        self.id_pedido = id_pedido
        self.fecha = datetime.now()
        self.cliente = cliente
        self.empleado = empleado
        self.productos: List[PedidoProducto] = []

        # Asociar relaciones bidireccionales
        cliente.realizar_pedido(self)
        empleado.atender_pedido(self)

    def agregar_producto(self, producto: Producto, cantidad: int):
        self.productos.append(PedidoProducto(producto, cantidad))

    def total(self) -> float:
        return sum(item.subtotal() for item in self.productos)

    def __str__(self):
        productos_str = "\n  ".join(str(p) for p in self.productos)
        return (
            f"Pedido #{self.id_pedido} ({self.fecha.strftime('%Y-%m-%d %H:%M')})\n"
            f"Cliente: {self.cliente.nombre}\n"
            f"Empleado: {self.empleado.nombre}\n"
            f"Productos:\n  {productos_str}\n"
            f"Total: {self.total():.2f}€"
        )


# ----------------------------
# Ejemplo de uso
# ----------------------------
if __name__ == "__main__":
    # Crear objetos
    cliente1 = Cliente(1, "Laura Gómez", "laura@example.com", 120)
    empleado1 = Empleado(1, "Carlos Ruiz", "Barista", "Mañana")

    cafe = Producto(1, "Café Latte", "Bebida", 2.50)
    croissant = Producto(2, "Croissant", "Comida", 1.80)

    pedido1 = Pedido(101, cliente1, empleado1)
    pedido1.agregar_producto(cafe, 2)
    pedido1.agregar_producto(croissant, 1)

    print(pedido1)
