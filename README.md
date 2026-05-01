# CITS3403-project
  
### Simple How-To  
#### Install requirements.txt:  
Run ```conda activate ur-env-name``` (reccomended, not necessary)  
Run ```pip install -r requirements.txt```  
  
#### In its own terminal for compiling tailwind:  
Run ```npm run watch:css```  
  
#### For initial set up:  
Run ```flask db init```   
Run ```flask db migrate -m "users table"```  
Run ```flask db upgrade ```  
  
#### For other updates to model:  
Run ```flask db migrate -m "change description"```  
Run ```flask db upgrade```  
  
#### For running development server:  
Run ```flask run```  