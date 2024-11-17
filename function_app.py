import logging
import azure.functions as func
import main
import os

app = func.FunctionApp()

@app.schedule(schedule="0 0 3 * * *", arg_name="myTimer",
              use_monitor=False) 

def TodoistTimerTrigger(myTimer: func.TimerRequest) -> None:
    if myTimer.past_due:
        logging.info('The timer is past due!')
        
    respDiego = main.mainDiego(address=os.getenv('DIEGO_EMAIL'))
    logging.info(f'Diego execution: {respDiego}')