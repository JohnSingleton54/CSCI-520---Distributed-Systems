const gameState = {
    Init:     'Init',     // The initial state of the game were you can pick your color.
    Wait:     'Wait',     // Waiting for the other player to pick their color.
    Fight:    'Fight',    // Main part of the game.
    RedWins:  'RedWins',  // Game over with Red winning.
    BlueWins: 'BlueWins', // Game over with Blue winning.
}

const color = {
    Red:  'Red',
    Blue: 'Blue'
}

const condition = {
    Neutral:    'Neutral',
    Lose:       'Lose',
    LeftBlock:  'LeftBlock',
    LeftPunch:  'LeftPunch',
    RightBlock: 'RightBlock',
    RightPunch: 'RightPunch'
}

// Initialize Game variables
var curState = gameState.Init;
var playerColor   = color.Red;
var opponentColor = color.Blue;
var playerCondition   = condition.Neutral;
var opponentCondition = condition.Neutral;

// Get HTML elements that will be updated by the game.
var stateElem    = document.getElementById("state");
var leftImgElem  = document.getElementById("leftImage");
var rightImgElem = document.getElementById("rightImage");

// Updates the status text box at the top of the game to show the state of the game.
function updateState() {
    if (curState === gameState.Init) {
        stateElem.innerHTML = "Select your player";
    } else if (curState === gameState.Wait) {
        stateElem.innerHTML = "Waiting for other player";
    } else if (curState === gameState.Fight) {
        stateElem.innerHTML = "Fight";
    } else if (curState === gameState.BlueWins) {
        stateElem.innerHTML = "Blue Wins!";
    } else { // curState === gameState.RedWins
        stateElem.innerHTML = "Red Wins!"; 
    }
}

// Sets the condition of the player and updates the image.
function setPlayerCondition(cond) {
    playerCondition = cond;
    if (curState === gameState.Init) {
        leftImgElem.className = "clickable";
        leftImgElem.src = "RedSelect.png";
    } else { // including Wait
        leftImgElem.className = (playerColor === color.Blue) ? "flip" : "";
        leftImgElem.src = playerColor + playerCondition + ".png";
    }
}

// Sets the conditions of the opponent and updates the image.
function setOpponentCondition(cond) {
    opponentCondition = cond;
    if (curState === gameState.Init) {
        rightImgElem.className = "clickable";
        rightImgElem.src = "BlueSelect.png";
    } else if (curState === gameState.Wait) {
        rightImgElem.className = (opponentColor === color.Red) ? "flip grayedOut" : "grayedOut";
        rightImgElem.src = opponentColor + condition.Neutral + ".png";
    } else {
        rightImgElem.className = (opponentColor === color.Red) ? "flip" : "";
        rightImgElem.src = opponentColor + opponentCondition + ".png";
    }
}

// This is called when a player has picked the color they want to play as.
// The color doesn't actually matter since the players will be described by
// their connection in the client server.
function makeColorSelection(clr) {
    if (curState === gameState.Init) {
        playerColor = clr;
        opponentColor = (clr === color.Red) ? color.Blue : color.Red;
        curState = gameState.Wait;
        updateState();
        setPlayerCondition(condition.Neutral);
        setOpponentCondition(condition.Neutral);
    }
}

// This indicates that the player has won and updates the images.
function playersWins() {
    curState = (playerColor === color.Red) ? gameState.RedWins : gameState.BlueWins;
    updateState();
    setPlayerCondition(condition.Neutral);
    setOpponentCondition(condition.Lose);
}

// This indicates that the opponent has won and updates the images.
function opponentWins() {
    curState = (opponentColor === color.Red) ? gameState.RedWins : gameState.BlueWins;
    updateState();
    setPlayerCondition(condition.Lose);
    setOpponentCondition(condition.Neutral);
}

// This adds a callback for an event to the given element depending
// on what has been defined on that element.
function addEvent(element, eventName, callback) {
    if (element.addEventListener) {
        element.addEventListener(eventName, callback, false);
    } else if (element.attachEvent) {
        element.attachEvent("on" + eventName, callback);
    } else {
        element["on" + eventName] = callback;
    }
}

// Prepare the initial state and images on the page.
updateState();
setPlayerCondition(condition.Neutral);
setOpponentCondition(condition.Neutral);

// Add a listener to the left image for selecting Red as the player's color.
addEvent(leftImgElem, "click", function () {
    makeColorSelection(color.Red);
});

// Add a listener to the right image for selecting Blue as the player's color.
addEvent(rightImgElem, "click", function () {
    makeColorSelection(color.Blue);
});

// Add a listener to the whole document to listen for any key being pressed.
addEvent(document, "keydown", function (e) {
    e = e || window.event;
    if (curState === gameState.Fight) {
        if (e.key === 'q') {
            setPlayerCondition(condition.LeftPunch);
        } else if (e.key === 'w') {
            setPlayerCondition(condition.RightPunch);
        } else if (e.key === 'a') {
            setPlayerCondition(condition.LeftBlock);
        } else if (e.key === 's') {
            setPlayerCondition(condition.RightBlock);
        } else if (e.key === 'p') { // For testing
            playersWins();
        } else if (e.key === 'o') { // For testing
            opponentWins();
        }
    } else if (curState === gameState.Wait) {
        if (e.key === ' ') { // For testing
            curState = gameState.Fight;
            updateState();
            setPlayerCondition(condition.Neutral);
            setOpponentCondition(condition.Neutral);
        }
    } else if ((curState === gameState.RedWins) || (curState === gameState.BlueWins)) {
        if (e.key === ' ') { // For testing
            curState = gameState.Init;
            updateState();
            setPlayerCondition(condition.Neutral);
            setOpponentCondition(condition.Neutral);
        }
    }
});

// Add a listener to the whole document to listen for any key being released.
addEvent(document, "keyup", function () {
    if (curState === gameState.Fight) {
        setPlayerCondition(condition.Neutral);
    }
});

// TODO: Setup rules for when a player can punch and block.
// TODO: Setup connection to server.
// TODO: Receive update to game state. (start fight and who won)
// TODO: Send player's condition.
// TODO: Receive opponent's condition.
