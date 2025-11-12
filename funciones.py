

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