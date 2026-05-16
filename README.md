<div align="center">
    <h1>★ RateRace — Which Movie Rates Higher?</h1>
    <span style="font-size: 1.25em; font-weight: bold;">
        <p style="margin-bottom: 0;">Two films. One question.</p>
        <p style="margin-top: 0;">Guess which has the higher IMDb score and climb the ranks.</p>
    </span>
</div>

### Cits3403 Project
Welcome to RateRace, a full-stack Flask based web game where users compare 10 movie pairs and attempt to guess the higher-rated film. The goal of the project is to provide an simple competitive movie-ranking game for a player of any entry level, that is both engaging and entertaining. 
### RateRace offers:
* Dynamic gameplay - With 10 round long games, timer constraints and correctness of answer affect score and outcome of a match
* Dynamic movie fetching - When a game is launched, movies in the database are fetched from the `TMDB` api when a game is played and either; the movie cache is low, or it has been atleast 3 days since the last fetch.
* Gamemodes:
  * Standard Mode - Played with a set of random movies
  * Daily Mode - Played with a global set of movies that are generated for each day. Also offers play through history of Daily Games that can be selected through a dropdown panel
  * Challenge Mode (PVP) - Played as a real-time challenge between two players, with random movie pairs sent simultaneously.
* Global Leaderboard - To track the stats of a users play history. The leaderboard also offers:
  * A challenge button to request a challenge against any user that is active
  * Profile page with more stats when a players name is selected
* Score track of daily games and other games.

### Design and Architecture
On the frontend, this application is built with HTML, Tailwind CSS, and JavaScript. Fetch API and SocketIO are used for realtime updates and game logic, while on the backend, this application uses the Flask python library with several other extensions (as specified in `requirements.txt`) for API endpoints, field validation and real-time event handlers.

 The application uses server-side rendering, `render_template()` for front end navigation, however client-side rendering is used for part of the application using AJAX, particularly with for the transitions between game rounds and game mode selection for all game-modes. The challenge mode and single player modes do however differ, in that round and match validation for challenge mode uses server-side logic with WebSockets to ensure fairness and synchronisation between both players, while single player game logic is handled client-side.

**Group Members**
| UWA ID   | Name            | Github Username |
|----------|-----------------|-----------------|
| 24273259 | Kush Patel      | KushPatel-18    |
|          | Dean Kalweit    | flamedphoenix   |
|          | Roland Levinson | ggtroland       |
### Simple Launch Instructions
#### Set up Initial Project Files:  
#### In its own terminal for compiling tailwind:  
Run ```npm run watch:css```  
#### Initialise and Launch - in it's own terminal:  
#### Database Management / Updates
#### Running the Tests
<div align="center">
★   RateRace — CITS3403 Project — 2026   ★
</div>