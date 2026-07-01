-GRID RUNNER
  Juego de laberintos construido con grafos para el curso de Estructura de Datos y Algoritmos.

-Cómo correrlo
  bash
  pip install pygame
  python grid_runner.py

-Controles
  Table
  Tecla	Acción
  ↑ ↓ ← →	Moverte por el laberinto
  R	Reiniciar nivel
  N / Espacio	Siguiente nivel (al ganar)


-El juego
  Llegá desde la S (verde) hasta la E (magenta). Evitá las paredes grises, juntá monedas amarillas y cuidado con las trampas rojas.
  Conceptos de grafos que usa


-Concepto
  Nodos:	Cada celda del grid es un nodo 
  Conexiones:	Solo podés moverte a celdas de al lado 
  Verificación de camino:	BFS que revisa que haya salida 
  Nodos visitados:	Se marcan en cyan al pasar


-Hecho con
  Python 3
  PyGame
