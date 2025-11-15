import logging
import azure.functions as func
import main
import os
from datetime import datetime

mainDiego = main.MainDiego(todoist_api_token=os.getenv('TODOIST_API_TOKEN'))
addressDiego = os.getenv('DIEGO_EMAIL')

app = func.FunctionApp()

@app.schedule(schedule="0 0 4 * * *", arg_name="myTimer", use_monitor=False) 
def TodoistDaily(myTimer: func.TimerRequest) -> None:
    if myTimer.past_due:
        logging.info('The timer is past due!')
        
    respDiego = mainDiego.TodoistDaily(address=addressDiego)
    logging.info(f'Diego execution: {respDiego}')
    
    
@app.schedule(schedule="0 55 11,15,17 * * *", arg_name="myTimer", use_monitor=False) 
def TodoistSuperBet(myTimer: func.TimerRequest) -> None:
    if myTimer.past_due:
        logging.info('The timer is past due!')
        
    today = datetime.today()
    respSuperBet = mainDiego.TodoistSuperBet(hour=today.hour)
    logging.info(f'SuperBet execution: {respSuperBet}')
    
    
@app.schedule(schedule="0 55 19 * * *", arg_name="myTimer", use_monitor=False) 
def TodoistWhatsapp(myTimer: func.TimerRequest) -> None:
    if myTimer.past_due:
        logging.info('The timer is past due!')
        
    respWhatsapp = mainDiego.TodoistWhatsapp()
    logging.info(f'Whatsapp execution: {respWhatsapp}')
    
    
@app.schedule(schedule="0 55 20 * * *", arg_name="myTimer", use_monitor=False) 
def TodoistHealthcare(myTimer: func.TimerRequest) -> None:
    if myTimer.past_due:
        logging.info('The timer is past due!')
        
    respHealthcare = mainDiego.TodoistHealthcare()
    logging.info(f'Healthcare execution: {respHealthcare}')
        
        
# @app.schedule(schedule="0 0 * * 2", arg_name="myTimer", use_monitor=False)
# def TodoistToDoLP(myTimer: func.TimerRequest) -> None:
#     if myTimer.past_due:
#         logging.info('The timer is past due!')
        
#     respToDoLP = mainDiego.TodoistToDoLP(address=addressDiego)
#     logging.info(f'ToDoLP execution: {respToDoLP}')
    
@app.schedule(schedule="0 55 13 * * *", arg_name="myTimer", use_monitor=False)
def TodoistWeather(myTimer: func.TimerRequest) -> None:
    if myTimer.past_due:
        logging.info('The timer is past due!')
        
    respWeather = mainDiego.TodoistWeather()
    logging.info(f'Weather execution: {respWeather}')