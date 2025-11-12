import csv
import os
import requests
import sys
import math
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from thefuzz import fuzz, process

console = Console()

NOMBRE_ARCHIVO = 'paises.csv'
URL_API = 'https://restcountries.com/v3.1/all?fields=name,population,area,region,translations'
TAMANO_PAGINA = 10
MAPEO_CONTINENTES = {
    'Asia': 'Asia',
    'Europe': 'Europa',
    'Americas': 'America',
    'Africa': 'Africa',
    'Oceania': 'Oceania',
    'Antarctic': 'Antartida',
    '': 'Sin Continente',
    'N/A': 'Sin Continente'
}

## Esta funcion limpia la pantalla de la consola.

def limpiar_consola():
    if os.name == 'posix':
        os.system('clear')
    elif os.name == 'nt':
        os.system('cls')

## Esta funcion pausa la ejecución, espera un 'Enter' del usuario y luego limpia la consola.Acepta un mensaje de pausa personalizado.

def pausa_para_continuar(mensaje_pausa="Presione Enter para volver al menú principal..."):
    
    console.print(f"\n[bold magenta]{mensaje_pausa}[/bold magenta]", end="")
    
    console.file.flush()
    
    try:
        input()
    except KeyboardInterrupt:
        pass

    limpiar_consola()

## Esta funcion descarga los datos de la API, traduce nombres y continentes al español, y guarda el resultado en el archivo CSV ('paises.csv')

def descargar_y_crear_csv():
    console.print("[bold blue]:cloud: Descargando datos desde la API de restcountries.com...[/bold blue]")
    try:
        respuesta = requests.get(URL_API)
        respuesta.raise_for_status()
        datos = respuesta.json()
        
        filas_escritas = 0
        
        with open(NOMBRE_ARCHIVO, 'w', newline='', encoding='utf-8') as archivo:
            writer = csv.writer(archivo)
            writer.writerow(['nombre', 'poblacion', 'superficie', 'continente'])
            
            for pais in datos:
                nombre = pais.get('name', {}).get('common', 'N/A')
                traducciones = pais.get('translations', {})
                nombre_espanol = traducciones.get('spa', {}).get('common')
                if nombre_espanol:
                    nombre = nombre_espanol
                else:
                    nombre = pais.get('name', {}).get('common', 'N/A')
                poblacion = pais.get('population', 0)
                superficie = int(pais.get('area', 0) or 0)
                region_api = pais.get('region', 'N/A')
                continente = MAPEO_CONTINENTES.get(region_api, region_api)
                
                if nombre != 'N/A' and continente != 'N/A' and superficie > 0:
                    writer.writerow([nombre, poblacion, superficie, continente])
                    filas_escritas += 1
        
        if filas_escritas == 0:
            console.print("[bold red]Error: La descarga fue exitosa, pero no se escribió ningún país.[/bold red]")
            return False
            
        console.print(f"[bold green]:white_check_mark: Archivo '{NOMBRE_ARCHIVO}' creado exitosamente con {filas_escritas} países.[/bold green]")
        
        console.file.flush()
    
    except requests.exceptions.RequestException as e:
        console.print(f"[bold red]Error al conectar con la API: {e}[/bold red]")
        return False
    except IOError as e:
        console.print(f"[bold red]Error al escribir el archivo CSV: {e}[/bold red]")
        return False
    except Exception as e:
        console.print(f"[bold red]Error inesperado durante la descarga: {e}[/bold red]")
        return False
        
    return True

## Carga los países desde el CSV. Si el archivo no existe, llama a la función de descarga ('descargar_y_crear_csv') primero para crearlo.

def cargar_datos():

    if not os.path.exists(NOMBRE_ARCHIVO):
        console.print(f"[bold yellow]El archivo '{NOMBRE_ARCHIVO}' no existe. Iniciando descarga.[/bold yellow]")
        if not descargar_y_crear_csv():
            return []

        pausa_para_continuar("¡Datos descargados y traducidos! Presione Enter para ir al menú...")

    paises = []
    try:
        with open(NOMBRE_ARCHIVO, 'r', encoding='utf-8') as archivo:
            reader = csv.DictReader(archivo)
            filas_con_error = 0
            for fila in reader:
                try:
                    fila['poblacion'] = int(fila['poblacion'])
                    fila['superficie'] = int(fila['superficie'])
                    paises.append(fila)
                except (ValueError, TypeError):
                    filas_con_error += 1
            if filas_con_error > 0:
                 console.print(f"[bold yellow]Advertencia: Se omitieron {filas_con_error} filas con formato incorrecto.[/bold yellow]")
                 
    except Exception as e:
        console.print(f"[bold red]Error inesperado al leer el CSV: {e}[/bold red]")
        return []
        
    return paises

