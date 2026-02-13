kiosco_app/
│
├── main.py                          # Archivo principal que arranca la app
│
├── ui/                              # Todo lo visual (interfaz)
│   ├── __init__.py
│   ├── pantalla_ventas.py          # Interfaz de ventas
│   ├── pantalla_stock.py           # Interfaz de stock
│   └── pantalla_login.py           # Interfaz de login/empleado
│
├── modules/                         # Lógica del programa
│   ├── __init__.py
│   ├── ventas.py                   # Lógica de ventas
│   ├── stock.py                    # Control y alertas de stock
│   ├── empleados.py                # Control de empleados y turnos
│   └── licencia.py                 # Verificación de licencia mensual
│
├── data/                            # Archivos de datos (locales)
│   ├── productos.json              # Lista de productos
│   ├── ventas.json                 # Historial de ventas
│   ├── empleados.json              # Lista de empleados
│   └── config.json                 # Configuración general
│
├── assets/                          # Imágenes, íconos, sonidos, etc.
│   └── logo.png
│
└── README.md                        # Instrucciones y guía del proyecto


**Plan de Desarrollo - Aplicación para Kioscos (PC - Local)**

---

**Objetivo General:** Crear una aplicación de escritorio para computadoras con Windows, orientada a negocios pequeños tipo kiosco. Esta aplicación funcionará sin necesidad de internet ni bases de datos externas. Todo estará guardado localmente, utilizando archivos simples como JSON. Además, el objetivo a largo plazo es poder alquilar esta aplicación a otros negocios cobrando una licencia mensual mediante un sistema de activación por código.

Este documento sirve para mantener toda la información organizada y clara, por si hay que continuar el proyecto en otro momento o con otra inteligencia artificial.

---

**Resumen de Características Clave:**

* Funcionamiento 100% offline
* Diseño claro (sin modo oscuro)
* Sin base de datos externa
* Todo guardado localmente en archivos como `.json` o `.csv`
* Validación de licencia mensual por código ingresado manualmente
* Interfaz simple, intuitiva, adaptada a usuarios no técnicos

---

**Módulos Iniciales:**

1. **Pantalla de Ventas**

   * Ingreso de productos, cantidad y precio
   * Cálculo automático del total y del vuelto
   * Interfaz para buscar productos rápidamente

2. **Control de Stock**

   * Registro de productos con nombre, precio, stock inicial
   * Descuento automático del stock al realizar una venta
   * Avisos cuando un producto baja de cierto nivel (por ejemplo, menos de 5 unidades)
   * Botón para reponer stock fácilmente

3. **Validación de Licencia**

   * El programa requiere un código que se ingresa manualmente una vez por mes
   * El código puede ser igual para todos los negocios si se desea
   * El código se valida localmente, sin necesidad de internet
   * El código puede estar cifrado para evitar que sea visible fácilmente

4. **Historial de Ventas**

   * Registro automático de cada venta con datos: fecha, hora, productos, cantidades, total
   * Guardado en archivo local (JSON o CSV)

---

**Módulos Intermedios:**

5. **Gestor de Empleados**

   * Alta/baja de empleados
   * Cada empleado tiene su propio usuario (sin contraseña si se quiere simple)
   * Posibilidad de asignar roles: administrador o vendedor

6. **Registro por Empleado**

   * Cada venta queda registrada con el nombre del empleado
   * Historial filtrable por empleado y por fecha

7. **Cierre de Caja**

   * Total vendido en el día
   * Posibilidad de exportar resumen del día (pantalla o archivo)

---

**Módulos Avanzados (para versiones futuras):**

* Descuentos automáticos o manuales
* Reportes exportables a PDF o Excel
* Control de ingresos/egresos (por ejemplo, pagos a proveedores)
* Atajos para ventas rápidas (productos más vendidos)
* Soporte para impresoras de ticket (opcional)
* Copias de seguridad automáticas en pendrive o carpeta externa

---

**Tecnología Recomendada para el Desarrollo:**

* Lenguaje: **Python**
* Librería de interfaz gráfica: **Tkinter**
* Almacenamiento: Archivos JSON
* Generación de ejecutable: PyInstaller

**Por qué Python + Tkinter:**

* Rápido de desarrollar
* Liviano y funciona en casi cualquier PC con Windows
* Fácil de mantener, modificar y escalar
* No necesita instalar bases de datos ni servidores

---

## Plan de Trabajo y Organización en Equipo (2 personas)

### Fase 1: Planificación y Diseño (ambos)

1. **Definir funcionalidades mínimas**

   * Confirmar los módulos iniciales que se van a implementar primero
2. **Hacer bocetos de las pantallas**

   * Pantalla de ventas, stock, inicio (código), historial, empleados
   * Herramientas sugeridas: Figma, Paint, papel

**División de tarea sugerida:**

* Persona 1 dibuja las interfaces y estructura visual
* Persona 2 revisa y anota cómo debería funcionar cada parte

---

### Fase 2: Preparación del Proyecto

3. **Crear estructura del proyecto**

```
/app
  main.py
  /ui        -> interfaces (Tkinter)
  /data      -> archivos JSON
  /modules   -> funciones lógicas
  /assets    -> imágenes, íconos, etc.
```

4. **Crear archivos base JSON vacíos**

* productos.json
* ventas.json
* empleados.json

**División sugerida:**

* Persona 1 arma carpetas y base de código (main.py, etc.)
* Persona 2 crea los archivos JSON con campos vacíos y los formatea

---

### Fase 3: Desarrollo por Módulos

**Comenzar con el módulo de ventas:**

**División de tareas sugerida:**

* Persona 1: arma la ventana con los botones, campos, layout (Tkinter)
* Persona 2: programa la lógica (calcular total, restar stock, guardar venta)

Una vez que ese módulo funciona bien:

* Agregar módulo de stock
* Agregar módulo de historial
* Agregar módulo de licencia (si es necesario al inicio)
* Agregar módulo de empleados

---

### Fase 4: Prueba y Empaquetado

1. Probar todo en diferentes PCs
2. Arreglar errores simples y probar sin conexión
3. Usar `PyInstaller` para generar el ejecutable (.exe)

---

**Resumen del orden paso a paso:**

1. Confirmar lista de funciones (ambos)
2. Diseñar pantallas (ambos)
3. Crear carpetas y archivos base (1)
4. Crear archivos JSON (2)
5. Empezar por el módulo de ventas:

   * Uno hace la interfaz
   * Otro hace la lógica
6. Agregar módulos uno por uno
7. Probar, empaquetar, y distribuir

---



