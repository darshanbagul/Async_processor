import subprocess
from threading import Timer
import time
from base import Command
from celery import Celery
from main import app
from db import session
from logger import logger
from config import TIME_OUT

"""
Handles the work of validating and processing command input.
"""

celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

def get_valid_commands(queue, fi):
    # TODO: efficiently evaluate commands
    try:
        with open(fi) as f:
            command_list = f.readlines()
        start_ind = command_list.index("[COMMAND LIST]\n")
        end_ind = command_list.index("[VALID COMMANDS]\n")

        validated = []
        if start_ind < end_ind and end_ind < len(command_list):
            commands = command_list[start_ind+1:end_ind]
            valid_commands = command_list[end_ind:len(command_list)]
            validated = list(set(commands).intersection(valid_commands))
        elif end_ind < start_ind:
            valid_commands = command_list[end_ind+1:start_ind]
            commands = command_list[start_ind:len(command_list)]
            validated = list(set(commands).intersection(valid_commands))

        if validated:
            for command in validated:
                queue.put(command)
    except Exception as e:
        raise e

@celery.task
def run_command_with_timeout(command):
    """Execute 'command' in a subprocess and enforce timeout 'TIME_OUT' seconds.
 
    Return subprocess exit code on natural completion of the subprocess.
    Raise an exception if timeout expires before subprocess completes."""
    start_time = time.time()
    proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    timer = Timer(TIME_OUT, proc.kill)
    timer.start()
    if timer.is_alive():
        # Process completed naturally - cancel timer and return exit code
        output, err = proc.communicate()
        print output
        timer.cancel()
    end_time = time.time()
    duration = end_time - start_time
    if duration > TIME_OUT-1:
        duration = 0
    db_entry = Command(command, len(command), duration, output)
    session.add(db_entry)
    session.commit()
    # Process killed by timer - raise exception
    logger.error('Process #%d killed after %f seconds' % (proc.pid, TIME_OUT))

def process_command_output(queue):
    # TODO: run the command and put its data in the db
    try:
        while queue.empty() == False:
            command = queue.get()
            command = command.strip('\n')
            if not Command.query.filter(Command.command_string == command).first():
                output = run_command_with_timeout.delay(command)
    except Exception as e:
        logger.error(str(e))
    return