## Muestra una lista de países en una tabla (rich.Table). Incluye lógica para mostrar el número de página actual si se proporciona.

def mostrar_paises(lista_paises, pagina_actual=None, total_paginas=None):

    if not lista_paises:
        console.print("[bold red]:x: No se encontraron países que coincidan con los criterios.[/bold red]")
        return
    
    tabla = Table(title="--- Resultados de Países ---", show_lines=True, header_style="bold cyan")
    
    tabla.add_column("Nombre", style="dim", width=30)
    tabla.add_column("Continente", justify="left")
    tabla.add_column("Población", justify="right", style="green")
    tabla.add_column("Superficie (km²)", justify="right", style="yellow")
    
    for pais in lista_paises:
        poblacion_str = f"{pais['poblacion']:,}"
        superficie_str = f"{pais['superficie']:,}"
        
        tabla.add_row(
            pais['nombre'],
            pais['continente'],
            poblacion_str,
            superficie_str
        )

    console.print(tabla)
    
    if pagina_actual and total_paginas:
        console.print(f"\n[bold cyan]Página {pagina_actual} de {total_paginas}[/bold cyan] (Total: {len(lista_paises)} países en esta página)")
    else:
        console.print(f"\n[bold magenta]Total: {len(lista_paises)} países.[/bold magenta]")

## Pide un nombre al usuario, usa 'theFuzz' para buscar coincidencias aunque tengan errores en la ortografia y muestra los resultados. Luego pausa la consola.

def buscar_por_nombre(paises):

    console.print("[bold yellow]🔎 Ingrese el nombre (o parte del nombre) del país:[/bold yellow] ", end="")
    nombre_buscado = input().strip()
    
    if not nombre_buscado:
        console.print("[bold red]Error: La búsqueda no puede estar vacía.[/bold red]")
        return
        
    nombres_paises = [pais['nombre'] for pais in paises]
    
    coincidencias_fuzz = process.extract(
        query=nombre_buscado, 
        choices=nombres_paises, 
        scorer=fuzz.partial_ratio,
        limit=10 
    )
    
    UMBRAL_PUNTAJE = 80
    resultados = []
    
    for nombre_coincidente, puntaje in coincidencias_fuzz: 
        if puntaje >= UMBRAL_PUNTAJE: 
            pais_encontrado = next(
                (p for p in paises if p['nombre'] == nombre_coincidente), 
                None
            )
            if pais_encontrado:
                 resultados.append(pais_encontrado)

    if not resultados:
        console.print(f"[bold red]:x: No se encontraron coincidencias para '{nombre_buscado}' (Umbral: {UMBRAL_PUNTAJE}).[/bold red]")
        return
        
    mostrar_paises(resultados)

    pausa_para_continuar()
    
## Pide un número al usuario (mostrando 'mensaje') y lo valida,asegurando que sea un entero. Maneja errores de entrada.

def validar_entero(mensaje):

    while True:
        try:
            console.print(f"[bold yellow]{mensaje}[/bold yellow] ", end="")
            valor_str = input().strip()
            
            if not valor_str:
                console.print("[bold red]Error: El valor no puede estar vacío.[/bold red]")
                continue
            
            return int(valor_str)
        
        except ValueError:
            console.print("[bold red]Error: Por favor, ingrese un número entero válido.[/bold red]")
        except (EOFError, KeyboardInterrupt):
            console.print("\n[bold yellow]Operación cancelada.[/bold yellow]")
            return None
          
# Pide un nombre de continente, filtra la lista (ignorando mayúsculas/minúsculas) y muestra los resultados.

