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