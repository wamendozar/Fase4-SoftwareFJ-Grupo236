# ===============================================================
# SOFTWARE FJ - Sistema de clientes, servicios y reservas (archivo único)
# Programación 213023 - UNAD - Fase 4
# Se ejecuta con:  python software_fj.py
# Fuentes: Van Rossum y Drake (2024), apartado 8; Cuevas Álvarez (2016), pp. 373-385;
# Romano et al. (2019); Mishra (2024).
# ===============================================================
import logging
import os
import re
from abc import ABC, abstractmethod

# >>>>>>>>>> Parte: errores <<<<<<<<<<
# ---------------------------------------------------------------
# errores.py
# Aquí están los errores propios del programa. Cada uno avisa de
# un problema distinto, así sabemos qué falló sin buscar mucho.
# Fuente: Van Rossum y Drake (2024), tutorial de Python, apartado 8 (errores y excepciones).
# ---------------------------------------------------------------


class ErrorFJ(Exception):
    """Error general de Software FJ. Todos los demás salen de este."""


class ClienteInvalido(ErrorFJ):
    """Los datos del cliente no sirven (nombre, correo, teléfono...)."""


class ServicioInvalido(ErrorFJ):
    """Los datos del servicio no sirven (precio, capacidad, nivel...)."""


class ServicioNoDisponible(ErrorFJ):
    """Se quiso reservar un servicio que no está disponible."""


class ReservaInvalida(ErrorFJ):
    """La reserva no se pudo crear o procesar."""


class OperacionNoPermitida(ErrorFJ):
    """Se pidió algo que el estado de la reserva no deja hacer."""


class CalculoInvalido(ErrorFJ):
    """El cálculo del costo recibió datos que no tienen sentido."""

# >>>>>>>>>> Parte: registro <<<<<<<<<<
# ---------------------------------------------------------------
# registro.py
# Aquí se arma el archivo de logs. Todo lo que pasa (lo bueno y lo
# malo) se anota en "eventos.log" con la fecha y la hora.
# Fuente: módulo logging, Van Rossum y Drake (2024).
# ---------------------------------------------------------------

# El archivo se guarda junto al código
RUTA_LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "eventos.log")


def preparar_log():
    """Crea el log una sola vez y lo devuelve listo para usar."""
    log = logging.getLogger("software_fj")
    if not log.handlers:  # así no se repiten los mensajes
        log.setLevel(logging.INFO)
        archivo = logging.FileHandler(RUTA_LOG, encoding="utf-8")
        archivo.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
        log.addHandler(archivo)
    return log


log = preparar_log()

# >>>>>>>>>> Parte: clientes <<<<<<<<<<
# ---------------------------------------------------------------
# clientes.py
# Clase abstracta Entidad (la base de todo) y la clase Cliente.
# Los datos del cliente son privados: solo se tocan por los
# métodos "set" que revisan que todo esté bien escrito.
# Fuente: Cuevas Álvarez (2016), pp. 373-385 (clases, herencia, propiedades) y Romano et al. (2019).
# ---------------------------------------------------------------



class Entidad(ABC):
    """Base de todo lo que tiene un código en el sistema."""

    def __init__(self, codigo):
        self._codigo = codigo  # el código no se cambia después

    @property
    def codigo(self):
        return self._codigo

    @abstractmethod
    def resumen(self):
        """Cada clase hija cuenta quién es en una sola línea."""


class Cliente(Entidad):
    """Persona que contrata los servicios de Software FJ."""

    # Forma básica de un correo: algo@algo.algo
    _FORMA_CORREO = re.compile(r"^[\w\.\-]+@[\w\-]+\.[\w\.\-]+$")

    def __init__(self, codigo, nombre, correo, telefono):
        super().__init__(codigo)
        # Usamos los "set" para que se revise cada dato desde el inicio
        self.nombre = nombre
        self.correo = correo
        self.telefono = telefono
        log.info("Se creó el cliente %s (%s)", codigo, self.nombre)

    # ----- nombre -----
    @property
    def nombre(self):
        return self.__nombre

    @nombre.setter
    def nombre(self, valor):
        # Debe ser texto, con al menos 3 letras y sin números
        if not isinstance(valor, str) or len(valor.strip()) < 3:
            raise ClienteInvalido("El nombre debe tener mínimo 3 letras")
        if any(letra.isdigit() for letra in valor):
            raise ClienteInvalido("El nombre no puede llevar números")
        self.__nombre = valor.strip().title()

    # ----- correo -----
    @property
    def correo(self):
        return self.__correo

    @correo.setter
    def correo(self, valor):
        if not isinstance(valor, str) or not self._FORMA_CORREO.match(valor):
            raise ClienteInvalido(f"El correo no es válido: {valor!r}")
        self.__correo = valor.lower()

    # ----- teléfono -----
    @property
    def telefono(self):
        return self.__telefono

    @telefono.setter
    def telefono(self, valor):
        # Solo números y exactamente 10 dígitos (celular colombiano)
        if not (isinstance(valor, str) and valor.isdigit() and len(valor) == 10):
            raise ClienteInvalido(f"El teléfono debe tener 10 números: {valor!r}")
        self.__telefono = valor

    def resumen(self):
        return f"Cliente {self.codigo}: {self.nombre} <{self.correo}>"

