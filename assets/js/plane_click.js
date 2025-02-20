document.addEventListener("DOMContentLoaded", function() {
    let trayectoriasLengths = {{trayectoriasLengths}};
    let selectedAvionId = null;
    function assignIdsToPaths() {
        let polylines = document.querySelectorAll('path.leaflet-interactive');
        let avionIndex = 0;
        let segmentCounter = 0;

        polylines.forEach((path) => {
            if (segmentCounter >= trayectoriasLengths[avionIndex]) {
                avionIndex++;
                segmentCounter = 0;
                while (trayectoriasLengths[avionIndex] === 0) {
                    avionIndex++;
                }
            }
            let avionId = avionIndex;
            path.setAttribute('data-avion-id', avionId);
            segmentCounter++;
        });
    }

    function hideOthers(selectedId) {
        selectedAvionId = selectedId;
        console.log("SELECTEDID", selectedId)
        document.querySelectorAll('.leaflet-marker-icon').forEach((marker, idx) => {
            marker.style.display = (idx === selectedId) ? 'block' : 'none';
        });

        document.querySelectorAll('path.leaflet-interactive').forEach(path => {
            let avionId = Number(path.getAttribute('data-avion-id'));
            path.style.display = (avionId === selectedId) ? 'block' : 'none';
        });
    }

    function resetAll() {
        document.querySelectorAll('.leaflet-marker-icon').forEach(marker => marker.style.display = 'block');
        document.querySelectorAll('path.leaflet-interactive').forEach(line => line.style.display = 'block');

        assignIdsToPaths();
        assignEventListeners();

        if (selectedAvionId !== null) {
            setTimeout(() => hideOthers(selectedAvionId), 100);
        }
    }

    function assignEventListeners() {
        document.querySelectorAll('.leaflet-marker-icon').forEach((el, idx) => {
            el.addEventListener('click', () => hideOthers(idx));
        });
    }

    function activateAllLayers() {
        document.querySelectorAll('.leaflet-control-layers-selector').forEach((checkbox, index) => {
            if (index !== 4 && !checkbox.checked) {
                checkbox.click();
            }
        });
        setTimeout(() => resetAll(), 500);
    }

    const observer = new MutationObserver(() => {
        resetAll();
    });
    observer.observe(document.querySelector('.leaflet-control-layers'), { childList: true, subtree: true });
    resetAll();

    var button = document.createElement('button');
    button.innerText = 'Mostrar todos los aviones';
    button.style.position = 'absolute';
    button.style.top = '10px';
    button.style.right = '10px';
    button.style.zIndex = '1000';
    button.style.background = 'white';
    button.style.border = '1px solid black';
    button.style.padding = '5px';
    button.style.cursor = 'pointer';
    button.addEventListener('click', function() {
        selectedAvionId = null;
        activateAllLayers();
    });
    document.body.appendChild(button);

    setTimeout(() => {
        // Busca en todos los objetos globales para encontrar el mapa Leaflet
        for (let key in window) {
            if (window.hasOwnProperty(key) && window[key] instanceof L.Map) {
                window.map = window[key];
                console.log("Instancia del mapa encontrada:", window.map);
                break;
            }
        }

        if (!window.map) {
            console.error('No se pudo encontrar la instancia del mapa de Leaflet.');
        }
    }, 500); // Tiempo de espera para asegurarse de que el mapa está creado

    let createdPoint = null; // Variable para guardar el punto creado

    // Escuchar mensajes para cuando el ratón esté sobre un punto
    window.addEventListener('message', function(event) {
                // Escuchar mensajes cuando el ratón sale de un punto
        if (event.data === 'mouse_off_point') {
            console.log('Mouse salió de un punto. Eliminando el punto.');
    
            // Eliminar el punto cuando el ratón sale
            if (createdPoint !== null) {
                window.map.removeLayer(createdPoint);
                createdPoint = null; // Reinicia la variable
            }
        }
        if (event.data.type === 'mouse_on_point') {
            console.log('Mouse sobre el punto: (X:', event.data.x, ', Y:', event.data.y, ')');
            console.log('Hover data:', event.data.hoverData);
    
            var lat = event.data.hoverData[0];
            var lon = event.data.hoverData[1];
    
            console.log("Latitud:", lat);
            console.log("Longitud:", lon);
    
            // Verifica que las coordenadas sean válidas
            if (lat !== undefined && lon !== undefined && lat !== null && lon !== null) {
                try {
                    // Si ya hay un punto creado, elimínalo primero
                    if (createdPoint !== null) {
                        window.map.removeLayer(createdPoint);
                    }
    
                    // Crear el punto 2D como un círculo pequeño (sin interactividad)
                    createdPoint = L.circle([lat, lon], {
                        radius: 100,         // Radio pequeño para el punto
                        color: '#00BFFF',  // Color del borde
                        fillColor: '#00BFFF',  // Color de relleno
                        fillOpacity: 1,    // Opacidad total
                        interactive: false // Sin interactividad
                    }).addTo(window.map);
                    
                } catch (error) {
                    console.error('Error al agregar el punto:', error);
                }
            } else {
                console.error("Latitud o longitud inválidas:", lat, lon);
            }
        }
    

    });
});
