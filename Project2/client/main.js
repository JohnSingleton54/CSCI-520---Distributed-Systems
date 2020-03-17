const gameState = {
    Init:        'Select your player',
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

var curState      = gameState.Init;
var playerColor   = color.Red;
var playerLeft    = condition.Neutral;
var playerRight   = condition.Neutral;
var playerLose    = false;
var opponentColor = color.Blue;
var opponentLeft  = condition.Neutral;
var opponentRight = condition.Neutral;
var opponentLose  = false;

// Get HTML elements that will be updated by the game.

var stateElem   = document.getElementById('stateElem');
var selectGroup = document.getElementById('selectGroup');
var leftSelect  = document.getElementById('leftSelect');
var rightSelect = document.getElementById('rightSelect');
var gameGroup   = document.getElementById('gameGroup');

var leftForeImage  = document.getElementById('leftForeImage');
var leftBodyImage  = document.getElementById('leftBodyImage');
var leftHeadImage  = document.getElementById('leftHeadImage');
var leftBackImage  = document.getElementById('leftBackImage');

var rightForeImage = document.getElementById('rightForeImage');
var rightBodyImage = document.getElementById('rightBodyImage');
var rightHeadImage = document.getElementById('rightHeadImage');
var rightBackImage = document.getElementById('rightBackImage');

// Sets the condition of the player and updates the image.
function setPlayerCondition(left, right, lose) {
    playerLeft  = left;
    playerRight = right;
    playerLose  = lose;
    leftForeImage.src = playerColor + 'Fore' + playerRight + '.png';
    leftBodyImage.src = playerColor + 'Body.png';
    leftHeadImage.src = playerColor + (lose ? 'HeadPop' : 'Head') + '.png';
    leftBackImage.src = playerColor + 'Back' + playerLeft + '.png';
}

// Sets the condition of the opponent and updates the image.
function setOpponentCondition(left, right, lose) {
    opponentLeft = left;
    opponentRight = right;
    opponentLose = lose;
    rightForeImage.src = opponentColor + 'Fore' + opponentLeft + '.png';
    rightBodyImage.src = opponentColor + 'Body.png';
    rightHeadImage.src = opponentColor + (lose ? 'HeadPop' : 'Head') + '.png';
    rightBackImage.src = opponentColor + 'Back' + opponentRight + '.png';
}

// Sets the game start and hides/shows the selection and game images.
function setGameState(state) {
    curState = state;
    stateElem.innerHTML = state;
    showSelection = (curState === gameState.Init);
    selectGroup.style.display = showSelection ? 'block' : 'none';
    gameGroup.style.display   = showSelection ? 'none' : 'block';
}

// This is called when a player has picked the color they want to play as.
// The color doesn't actually matter since the players could be defined by
// their connection in the client server.
function makeColorSelection(clr) {
    if (curState === gameState.Init) {
        playerColor = clr;
        opponentColor = (clr === color.Red) ? color.Blue : color.Red;
        setGameState(gameState.Wait);
        setPlayerCondition(condition.Neutral, condition.Neutral, false);
        setOpponentCondition(condition.Neutral, condition.Neutral, false);
    }
}

// This indicates that the player has won and updates the images.
function playersWins() {
    setGameState(gameState.PlayerWins);
    setPlayerCondition(condition.Neutral, condition.Neutral, false);
    setOpponentCondition(condition.Neutral, condition.Neutral, true);
}

// This indicates that the opponent has won and updates the images.
function opponentWins() {
    setGameState(gameState.PlayerLoses);
    setPlayerCondition(condition.Neutral, condition.Neutral, true);
    setOpponentCondition(condition.Neutral, condition.Neutral, false);
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

// Prepare the initial state and images on the page.
setGameState(gameState.Init);
setPlayerCondition(condition.Neutral, condition.Neutral, false);
setOpponentCondition(condition.Neutral, condition.Neutral, false);

// Add a listener to the left image for selecting Red as the player's color.
addEvent(leftSelect, 'click', function () {
    makeColorSelection(color.Red);
});

// Add a listener to the right image for selecting Blue as the player's color.
addEvent(rightSelect, 'click', function () {
    makeColorSelection(color.Blue);
});

// Add a listener to the whole document to listen for any key being pressed.
addEvent(document, 'keydown', function (e) {
    e = e || window.event;
    if (curState === gameState.Fight) {
        if (e.key === 'q') {
            setPlayerCondition(condition.Punch, playerRight, false);
        } else if (e.key === 'w') {
            setPlayerCondition(playerLeft, condition.Punch, false);
        } else if (e.key === 'a') {
            setPlayerCondition(condition.Block, playerRight, false);
        } else if (e.key === 's') {
            setPlayerCondition(playerLeft, condition.Block, false);
        } else if (e.key === 'p') { // For testing
            playersWins();
        } else if (e.key === 'o') { // For testing
            opponentWins();
        }
    } else if (curState === gameState.Wait) {
        if (e.key === ' ') { // For testing
            setGameState(gameState.Fight);
            setPlayerCondition(condition.Neutral, condition.Neutral, false);
            setOpponentCondition(condition.Neutral, condition.Neutral, false);
        }
    } else if ((curState === gameState.PlayerWins) || (curState === gameState.PlayerLoses)) {
        if (e.key === ' ') { // For testing
            curState = gameState.Init;
            setGameState(gameState.Init);
            setPlayerCondition(condition.Neutral, condition.Neutral, false);
            setOpponentCondition(condition.Neutral, condition.Neutral, false);
        }
    }
});

// Add a listener to the whole document to listen for any key being released.
addEvent(document, 'keyup', function (e) {
    e = e || window.event;
    if (curState === gameState.Fight) {
        if ((e.key === 'q') && (playerLeft === condition.Punch)) {
            setPlayerCondition(condition.Neutral, playerRight, false);
        } else if ((e.key === 'w') && (playerRight === condition.Punch)) {
            setPlayerCondition(playerLeft, condition.Neutral, false);
        } else if ((e.key === 'a') && (playerLeft === condition.Block)) {
            setPlayerCondition(condition.Neutral, playerRight, false);
        } else if ((e.key === 's') && (playerRight === condition.Block)) {
            setPlayerCondition(playerLeft, condition.Neutral, false);
        }
    }
});

// TODO: Setup connection to server.
// TODO: Setup rules for when a player can punch and block.
// TODO: Receive update to game state. (start fight and who won)
// TODO: Send player's condition.
// TODO: Receive opponent's condition.