def filtrar_por_continente(paises):

    console.print("[bold yellow]🗺️  Ingrese el nombre del continente:[/bold yellow] ", end="")
    continente_buscado = input().strip()
    
    if not continente_buscado:
        console.print("[bold red]Error: El nombre del continente no puede estar vacío.[/bold red]")
        pausa_para_continuar() 
        return
    
    continentes_disponibles = sorted(list(set(p['continente'] for p in paises)))
    console.print(f"[bold magenta]Continentes disponibles:[/bold magenta] {', '.join(c for c in continentes_disponibles)}")
    
    continente_buscado_lower = continente_buscado.lower()
    
    resultados = [
        pais for pais in paises 
        if continente_buscado_lower == pais['continente'].lower()
    ]

    mostrar_paises(resultados)
    pausa_para_continuar()

# Pide una población mínima y máxima (usando 'validar_entero'),filtra la lista y muestra los resultados.

def filtrar_por_poblacion(paises):

    console.print("\n[bold cyan]--- Filtro por Rango de Población ---[/bold cyan]")
    min_pob = validar_entero("Ingrese la población mínima:")
    if min_pob is None: return
    
    max_pob = validar_entero("Ingrese la población máxima:")
    if max_pob is None: return
    
    if min_pob > max_pob:
        console.print("[bold red]Error: La población mínima no puede ser mayor que la máxima.[/bold red]")
        return

    resultados = [pais for pais in paises if min_pob <= pais['poblacion'] <= max_pob]
    mostrar_paises(resultados)

    pausa_para_continuar()

# Pide una superficie mínima y máxima (usando 'validar_entero'),filtra la lista y muestra los resultados.

def filtrar_por_superficie(paises):

    console.print("\n[bold cyan]--- Filtro por Rango de Superficie (km²) ---[/bold cyan]")
    min_sup = validar_entero("Ingrese la superficie mínima (km²):")
    if min_sup is None: return
    
    max_sup = validar_entero("Ingrese la superficie máxima (km²):")
    if max_sup is None: return

    if min_sup > max_sup:
        console.print("[bold red]Error: La superficie mínima no puede ser mayor que la máxima.[/bold red]")
        return

    resultados = [pais for pais in paises if min_sup <= pais['superficie'] <= max_sup]
    mostrar_paises(resultados)

    pausa_para_continuar()

# Pide un criterio y orden (A/D). Muestra la lista ordenada usando un bucle de paginación interactivo (A/S/V) que limpia la consola.

def ordenar_paises(paises):
    limpiar_consola()

    console.print("\n[bold cyan]--- Criterios de Ordenamiento ---[/bold cyan]")
    console.print("1. Nombre")
    console.print("2. Continente")
    console.print("3. Población")
    console.print("4. Superficie")
    
    criterio = input("Ingrese el número del criterio (1-4): ").strip()
    
    if criterio not in ['1', '2', '3', '4']:
        console.print("[bold red]Opción de criterio inválida. Abortando.[/bold red]")
        return 

    console.print("\n[bold cyan]--- Tipo de Orden ---[/bold cyan]")
    orden = input("Ascendente (A) o Descendente (D): ").upper().strip()
    
    if orden == 'D':
        orden_descendente = True
    elif orden == 'A':
        orden_descendente = False
    else:
        console.print("[bold yellow]Opción de orden inválida. Usando Ascendente por defecto.[/bold yellow]")
        orden_descendente = False 
    
    paises_ordenados = []

    if criterio == '1': # Por Nombre
        paises_ordenados = sorted(paises, key=lambda p: p['nombre'], reverse=orden_descendente)
    elif criterio == '2': # Por Continente (y luego nombre)
        paises_ordenados = sorted(paises, key=lambda p: (p['continente'], p['nombre']), reverse=orden_descendente) 
    elif criterio == '3': # Por Población
        paises_ordenados = sorted(paises, key=lambda p: p['poblacion'], reverse=orden_descendente)
    elif criterio == '4': # Por Superficie
        paises_ordenados = sorted(paises, key=lambda p: p['superficie'], reverse=orden_descendente)
    
    if not paises_ordenados:
        console.print("[bold red]No hay países para mostrar después del ordenamiento.[/bold red]")
        return
        
    total_paises = len(paises_ordenados)
    total_paginas = math.ceil(total_paises / TAMANO_PAGINA)
    pagina_actual = 1
    
    while True:
        inicio = (pagina_actual - 1) * TAMANO_PAGINA
        fin = inicio + TAMANO_PAGINA
        
        paises_pagina = paises_ordenados[inicio:fin]

        mostrar_paises(paises_pagina, pagina_actual=pagina_actual, total_paginas=total_paginas)
        
        console.print("\n[bold]Opciones de Paginación:[/bold]")
        opciones_nav = []
        if pagina_actual > 1:
            opciones_nav.append("[bold green](A)Anterior[/bold green]")
        if pagina_actual < total_paginas:
            opciones_nav.append("[bold green](S)Siguiente[/bold green]")
        opciones_nav.append("[bold red](V)Volver al menú principal[/bold red]")
        
        console.print(" | ".join(opciones_nav))
        
        opcion_nav = input("Ingrese opción (A/S/V): ").upper().strip()
        
        if opcion_nav == 'V':
            limpiar_consola()
            break 
        
        elif opcion_nav == 'A':
            if pagina_actual > 1:
                pagina_actual -= 1
                limpiar_consola()
            else:
                console.print("[bold yellow]Ya estás en la primera página.[/bold yellow]")

        elif opcion_nav == 'S':
            if pagina_actual < total_paginas:
                pagina_actual += 1
                limpiar_consola()
            else:
                console.print("[bold yellow]Ya estás en la última página.[/bold yellow]")
                
        else:
            console.print("[bold red]Opción de navegación inválida. Intente A, S o V.[/bold red]")