# >>>>>>>>>> Parte: servicios <<<<<<<<<<
# ---------------------------------------------------------------
# servicios.py
# Clase abstracta Servicio y tres servicios que heredan de ella:
# salas, equipos y asesorías. Cada uno calcula su costo a su modo
# (eso es el polimorfismo: mismo método, resultado distinto).
# Fuente: Cuevas Álvarez (2016), pp. 373-385 y Romano et al. (2019): clases abstractas y polimorfismo.
# ---------------------------------------------------------------



class Servicio(Entidad):
    """Base de todos los servicios: nombre, precio por hora y disponibilidad."""

    def __init__(self, codigo, nombre, precio_hora, disponible=True):
        super().__init__(codigo)
        self.nombre = nombre
        self._precio_hora = precio_hora
        self.disponible = disponible
        self.validar()  # cada servicio revisa sus propios datos

    @abstractmethod
    def validar(self):
        """Revisa que los datos del servicio estén bien."""

    @abstractmethod
    def describir(self):
        """Explica en una frase qué ofrece el servicio."""

    @abstractmethod
    def calcular_costo(self, horas, impuesto=0.0, descuento=0.0):
        """Calcula cuánto cuesta. Se puede llamar de varias formas:
        calcular_costo(2)                -> solo las horas
        calcular_costo(2, 0.19)          -> con IVA
        calcular_costo(2, 0.19, 0.10)    -> con IVA y descuento
        (así se hace la 'sobrecarga' en Python: con valores opcionales)."""

    def _costo_base(self, horas, impuesto, descuento):
        """Cuenta común para todos: precio x horas, menos descuento, más impuesto."""
        if not isinstance(horas, (int, float)) or horas <= 0:
            raise CalculoInvalido(f"Las horas deben ser un número mayor que 0: {horas!r}")
        if not 0 <= impuesto <= 1:
            raise CalculoInvalido("El impuesto debe estar entre 0 y 1 (0.19 = 19%)")
        if not 0 <= descuento <= 1:
            raise CalculoInvalido("El descuento debe estar entre 0 y 1 (0.10 = 10%)")
        return round(self._precio_hora * horas * (1 - descuento) * (1 + impuesto), 2)

    def _revisar_precio(self):
        if not isinstance(self._precio_hora, (int, float)) or self._precio_hora <= 0:
            raise ServicioInvalido("El precio por hora debe ser mayor que cero")

    def resumen(self):
        estado = "disponible" if self.disponible else "NO disponible"
        return f"Servicio {self.codigo}: {self.nombre} ({estado})"


class Sala(Servicio):
    """Alquiler de salas de reunión. Importa cuánta gente cabe."""

    def __init__(self, codigo, nombre, precio_hora, capacidad, disponible=True):
        self.capacidad = capacidad  # va primero porque validar() la necesita
        super().__init__(codigo, nombre, precio_hora, disponible)

    def validar(self):
        self._revisar_precio()
        if not isinstance(self.capacidad, int) or self.capacidad <= 0:
            raise ServicioInvalido("La capacidad de la sala debe ser un número entero mayor que 0")

    def describir(self):
        return f"Sala '{self.nombre}' con espacio para {self.capacidad} personas, ${self._precio_hora:,.0f} la hora"

    def calcular_costo(self, horas, impuesto=0.0, descuento=0.0):
        return self._costo_base(horas, impuesto, descuento)


