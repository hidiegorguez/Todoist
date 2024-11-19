import logging
import azure.functions as func
import main
import os

mainDiego = main.MainDiego(todoist_api_token=os.getenv('TODOIST_API_TOKEN'))
addressDiego = os.getenv('DIEGO_EMAIL')

app = func.FunctionApp()

@app.schedule(schedule="0 0 3 * * *", arg_name="myTimer", use_monitor=False) 
def TodoistDaily(myTimer: func.TimerRequest) -> None:
    if myTimer.past_due:
        logging.info('The timer is past due!')
        
    respDiego = mainDiego.TodoistDaily(address=addressDiego)
    logging.info(f'Diego execution: {respDiego}')
    
    
@app.schedule(schedule="0 55 11 * * *", arg_name="myTimer", use_monitor=False, run_on_startup=True) 
def TodoistSuperBet(myTimer: func.TimerRequest) -> None:
    if myTimer.past_due:
        logging.info('The timer is past due!')
        
    respSuperBet = mainDiego.TodoistSuperBet()
    logging.info(f'SuperBet execution: {respSuperBet}')