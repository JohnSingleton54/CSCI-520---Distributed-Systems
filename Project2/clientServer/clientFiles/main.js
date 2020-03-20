"use strict";

// Grant Nelson and John M.Singleton
// CSCI 520 - Distributed Systems
// Project 2 (Consensus Project)
// due Apr 6, 2020 by 11: 59 PM

// References
// - https://javascript.info/websocket
// - https://base64.guru/developers/javascript/btoa
// - https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API/Writing_WebSocket_client_applications

// Define enumerator values for game states.

const gameState = {
    Wait:        'Waiting for other player',
    Fight:       'Fight',
    PlayerWins:  'You Win!',
    PlayerLoses: 'You Lose!'
}

const color = {
    Red:  'Red',
    Blue: 'Blue'
}

const condition = {
    Neutral: 'Neutral',
    Block:   'Block',
    Punch:   'Punch'
}

// Initialize global game variables.

var socket;
var curState      = gameState.Wait;
var playerColor   = color.Red;
var playerLeft    = condition.Neutral;
var playerRight   = condition.Neutral;
var opponentColor = color.Blue;
var opponentLeft  = condition.Neutral;
var opponentRight = condition.Neutral;

// Sets the condition of the player and updates the image.
function setPlayerCondition(left, right) {
    var oldLeft  = playerLeft;
    var oldRight = playerRight;
    playerLeft  = left  || condition.Neutral;
    playerRight = right || condition.Neutral;

    // Update the images to show for the player
    var head = (curState == gameState.PlayerLoses) ? 'HeadPop' : 'Head';
    document.getElementById('leftForeImage').src = playerColor + 'Fore' + playerRight + '.png';
    document.getElementById('leftBodyImage').src = playerColor + 'Body.png';
    document.getElementById('leftHeadImage').src = playerColor + head + '.png';
    document.getElementById('leftBackImage').src = playerColor + 'Back' + playerLeft + '.png';

    // Send the new condition to the server.
    if ((oldLeft !== playerLeft) || (oldRight !== playerRight)) {
        socket.send(JSON.stringify({
            Type: 'PlayerChanged',
            Left: playerLeft,
            Right: playerRight
        }))
    }
}

// Sets the condition of the opponent and updates the image.
function setOpponentCondition(left, right) {
    opponentLeft  = left  || condition.Neutral;
    opponentRight = right || condition.Neutral;

    // Update the images to show for the opponent
    var head = (curState == gameState.PlayerWins) ? 'HeadPop' : 'Head';
    document.getElementById('rightForeImage').src = opponentColor + 'Fore' + opponentLeft + '.png';
    document.getElementById('rightBodyImage').src = opponentColor + 'Body.png';
    document.getElementById('rightHeadImage').src = opponentColor + head + '.png';
    document.getElementById('rightBackImage').src = opponentColor + 'Back' + opponentRight + '.png';
}

// Sets the game start and hides/shows the selection and game images.
function setGameState(state) {
    curState = state || gameState.Wait;
    document.getElementById('stateElem').innerHTML = state;
}

// This indicates that the player has won and updates the images.
function playersWins() {
    setGameState(gameState.PlayerWins);
    setOpponentCondition();
}

// This indicates that the opponent has won and updates the images.
function opponentWins() {
    setGameState(gameState.PlayerLoses);
    setPlayerCondition();
}

// This adds a callback for an event to the given element depending
// on what has been defined on that element.
function addEvent(element, eventName, callback) {
    if (element.addEventListener) {
        element.addEventListener(eventName, callback, false);
    } else if (element.attachEvent) {
        element.attachEvent('on' + eventName, callback);
    } else {
        element['on' + eventName] = callback;
    }
}

// This loads a JSON file from the server.
function readJSONFile(file, callback) {
    var rawFile = new XMLHttpRequest();
    rawFile.overrideMimeType("application/json");
    rawFile.open("GET", file, true);
    rawFile.onreadystatechange = function() {
        if (rawFile.readyState === 4 && rawFile.status == "200") {
            callback(JSON.parse(rawFile.responseText));
        }
    }
    rawFile.send(null);
}

// Add a listener to the whole document to listen for any key being pressed.
addEvent(document, 'keydown', function (e) {
    e = e || window.event;
    if (curState === gameState.Fight) {
        if (e.key === 'q') {
            setPlayerCondition(condition.Punch, playerRight);
        } else if (e.key === 'w') {
            setPlayerCondition(playerLeft, condition.Punch);
        } else if (e.key === 'a') {
            setPlayerCondition(condition.Block, playerRight);
        } else if (e.key === 's') {
            setPlayerCondition(playerLeft, condition.Block);
        } else if (e.key === 'p') { // For testing
            playersWins();
        } else if (e.key === 'o') { // For testing
            opponentWins();
        }
    } else {
        if (e.key === ' ') { // For testing
            setGameState((curState === gameState.Wait) ? gameState.Fight : gameState.Wait);
            setPlayerCondition();
            setOpponentCondition();
        }
    }
});

// Add a listener to the whole document to listen for any key being released.
addEvent(document, 'keyup', function (e) {
    e = e || window.event;
    if (curState === gameState.Fight) {
        if ((e.key === 'q') && (playerLeft === condition.Punch)) {
            setPlayerCondition(condition.Neutral, playerRight);
        } else if ((e.key === 'w') && (playerRight === condition.Punch)) {
            setPlayerCondition(playerLeft, condition.Neutral);
        } else if ((e.key === 'a') && (playerLeft === condition.Block)) {
            setPlayerCondition(condition.Neutral, playerRight);
        } else if ((e.key === 's') && (playerRight === condition.Block)) {
            setPlayerCondition(playerLeft, condition.Neutral);
        }
    }
});

// This handles messages coming up from the server.
function handleServerMessage(data) {
    switch (data['Type']) {
        case 'OpponentChanged':
            setOpponentCondition(data['Left'], data['Right']) 
            break;
        default:
            console.log("Unknown Message: ", data)
            break;
    }
}

// TODO: Setup rules for when a player can punch and block.
// TODO: Receive update to game state. (start fight and who won)
// TODO: Receive opponent's condition.

function main(config) {
    // Setup websocket to server
    socket = new WebSocket("ws://" + config['SocketHost'] + ":" + config['SocketPort']);
    socket.onopen = function (e) {
        console.log('Connected websocket to server');
    };
    socket.onclose = function (event) {
        if (event.wasClean) {
            console.log(`[close] Connection closed cleanly, code=${event.code} reason=${event.reason}`);
        } else {
            // e.g. server process killed or network down event.code is usually 1006 in this case
            console.log('[close] Connection died');
        }
    };
    socket.onerror = function (error) {
        console.log(`[error] ${error.message}`);
    };
    socket.onmessage = function (event) {
        handleServerMessage(JSON.parse(event.data));
    };

    // Prepare the initial state and images on the page.
    playerColor   = config['PlayerColor'];
    opponentColor = (playerColor === color.Red) ? color.Blue : color.Red;
    setGameState(gameState.Wait);
    setPlayerCondition();
    setOpponentCondition();
}

// Start main as soon as we have the config file.
readJSONFile('config.json', main)