class Equipo(Servicio):
    """Alquiler de equipos (portátiles, proyectores...). Lleva un seguro fijo."""

    SEGURO = 5000  # lo que se cobra de más por el seguro del equipo

    def __init__(self, codigo, nombre, precio_hora, tipo, disponible=True):
        self.tipo = tipo
        super().__init__(codigo, nombre, precio_hora, disponible)

    def validar(self):
        self._revisar_precio()
        if not isinstance(self.tipo, str) or not self.tipo.strip():
            raise ServicioInvalido("Falta decir qué tipo de equipo es")

    def describir(self):
        return f"Equipo '{self.nombre}' ({self.tipo}), ${self._precio_hora:,.0f} la hora más seguro"

    def calcular_costo(self, horas, impuesto=0.0, descuento=0.0):
        # Aquí cambia el cálculo: al costo normal se le suma el seguro
        return round(self._costo_base(horas, impuesto, descuento) + self.SEGURO, 2)


class Asesoria(Servicio):
    """Asesorías con un especialista. El nivel del asesor cambia el precio."""

    FACTOR_NIVEL = {"junior": 1.0, "senior": 1.5, "experto": 2.0}

    def __init__(self, codigo, nombre, precio_hora, nivel, disponible=True):
        self.nivel = nivel
        super().__init__(codigo, nombre, precio_hora, disponible)

    def validar(self):
        self._revisar_precio()
        if self.nivel not in self.FACTOR_NIVEL:
            raise ServicioInvalido(f"El nivel debe ser junior, senior o experto, no {self.nivel!r}")

    def describir(self):
        return f"Asesoría '{self.nombre}' con asesor {self.nivel}, desde ${self._precio_hora:,.0f} la hora"

    def calcular_costo(self, horas, impuesto=0.0, descuento=0.0):
        # Aquí cambia el cálculo: se multiplica por el factor del nivel
        return round(self._costo_base(horas, impuesto, descuento) * self.FACTOR_NIVEL[self.nivel], 2)

# >>>>>>>>>> Parte: reservas <<<<<<<<<<
# ---------------------------------------------------------------
# reservas.py
# La reserva junta un cliente, un servicio y una duración, y va
# pasando por estados: PENDIENTE -> CONFIRMADA o CANCELADA.
# Fuente: Van Rossum y Drake (2024), apartado 8: try/except/else/finally y encadenamiento de excepciones.
# ---------------------------------------------------------------


class Reserva(Entidad):
    """Una reserva de un cliente para un servicio durante unas horas."""

    MAX_HORAS = 12  # no se reserva más de 12 horas seguidas

    def __init__(self, codigo, cliente, servicio, horas):
        super().__init__(codigo)
        if not isinstance(cliente, Cliente):
            raise ReservaInvalida("Falta un cliente válido")
        if not isinstance(servicio, Servicio):
            raise ReservaInvalida("Falta un servicio válido")
        if not isinstance(horas, (int, float)) or not 0 < horas <= self.MAX_HORAS:
            raise ReservaInvalida(f"Las horas deben estar entre 1 y {self.MAX_HORAS}: {horas!r}")
        self.cliente = cliente
        self.servicio = servicio
        self.horas = horas
        self.estado = "PENDIENTE"
        self.costo = None  # se llena cuando se procesa

    def confirmar(self):
        """Confirma la reserva si todavía está pendiente y el servicio está libre."""
        if self.estado != "PENDIENTE":
            raise OperacionNoPermitida(f"No se puede confirmar: la reserva está {self.estado}")
        if not self.servicio.disponible:
            raise ServicioNoDisponible(f"'{self.servicio.nombre}' no está disponible")
        self.estado = "CONFIRMADA"
        log.info("Reserva %s confirmada", self.codigo)

    def cancelar(self):
        """Cancela la reserva. Si ya estaba cancelada, avisa con un error."""
        if self.estado == "CANCELADA":
            raise OperacionNoPermitida("La reserva ya estaba cancelada")
        self.estado = "CANCELADA"
        log.info("Reserva %s cancelada", self.codigo)

    def procesar(self, impuesto=0.19, descuento=0.0):
        """Confirma y calcula el costo. Muestra el uso de try/except/else/finally
        y el encadenamiento de errores (raise ... from ...)."""
        try:
            self.confirmar()
            costo = self.servicio.calcular_costo(self.horas, impuesto, descuento)
        except (ServicioNoDisponible, OperacionNoPermitida) as causa:
            log.error("No se pudo procesar la reserva %s: %s", self.codigo, causa)
            # Se lanza un error nuevo, pero guardando el original como causa
            raise ReservaInvalida(f"La reserva {self.codigo} no se pudo procesar") from causa
        except Exception as causa:
            self.estado = "PENDIENTE"  # si falló el cálculo, vuelve a como estaba
            log.error("Falló el cálculo de la reserva %s: %s", self.codigo, causa)
            raise ReservaInvalida(f"Falló el cálculo de la reserva {self.codigo}") from causa
        else:
            # Esto solo se ejecuta si NO hubo errores arriba
            self.costo = costo
            log.info("Reserva %s procesada, costo $%s", self.codigo, costo)
            return costo
        finally:
            # Esto se ejecuta siempre, haya o no errores
            log.info("Terminó el procesamiento de la reserva %s", self.codigo)

    def resumen(self):
        texto = (f"Reserva {self.codigo}: {self.cliente.nombre} -> {self.servicio.nombre}, "
                 f"{self.horas} h, {self.estado}")
        if self.costo is not None:
            texto += f", ${self.costo:,.2f}"
        return texto

