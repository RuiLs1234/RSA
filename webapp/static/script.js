document.addEventListener('DOMContentLoaded', function () {
    const socketIO = io.connect('http://' + document.domain + ':' + location.port);
    const mapContainer = document.getElementById('map-container');

    const initialCoordinates = [
        { lat: 39.9776, lng: -8.0000 },
        { lat: 39.9778, lng: -8.0000 },
        { lat: 39.978, lng: -8.0000 }
    ];

    const squareSize = 20; // Size of the square
    const circleRadius = 90; // Radius of the circle

    // Helper function to create and append an SVG circle
    function createCircle(container, circleRadius) {
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('width', (circleRadius * 2) + 'px');
        svg.setAttribute('height', (circleRadius * 2) + 'px');
        container.appendChild(svg);

        const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        circle.setAttribute('cx', circleRadius);
        circle.setAttribute('cy', circleRadius);
        circle.setAttribute('r', circleRadius);
        circle.setAttribute('fill', 'rgba(0, 255, 0, 0.2)'); // Pale green color with 20% opacity
        svg.appendChild(circle);
    }

    // Helper function to create and append a square
    function createSquare(container, squareSize, circleRadius, color) {
        const square = document.createElement('div');
        square.className = 'square';
        square.style.width = squareSize + 'px';
        square.style.height = squareSize + 'px';
        square.style.position = 'absolute';
        square.style.top = (circleRadius - squareSize / 2) + 'px';
        square.style.left = (circleRadius - squareSize / 2) + 'px';
        square.style.backgroundColor = color;
        container.appendChild(square);
    }

    // Function to add initial squares (if any)
    function addInitialSquares(mapContainer) {
        // Render initial static elements
        initialCoordinates.forEach((coord, index) => {
            const itemContainer = document.createElement('div');
            itemContainer.style.position = 'absolute';
            itemContainer.style.top = (200 * index + 100 - circleRadius) + 'px';
            itemContainer.style.left = (420 - circleRadius) + 'px';
            itemContainer.style.width = (circleRadius * 2) + 'px';
            itemContainer.style.height = (circleRadius * 2) + 'px';
            mapContainer.appendChild(itemContainer);

            // Create and append SVG circle
            createCircle(itemContainer, circleRadius);

            // Create and append square
            createSquare(itemContainer, 20, circleRadius, 'rgba(0, 0, 255, 0.5)'); // Blue square for initial static elements
        });
    }

    let lastCoordinates = [];

    function updateMap(coordinates) {
        const mapContainer = document.getElementById('map-container');
    
        // Clear existing elements
        mapContainer.innerHTML = '';
    
        // Add initial squares (if any)
        addInitialSquares(mapContainer);
    
        // Calculate the total height available for displaying squares
        const totalHeight = squareSize - 5;
    
        // Calculate the vertical spacing between squares
        const verticalSpacing = totalHeight / coordinates.length;
    
        // Add squares for each coordinate
        coordinates.forEach((coord, index) => {
            const squareSize = 20; // Size of the square
            const offsetRight = 400; // Additional offset for the new squares
    
            // Calculate position based on coordinates
            let top = (coord.lat - initialCoordinates[index].lat) * 25000 + (squareSize + 10) * index - 50;
            const left = coord.lng - squareSize / 2 + offsetRight; // Add offset for right shift
    
            // Create square element
            const square = document.createElement('div');
            square.className = 'square red'; // Apply CSS class for moving squares
            square.style.width = squareSize + 'px';
            square.style.height = squareSize + 'px';
            square.style.position = 'absolute';
            square.style.top = top + 'px'; // Update top position with calculated value
            square.style.left = left + 'px'; // Update left position with calculated value
            square.id = 'additional-square' + index;
            mapContainer.appendChild(square);
    
            // Store the current coordinates
            lastCoordinates[index] = {
                lat: coord.lat,
                lng: coord.lng,
                top: top,
                left: left
            };
        });
    }
    
    
    // Add event listener for WebSocket messages
    const socketWebSocket = new WebSocket('ws://localhost:8765');

    socketWebSocket.onopen = function (event) {
        console.log('WebSocket connection established.');
    };

    socketWebSocket.onmessage = function (event) {
        const coordinates = JSON.parse(event.data);
        console.log('Received coordinates:', coordinates);
        updateMap(coordinates); // Call function to update the map with received coordinates
    };

    socketWebSocket.onerror = function (error) {
        console.error('WebSocket error:', error);
    };

    // Add event listener for Socket.IO messages
    socketIO.on('update_coordinates', function (data) {
        console.log('Received coordinates:', data);
        updateMap(data); // Call function to update the map with received coordinates
    });
});
