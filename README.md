# Nervana Cloud Coding Challenge #

You are to build a server that processes valid bash command strings.
Your server takes the command strings from commands.txt and does the following:

## Tasks Completed: ##

1. The server checks that the command strings in the COMMAND_LIST section are valid command strings by cross-checking with the VALID_command strings section. Regardless of the command itself, the command string needs to exactly match a command in the valid command strings list.
   Ex: `grep "tacos" commands.txt` isn't valid, but `grep "pwd" commands.txt` is.

Assuming the command is valid:
2. Stores metadata about each command:
    - actual command itself as a string
    - length of command string
    - time to complete (up to 1 min, else mark as 0)
    - eventual output (see below)
3. Grabs the command output from each command if possible.
4. Stores the output in the db provided.
5. Enables the data to be fetched via the endpoint provided in the code.

6. The processing of commands is ASYNCHRONOUS i.e, the processing follows a non-blocking paradigm, given some commands take large times for execution blocking other requests. This is enabled using Celery worker.

7. The text(.txt) file containing the commands can be uploaded to the server via a post request, with 'file_data' as the key in the request headers. In case file is not uploaded, and a file already present on the server has to be used, provide the full path of the file location or just the file name (if present in same folder as server) via a post request, with 'filename' as the key in the request header.

8. The server ensures that the uploaded file is just a text file for security concerns. For additional security, there are checks which prevent any malicious activity to sensitive files such as '.bashrc'.

9. The code has been well commented and stores request logs for better understanding and debugging.


### For how to run either project ###
1. `make run` to start the project; see the `Makefile` for other helpful things like `make swagger`
2. Ensure Redis Server is running as a background process : redis-server &
3. Run the celery worker with this command: celery worker -A command_parser.celery --loglevel=info
4. You can then hit it to either drop the db, init the db, fetch results, input data (curl or python requests).
   - Sample request to feed in the data: requests.post("http://127.0.0.1:8080/commands", params={'filename': 'commands.txt'})