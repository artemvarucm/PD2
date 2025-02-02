### Problemas que pueden surgir en el futuro

#### 1. Duplicados de filas innecesarias
Parece que el avion no cambia de posicion y las filas duplicadas hacen que el avion mayor importancia
100 posicion
100 info -> se podria descartar
130 info -> se podria descartar
140 info -> se podria descartar
200 posicion


#### 2. Guardamos surface position, cuando el avion ya está volando
Si el avión ha despegado, no podemos guardar el surface position, porque no tiene posición en la superficie

Para solucionarlo se podrían compartir atributos en un marco temporal determinado, por ejemplo 2 segundos, y después resetear el estado.