# Calcula y muestra estadísticas (país más/menos poblado, promedio,conteo por continente). Luego pausa la consola.

def mostrar_estadisticas(paises):

    if not paises:
        console.print("[bold red]No hay datos para calcular estadísticas.[/bold red]")
        return

    total_paises = len(paises)
    total_poblacion = sum(p['poblacion'] for p in paises)
        
    pais_max_pob = max(paises, key=lambda p: p['poblacion'])
    pais_min_pob = min(paises, key=lambda p: p['poblacion'])
    
    prom_poblacion = total_poblacion / total_paises if total_paises > 0 else 0
    
    paises_por_continente = {}
    for pais in paises:
        continente = pais['continente']
        paises_por_continente[continente] = paises_por_continente.get(continente, 0) + 1
        
    console.print("\n[bold blue]📈 --- Estadísticas Globales ---[/bold blue]")
    console.print(f"País con mayor población: [green]{pais_max_pob['nombre']} ({pais_max_pob['poblacion']:,})[/green]")
    console.print(f"País con menor población: [red]{pais_min_pob['nombre']} ({pais_min_pob['poblacion']:,})[/red]")
    console.print(f"Población promedio: {prom_poblacion:,.2f}")
    
    console.print("\n[bold yellow]Cantidad de países por continente:[/bold yellow]")
    for continente, cantidad in sorted(paises_por_continente.items()):
        console.print(f"- {continente}: [magenta]{cantidad} países[/magenta]")

    pausa_para_continuar()

# Limpia la consola y muestra el menú principal de opciones usando un Panel y Tabla de 'rich' para centrarlo.
    
def mostrar_menu():
    limpiar_consola()

    menu_tabla = Table(
        show_header=False, 
        show_edge=False, 
        box=None, # Sin bordes
        padding=(0, 1), # Espaciado (vertical, horizontal)
        width=50 # Ancho fijo para centrar mejor
    )
    
    menu_tabla.add_column(width=4, justify="right")
    menu_tabla.add_column()

    menu_tabla.add_row("1.", "[gray]🔍 Buscar país por nombre[/gray]🔍")
    menu_tabla.add_row("2.", "[cyan]🌎 Filtrar por continente[/cyan]🌎")
    menu_tabla.add_row("3.", "[yellow]👨 Filtrar por rango de población[/yellow]👩")
    menu_tabla.add_row("4.", "[green]🌲 Filtrar por rango de superficie[/green]🌲")
    menu_tabla.add_row("5.", "[magenta]📉 Ordenar países[/magenta]📈")
    menu_tabla.add_row("6.", "[white]📊 Mostrar estadísticas[/white]📊")
    menu_tabla.add_row("", "") # Fila vacía como espaciador
    menu_tabla.add_row("0.", "[bold red]👋 Salir[/bold red]👋")

    console.print(
        Panel(
            menu_tabla,
            title="[bold blue] 🌐 Gestión de Datos de Países (TPI) 🌐 [/bold blue]",
            border_style="blue",
            padding=(1, 4)
        )
    )