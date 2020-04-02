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

const punchTimeout = 250; // in milliseconds

// Initialize global game variables.

var socket;
var curState = gameState.Fight;

var playerColor = color.Red;
var playerLeft  = condition.Neutral;
var playerRight = condition.Neutral;
var playerLeftPunchTimeout;
var playerRightPunchTimeout;

var opponentColor = color.Blue;
var opponentLeft  = condition.Neutral;
var opponentRight = condition.Neutral;
var opponentLeftPunchTimeout;
var opponentRightPunchTimeout;

// Updates the player's images.
function updatePlayerImages() {
    var head = (curState == gameState.PlayerLoses) ? 'HeadPop' : 'Head';
    document.getElementById('leftForeImage').src = playerColor + 'Fore' + playerRight + '.png';
    document.getElementById('leftBodyImage').src = playerColor + 'Body.png';
    document.getElementById('leftHeadImage').src = playerColor + head + '.png';
    document.getElementById('leftBackImage').src = playerColor + 'Back' + playerLeft + '.png';
}

// Updates the opponent's images.
function updateOpponentImages() {
    var head = (curState == gameState.PlayerWins) ? 'HeadPop' : 'Head';
    document.getElementById('rightForeImage').src = opponentColor + 'Fore' + opponentLeft + '.png';
    document.getElementById('rightBodyImage').src = opponentColor + 'Body.png';
    document.getElementById('rightHeadImage').src = opponentColor + head + '.png';
    document.getElementById('rightBackImage').src = opponentColor + 'Back' + opponentRight + '.png';
}

// Sets the game start and hides/shows the selection and game images.
function setGameState(state) {
    curState = state || gameState.Fight;
    document.getElementById('stateElem').innerHTML = state;
    playerLeft  = condition.Neutral;
    playerRight = condition.Neutral;
    updatePlayerImages();
    opponentLeft  = condition.Neutral;
    opponentRight = condition.Neutral;
    updateOpponentImages();
}

// This indicates that the player or opponent has won and updates the images.
function gameOver(youWin) {
    setGameState(youWin ? gameState.PlayerWins : gameState.PlayerLoses);
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
        switch (e.key) {
            case 'q': socket.send('LeftPunch');  break;
            case 'w': socket.send('RightPunch'); break;
            case 'a': socket.send('LeftBlock');  break;
            case 's': socket.send('RightBlock'); break;
            case 'p': socket.send('TestWin');    break;
            case 'o': socket.send('TestLose');   break;
        }
    }
    if (e.key === 'r') socket.send('Reset');
});

// This cancels any other time which is counting down to reset the punch.
// If the given value is a punch, it will start a new timer to reset it by calling the given handle.
function setPunchTimeout(timeout, value, handle) {
    if (timeout != null) {
        window.clearTimeout(timeout);
        timeout = null;
    }
    if (value === condition.Punch) {
        timeout = window.setTimeout(handle, punchTimeout);
    }
    return timeout;
}

// This sets the condition of one of the player's hands.
// It also sets a timer to automatically re-render the punch being pulled back in.
function setPlayerCondition(hand, value) {
    if (hand == 'Left') {
        playerLeft = value;
        playerLeftPunchTimeout = setPunchTimeout(playerLeftPunchTimeout, value, function () {
            playerLeft = condition.Neutral;
            updatePlayerImages();
        });
    } else {
        playerRight = value;
        playerRightPunchTimeout = setPunchTimeout(playerRightPunchTimeout, value, function () {
            playerRight = condition.Neutral;
            updatePlayerImages();
        });
    }
    updatePlayerImages();
}

// This sets the condition of one of the opponent's hands.
// It also sets a timer to automatically re-render the punch being pulled back in.
function setOpponentCondition(hand, value) {
    if (hand == 'Left') {
        opponentLeft = value;
        opponentLeftPunchTimeout = setPunchTimeout(opponentLeftPunchTimeout, value, function () {
            opponentLeft = condition.Neutral;
            updateOpponentImages();
        });
    } else {
        opponentRight = value;
        opponentRightPunchTimeout = setPunchTimeout(opponentRightPunchTimeout, value, function () {
            opponentRight = condition.Neutral;
            updateOpponentImages();
        });
    }
    updateOpponentImages();
}

// This handles messages coming up from the server.
function handleServerMessage(data) {
    switch (data['Type']) {
        case 'PlayerChanged':
            if ('Left' in data) 
                setPlayerCondition('Left', data['Left']);
            if ('Right' in data) 
                setPlayerCondition('Right', data['Right']);
            break;
        case 'OpponentChanged':
            if ('Left' in data) 
                updateOpponentImages('Left', data['Left']);
            if ('Right' in data) 
                updateOpponentImages('Right', data['Right']);
            break;
        case 'GameOver':
            gameOver(data['YouWin']);
            break;
        case 'Reset':
            setGameState(gameState.Fight);
            break;
        default:
            console.log("Unknown Message: ", data);
            break;
    }
}

function main(config) {
    // Setup websocket to server
    socket = new WebSocket("ws://" + config['SocketURL']);
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
        //console.log(`received: ${event.data}`);
        handleServerMessage(JSON.parse(event.data));
    };

    // Prepare the initial state and images on the page.
    playerColor   = config['PlayerColor'];
    opponentColor = (playerColor === color.Red) ? color.Blue : color.Red;
    setGameState(gameState.Fight);
}

// Start main as soon as we have the config file.
readJSONFile('config.json', main);
