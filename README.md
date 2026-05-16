<div align="center">
    <h1>★ RateRace — Which Movie Rates Higher?</h1>
    <span style="font-size: 1.25em; font-weight: bold;">
        <p style="margin-bottom: 0;">Two films. One question.</p>
        <p style="margin-top: 0;">Guess which has the higher IMDb score and climb the ranks.</p>
    </span>
</div>

## Cits3403 Project   

Welcome to RateRace, a full-stack Flask based web game where users compare 10 movie pairs and attempt to guess the higher-rated film. The goal of the project is to provide an simple competitive movie-ranking game for a player of any entry level, that is both engaging and entertaining.     

## RateRace offers:
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

---
## Design and Architecture
On the frontend, this application is built with HTML, Tailwind CSS, and JavaScript. Fetch API and SocketIO are used for realtime updates and game logic, while on the backend, this application uses the Flask python library with several other extensions (as specified in `requirements.txt`) for API endpoints, field validation and real-time event handlers.

 The application uses server-side rendering, `render_template()` for front end navigation, however client-side rendering is used for part of the application using AJAX, particularly with for the transitions between game rounds and game mode selection for all game-modes. The challenge mode and single player modes do however differ, in that round and match validation for challenge mode uses server-side logic with WebSockets to ensure fairness and synchronisation between both players, while single player game logic is handled client-side.

---

## Group Members
| UWA ID   | Name            | Github Username |
|----------|-----------------|-----------------|
| 24273259 | Kush Patel      | KushPatel-18    |
|          | Dean Kalweit    | flamedphoenix   |
|          | Roland Levinson | ggtroland       |

---
## Simple Launch Instructions
### Set up Initial Project Files:  
Run ```git clone https://github.com/flamedphoenix/CITS3403-project``` in target directory to clone the repository, and then `cd CITS3403-project` 
Run ```python3 -m venv app-env``` to set-up virtual environment (reccomended, not necessary)    
Activate the environment on:
* Windows:
```venv\Scripts\activate``` 
* Mac / Linux:  
```source venv/bin/activate``` 

Run ```pip install -r requirements.txt```  to install dependencies    
Create ```.env``` in project root to start configuring environment, and add `SECRET_KEY=` and `TMDB_API_KEY=` with your respective keys at the end  
  
### In its own terminal for compiling tailwind:  
If not installed already: 
Run ```npm install```, and then run
Run ```npm run watch:css```  
  
### Initialise and Launch - in it's own terminal:  
Run `python3 run.py` - already configured to apply database migrations

Visit http://127.0.0.1:5020 to start playing!

### Database Management / Updates
If models are updated in `models.py`, then in project root directory,       
Run ```flask --app run db migrate -m "change description"```    
Run ```flask --app run db upgrade``` (or run `run.py` again)    
If models need to be downgraded:    
Run ```flask --app run db downgrade```    

---

### Running the Tests
**UnitTests for Game, API, Models, and User Auth**:     
In a separate terminal run:        
```
python3 -m unittest tests/test_models_auth.py
python3 -m unittest tests/test_game_api.py
```

**System Tests**    
Run ```python3 -m pytest tests/test_selenium.py``` if you want to see the test windows      
or
Run ```HEADLESS=1 python3 -m pytest tests/test_selenium.py``` if you don't want browser window      

---

## Web Page Previews
### Standard Game Pages

| Standard Game Screen   | Game Start Screen with Daily Game History Panel       |
|------------------------|--------------------------|
| <img width="1470" height="767" alt="Game-Standard" src="https://github.com/user-attachments/assets/bf12edfd-1111-4ac2-814a-9c4a216b9b0c" />        | <img width="1469" height="767" alt="Daily-history-panel-game" src="https://github.com/user-attachments/assets/de6a41d7-2aac-41ad-9e8f-6368c3a425c5" />|

### Leaderboard Pages
| Leaderboard Page and Challenge Page  | Challenge Game |
|-------------------------------|---------------------------------|
| <img width="1463" height="753" alt="Leaderboard-and-Challenge" src="https://github.com/user-attachments/assets/ff72a56f-d935-4a04-91d2-41ebc986edc9" />         | <img width="1456" height="756" alt="Challenge-Game" src="https://github.com/user-attachments/assets/4d051200-cb2d-4575-9b4f-14eabc3877ad" />       |

### Daily Challenge
|           Daily Challenge                                                                                                                   |
|---------------------------------------------------------------------------------------------------------------------------------------------|
|<img width="1466" height="766" alt="Daily-Challenge" src="https://github.com/user-attachments/assets/75e331d9-8b5d-4758-8c0e-b68b72124dda" />|

<details>
<summary><h3><strong>Click to See User Profile Page</strong></h3></summary>
    
![User Profile Page](https://github.com/user-attachments/assets/7962836c-394e-42b0-9222-4006b05a338a)
</details>
<details>
<summary><h3><strong>Click to See Home / Index Page</strong></h3></summary>
    
![Index page](https://github.com/user-attachments/assets/c4c4705c-3c5e-496e-94fd-18ac0e72e811)
</details>

---

<div align="center">
★   RateRace — CITS3403 Project — 2026   ★
</div>
