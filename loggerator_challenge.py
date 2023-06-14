"""
This script uses Flask to expose a REST endpoint (/logs) for retrieving and filtering logs from the running 
'loggerator' Docker container. The endpoint accepts 'code', 'method', and 'user' as optional query parameters to filter the logs 
and returns the matching logs in descending time order.
"""
import datetime
import docker
import logging
import re
import socket

from flask import Flask, request, jsonify

'''
Rationale for third party libraries:

docker: Using the Docker SDK for Python to run and connect to the loggerator

Flask: Using Flask to define the /logs REST endpoint and handle incoming HTTP requests and outgoing JSON responses.
'''

app = Flask(__name__)
client = docker.from_env()

# Configuration Constants
PORT = 1234  # Port for incoming requests
DOCKER_CONTAINER_NAME = "gcr.io/hiring-278615/loggerator"  # Name of Docker image for the loggerator
LOG_FILE_PATH = "app.log"  

# Set up logging
logging.basicConfig(filename=LOG_FILE_PATH, level=logging.INFO)

def get_loggerator_logs():
    """ 
    This function attempts to start the loggerator Docker container. It then connects to the loggerator 
    using a TCP/IP socket, sends a GET request, and receives the logs in response. These logs are collected into a list 
    called 'log_entries.' After completing these tasks or if any error occurs, the function closes the 
    connection and stops the Docker container.

    The function uses the global variables DOCKER_CONTAINER_NAME and LOGGERATOR_FLAGS as the name of the Docker image 
    and the flags to start the loggerator with, respectively.

    Returns:
        list: log_entries - A list of strings, each string being a log. Returns an empty list if any error occurs.
    """

    # Start the Docker container
    try:
        # Run the loggerator Docker container in detached mode and expose its 8080 port
        container = client.containers.run(
            DOCKER_CONTAINER_NAME,
            ports={"8080/tcp": 8080},
            detach=True,
        )

        # Create a TCP/IP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Connect the socket to the server
        server_address = ("loggerator_container", 8080)
        sock.connect(server_address)
        log_data = ""

        try:
            # Send request
            message = "GET HTTP/1.1\r\nHost: localhost\r\n\r\n"
            sock.sendall(message.encode())

            # Receive data until no more is sent by the loggerator
            data = sock.recv(1024)
            while data:
                log_data += data.decode() # Decoding the byte response to string
                data = sock.recv(1024)

        except Exception as e:
            logging.error(f"An error occurred while retrieving logs from loggerator: {str(e)}")

        finally:
            sock.close()
            container.stop()

        # Split log_data by newline character to get individual log entries in the log_entries list
        log_entries = log_data.split("\n")
        return log_entries

    except Exception as e:
        logging.error(f"An error occurred while connecting to the Docker container: {str(e)}")
        # Return an empty list as no logs could be retrieved
        return []

@app.route("/logs", methods=["GET"])
def filter_loggerator_logs():
    """ 
    This function serves as a RESTful endpoint that handles GET requests at the '/logs' endpoint. The response consists 
    of HTTP access logs filtered based on three optional query parameters: 'code' (HTTP status code), 'method' (HTTP method),
    and 'user'. If a parameter is present in the request, the function filters the logs to only 
    include entries that match the corresponding field. 

    After retrieving HTTP Access logs from the loggerator via get_loggerator_logs(), this function parses each one with a regular expression
    that extracts the query parameters. 

    Logs are returned in descending order based on their timestamp. If an invalid value for any of the query 
    parameters is provided, a ValueError is raised. If an error occurs during the log processing, the function will 
    return an error message in JSON format with an HTTP status code of 400.

    Query Parameters:
        code (str, optional): HTTP status code used to filter the logs. This must be a numeric string.
        method (str, optional): HTTP method used to filter the logs. This must be a string of one or more alphabetic characters.
        user (str, optional): Username tused to filter the logs. This must be a string of one or more alphabetic characters.

    Returns:
        Response: A Flask JSON Response object that contains a list of filtered and sorted log entries (sorted_filtered_entries).
        If there is an error during processing, the response will contain a JSON-encoded error message with HTTP status code 400.
    """


    try:
        code = request.args.get("code")
        method = request.args.get("method")
        user = request.args.get("user")

        # Input validation for query parameters
        if code and not code.isdigit():
            raise ValueError("Invalid value for 'code' query parameter")
        if method and not re.match(r"^[a-zA-Z]+$", method):
            raise ValueError("Invalid value for 'method' query parameter")
        if user and not re.match(r"^[a-zA-Z_]+$", user):
            raise ValueError("Invalid value for 'user' query parameter")

        # Get log entries from loggerator
        log_entries = get_loggerator_logs()

        filtered_entries = []

        # Process each log entry
        for entry in log_entries:
            # Parse log entry using regex
            # Loggerator logs use the format defined here: https://www.w3.org/Daemon/User/Config/Logging.html
            match = re.search(r"(\S+) - (\S+) \[(.*?)\] \"(.*?)\" (\d+)", entry)
            if match:
                # Extract individual components of the log entry
                log_ip = match.group(1)
                log_user = match.group(2)
                log_timestamp = match.group(3)
                log_request = match.group(4)
                log_method = re.search(r"^\S+", log_request)
                log_status_code = match.group(5)

                # Filter logs based on query parameters
                if (
                    (not code or log_status_code == code)
                    and (not method or log_method.group(0) == method)
                    and (not user or log_user == user)
                ):
                    # Add timestamp to filtered entries for sorting
                    filtered_entries.append(
                        {
                            "entry": entry,
                            "timestamp": datetime.datetime.strptime(
                                log_timestamp, "%d/%b/%Y %H:%M:%S %z"
                            ),
                        }
                    )
        # Sort filtered logs in descending order by timestamp
        sorted_entries = sorted(
            filtered_entries, key=lambda x: x["timestamp"], reverse=True
        )
        sorted_filtered_entries = [entry["entry"] for entry in sorted_entries]

        # Return filtered logs as a JSON response
        return jsonify(sorted_filtered_entries)

    except Exception as e:
        logging.error(f"An error occurred while filtering logs: {str(e)}")
        # Return an error message and status code 400
        return jsonify({"error": str(e)}), 400


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=PORT)
