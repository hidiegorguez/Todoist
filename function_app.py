import logging
import azure.functions as func
import main
import os

app = func.FunctionApp()

@app.schedule(schedule="0 0 3 * * *", arg_name="myTimer",
              use_monitor=False) 

def TodoistDaily(myTimer: func.TimerRequest) -> None:
    if myTimer.past_due:
        logging.info('The timer is past due!')
        
    respDiego = main.TodoistDaily(address=os.getenv('DIEGO_EMAIL'))
    logging.info(f'Diego execution: {respDiego}')
    
    
@app.schedule(schedule="0 55 11 * * *", arg_name="myTimer",
              use_monitor=False) 

def TodoistSuperBet(myTimer: func.TimerRequest) -> None:
    if myTimer.past_due:
        logging.info('The timer is past due!')
        
    respSuperBet = main.TodoistSuperBet(address=os.getenv('DIEGO_EMAIL'))
    logging.info(f'SuperBet execution: {respSuperBet}')