# >>>>>>>>>> Parte: gestor <<<<<<<<<<
# ---------------------------------------------------------------
# gestor.py
# El gestor es el "cerebro": guarda las listas de clientes,
# servicios y reservas (en memoria, sin base de datos) y ofrece
# las acciones principales para usarlas con calma.
# ---------------------------------------------------------------


class Gestor:
    """Maneja todo el sistema de Software FJ."""

    def __init__(self):
        self.clientes = []
        self.servicios = []
        self.reservas = []

    # ----- buscar -----
    def _buscar(self, lista, codigo, nombre_cosa):
        """Busca por código dentro de una lista; si no lo halla, avisa."""
        for elemento in lista:
            if elemento.codigo == codigo:
                return elemento
        raise ErrorFJ(f"No existe {nombre_cosa} con código {codigo}")

    # ----- registrar -----
    def registrar_cliente(self, codigo, nombre, correo, telefono):
        if any(c.codigo == codigo for c in self.clientes):
            raise ErrorFJ(f"Ya existe un cliente con código {codigo}")
        cliente = Cliente(codigo, nombre, correo, telefono)
        self.clientes.append(cliente)
        return cliente

    def registrar_servicio(self, servicio):
        if any(s.codigo == servicio.codigo for s in self.servicios):
            raise ErrorFJ(f"Ya existe un servicio con código {servicio.codigo}")
        self.servicios.append(servicio)
        log.info("Se registró el servicio %s", servicio.codigo)
        return servicio

    def crear_reserva(self, codigo, codigo_cliente, codigo_servicio, horas):
        cliente = self._buscar(self.clientes, codigo_cliente, "un cliente")
        servicio = self._buscar(self.servicios, codigo_servicio, "un servicio")
        if any(r.codigo == codigo for r in self.reservas):
            raise ReservaInvalida(f"Ya existe la reserva {codigo}")
        reserva = Reserva(codigo, cliente, servicio, horas)
        self.reservas.append(reserva)
        log.info("Se creó la reserva %s", codigo)
        return reserva

    def procesar_reserva(self, codigo, impuesto=0.19, descuento=0.0):
        reserva = self._buscar(self.reservas, codigo, "una reserva")
        return reserva.procesar(impuesto, descuento)

    def cancelar_reserva(self, codigo):
        self._buscar(self.reservas, codigo, "una reserva").cancelar()

    # ----- consultas -----
    def reservas_de(self, codigo_cliente):
        """Todas las reservas de un cliente."""
        return [r for r in self.reservas if r.cliente.codigo == codigo_cliente]

    def total_facturado(self):
        """Suma lo que cuestan las reservas confirmadas y procesadas."""
        return round(sum(r.costo for r in self.reservas
                         if r.estado == "CONFIRMADA" and r.costo is not None), 2)

# >>>>>>>>>> Parte: main <<<<<<<<<<
# ---------------------------------------------------------------
# main.py
# Programa principal: hace 18 operaciones, unas buenas y otras con
# errores a propósito, para mostrar que el sistema NO se cae.
# Se ejecuta con:  python main.py
# ---------------------------------------------------------------

fj = Gestor()


