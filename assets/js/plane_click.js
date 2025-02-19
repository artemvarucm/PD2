document.addEventListener('DOMContentLoaded', function() {
    let trayectoriasLengths = {{trayectoriasLengths}};
    //console.log("TRAAAAA ",trayectoriasLengths)
    let selectedAvionId = null;

    function assignIdsToPaths() {
        let polylines = document.querySelectorAll('path.leaflet-interactive');
        let avionIndex = 0;
        let segmentCounter = 0;
        //let ii = 0;
        polylines.forEach((path) => {
            //console.log("ii=",ii)
            
            if (segmentCounter >= trayectoriasLengths[avionIndex]) {
                avionIndex++;
                segmentCounter = 0;
                while (trayectoriasLengths[avionIndex] === 0){
                    avionIndex++;
                }
            }
            let avionId = avionIndex;
            path.setAttribute('data-avion-id', avionId);
            //console.log("PA ", avionId)
            segmentCounter++;
            
            //ii = ii+ 1;
        });
    }

    function hideOthers(selectedId) {
        selectedAvionId = selectedId;

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
            //console.log("PATTTTTTTTTHH ", idx)
            el.addEventListener('click', () => hideOthers(idx));
        });
    }

    function activateAllLayers() {
        document.querySelectorAll('.leaflet-control-layers-selector').forEach((checkbox, index) => {
            //console.log("CHECKBOX", checkbox, "III", index)
            if (index !==4 && !checkbox.checked) {
                checkbox.click(); // Activa las capas que estaban desactivadas
            }
        });

        setTimeout(() => resetAll(), 500); // Esperamos un poco para que se activen antes de resetear
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
});