"""
Details the various flask endpoints for processing and retrieving
command details as well as a swagger spec endpoint
"""

from multiprocessing import Process, Queue
import sys
import os
from flask import Flask, request, jsonify
from flask_swagger import swagger
from flask_api import status

from db import engine
from base import Base, Command
from werkzeug.utils import secure_filename
from logger import logger
from config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND, UPLOAD_FOLDER, ALLOWED_EXTENSIONS

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['CELERY_BROKER_URL'] = CELERY_BROKER_URL
app.config['CELERY_RESULT_BACKEND'] = CELERY_RESULT_BACKEND


@app.route('/commands', methods=['GET'])
def get_command_output():
    """
    Returns as json the command details that have been processed
    ---
    tags: [commands]
    responses:
      200:
        description: Commands returned OK
      400:
        description: Commands not found
    """
    try:
        commands = Command.query.all()
        if commands:
            logger.info("Request processed successfully.")
            return jsonify([command.serialize() for command in commands]), status.HTTP_200_OK
        else:
            logger.error("No commands found in database.")
            return "Commands not found", status.HTTP_404_NOT_FOUND
    except Exception as e:
        logger.error(str(e))
        return str(e), status.HTTP_500_INTERNAL_SERVER_ERROR


def allowed_file(filename):
    """
    Prevents users from uploading any file having extension other than .txt
    Necessary precaution measure on server
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/commands', methods=['POST'])
def process_commands():
    """
    Processes commmands from a command list
    ---
    tags: [commands]
    parameters:
      - name: filename
        in: formData
        description: filename of the commands text file to parse
        required: true
        type: string
    responses:
      200:
        description: Processing OK
    """
    try:
        if 'file_data' in request.files:
            file_data = request.files['file_data']
            if file_data and allowed_file(file_data.filename):
                fi = secure_filename(file_data.filename)
                file_data.save(os.path.join(app.config['UPLOAD_FOLDER'], fi))
        else:
            fi = request.args.get('filename')

        from command_parser import get_valid_commands, process_command_output
        queue = Queue()
        get_valid_commands(queue, fi)
        processes = [Process(target=process_command_output, args=(queue,))]
        for process in processes:
            process.start()
        for process in processes:
            process.join()

        logger.info("All commands processed successfully.")
        return 'Successfully processed commands.', status.HTTP_200_OK
    except Exception as e:
        logger.error(str(e))
        return str(e), status.HTTP_500_INTERNAL_SERVER_ERROR


@app.route('/database', methods=['POST'])
def make_db():
    """
    Creates database schema
    ---
    tags: [db]
    responses:
      200:
        description: DB Creation OK
    """
    try:
        Base.metadata.create_all(engine)
        logger.info("Database created successfully.")
        return 'Database creation successful.'
    except Exception as e:
        logger.error(str(e))
        return "Error in creating database", status.HTTP_500_INTERNAL_SERVER_ERROR


@app.route('/database', methods=['DELETE'])
def drop_db():
    """
    Drops all db tables
    ---
    tags: [db]
    responses:
      200:
        description: DB table drop OK
    """
    try:
        Base.metadata.drop_all(engine)
        logger.info("Database deletion successful.")
        return 'Database deletion successful.'
    except Exception as e:
        logger.error(str(e))
        return 'Error in Deleting database', status.HTTP_500_INTERNAL_SERVER_ERROR


if __name__ == '__main__':
    """
    Starts up the flask server
    """
    port = 8080
    use_reloader = True

    # provides some configurable options
    for arg in sys.argv[1:]:
        if '--port' in arg:
            port = int(arg.split('=')[1])
        elif '--use_reloader' in arg:
            use_reloader = arg.split('=')[1] == 'true'

    app.run(port=port, debug=True, use_reloader=use_reloader)


@app.route('/spec')
def swagger_spec():
    """
    Display the swagger formatted JSON API specification.
    ---
    tags: [docs]
    responses:
      200:
        description: OK status
    """
    spec = swagger(app)
    spec['info']['title'] = "Nervana cloud challenge API"
    spec['info']['description'] = ("Nervana's cloud challenge " +
                                   "for interns and full-time hires")
    spec['info']['license'] = {
        "name": "Nervana Proprietary License",
        "url": "http://www.nervanasys.com",
    }
    spec['info']['contact'] = {
        "name": "Nervana Systems",
        "url": "http://www.nervanasys.com",
        "email": "info@nervanasys.com",
    }
    spec['schemes'] = ['http']
    spec['tags'] = [
        {"name": "db", "description": "database actions (create, delete)"},
        {"name": "commands", "description": "process and retrieve commands"}
    ]
    return jsonify(spec)