def hacer(numero, que_se_hace, accion):
    """Corre una operación. Si sale mal, anota el error y sigue con la siguiente."""
    print(f"\n[{numero:02d}] {que_se_hace}")
    try:
        resultado = accion()
        print("     Bien ->", resultado)
        log.info("Operación %s bien: %s", numero, que_se_hace)
    except ErrorFJ as error:
        causa = f" | causa original: {error.__cause__!r}" if error.__cause__ else ""
        print(f"     Error controlado -> {error}{causa}")
        log.error("Operación %s con error: %s (%s)", numero, que_se_hace, error)
    except Exception as error:  # incluso un error que no esperábamos no tumba el programa
        print("     Error inesperado ->", error)
        log.critical("Operación %s con error inesperado: %r", numero, error)


def main():
    log.info("===== Empieza la simulación =====")

    # --- Clientes ---
    hacer(1, "Registrar a Ana (datos buenos)",
          lambda: fj.registrar_cliente("C1", "ana torres", "Ana@Correo.com", "3001234567").resumen())
    hacer(2, "Registrar a Luis con correo mal escrito",
          lambda: fj.registrar_cliente("C2", "Luis Pérez", "luis-correo.com", "3007654321"))
    hacer(3, "Registrar a Marta con teléfono corto",
          lambda: fj.registrar_cliente("C3", "Marta Díaz", "marta@correo.com", "123"))
    hacer(4, "Registrar a un cliente con números en el nombre",
          lambda: fj.registrar_cliente("C4", "Juan123", "juan@correo.com", "3112223344"))
    hacer(5, "Registrar a Pedro (datos buenos)",
          lambda: fj.registrar_cliente("C5", "Pedro Gómez", "pedro@correo.com", "3159998877").resumen())

    # --- Servicios ---
    hacer(6, "Crear la sala Norte",
          lambda: fj.registrar_servicio(Sala("S1", "Sala Norte", 30000, 10)).describir())
    hacer(7, "Crear una sala con capacidad negativa",
          lambda: fj.registrar_servicio(Sala("S2", "Sala Sur", 30000, -4)).describir())
    hacer(8, "Crear el equipo Portátil",
          lambda: fj.registrar_servicio(Equipo("S3", "Portátil", 8000, "computador")).describir())
    hacer(9, "Crear una asesoría con nivel que no existe",
          lambda: fj.registrar_servicio(Asesoria("S4", "Asesoría Python", 50000, "dios")).describir())
    hacer(10, "Crear la asesoría con nivel experto",
          lambda: fj.registrar_servicio(Asesoria("S5", "Asesoría Python", 50000, "experto")).describir())

    # --- Reservas ---
    hacer(11, "Reservar la Sala Norte para Ana por 3 horas",
          lambda: fj.crear_reserva("R1", "C1", "S1", 3).resumen())
    hacer(12, "Reservar un equipo por 20 horas (pasa el máximo)",
          lambda: fj.crear_reserva("R2", "C1", "S3", 20).resumen())
    hacer(13, "Reservar para un cliente que no existe",
          lambda: fj.crear_reserva("R3", "C99", "S1", 2).resumen())
    hacer(14, "Procesar R1 con IVA 19% y descuento 10%",
          lambda: fj.procesar_reserva("R1", 0.19, 0.10))
    hacer(15, "Procesar R1 otra vez (ya estaba confirmada)",
          lambda: fj.procesar_reserva("R1"))

    # El portátil se daña y deja de estar disponible
    fj.servicios[1].disponible = False
    hacer(16, "Reservar y procesar el portátil que ya no está disponible",
          lambda: (fj.crear_reserva("R4", "C5", "S3", 2), fj.procesar_reserva("R4"))[1])
    hacer(17, "Costo de la asesoría por 2 horas con impuesto absurdo (150%)",
          lambda: fj.servicios[2].calcular_costo(2, 1.5))
    hacer(18, "Costo de la asesoría por 2 horas con IVA 19%",
          lambda: fj.servicios[2].calcular_costo(2, 0.19))

    print("\n--- Resumen final ---")
    print("Clientes registrados:", len(fj.clientes))
    print("Servicios registrados:", len(fj.servicios))
    print("Reservas hechas:", len(fj.reservas))
    print(f"Total facturado: ${fj.total_facturado():,.2f}")
    print("Los errores quedaron anotados en:", RUTA_LOG)
    log.info("===== Termina la simulación =====")


if __name__ == "__main__":
    main()