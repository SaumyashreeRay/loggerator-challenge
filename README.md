# README: loggerator_challenge

## Introduction

The `loggerator_challenge` interacts with the `loggerator` (running as a separate container), retrieves logs and exposes a REST endpoint (`/logs`) on port 1234 to return logs based on specific filters. The filters include `code` (HTTP status code), `method` (HTTP method), and `user`. The logs are returned in descending time order.

## Prerequisites

- Docker installed on your machine.
- Access to Docker image for the `loggerator`: `gcr.io/hiring-278615/loggerator`.

## How to Run Loggerator_Challenge

Follow these steps to run the Loggerator_Challenge Python program.

1. Build the Docker image for the application `loggerator_challenge`.
    ```bash
    docker build -t loggerator_challenge .
    ```

2. Create a Docker network for inter-container communication.
    ```bash
    docker network create loggerator_network
    ```

3. Run the `loggerator` container in detached mode.
    ```bash
    docker run -d --network=loggerator_network --name loggerator_container gcr.io/hiring-278615/loggerator
    ```

4. Run the container `loggerator_challenge` in detached mode. The container has access to the Docker daemon through the Docker socket, which allows it to start other Docker containers.
    ```bash
    docker run -v /var/run/docker.sock:/var/run/docker.sock -d --network=loggerator_network -p 1234:1234 --name loggerator_challenge_container loggerator_challenge
    ```

Now, `loggerator_challenge` is running and can interact with the `loggerator`. 

To use the application, send a GET request to the endpoint at `http://localhost:1234/logs` using curl. You can use any combination of the `code`, `method` and `user` query parameters to filter the HTTP access logs from the `loggerator`.

## Example Commands

`curl "http://localhost:1234/logs?method=GET"`

`curl "http://localhost:1234/logs?method=POST&user=aut"`

`curl "http://localhost:1234/logs?method=PUT&user=minus_aut&code=200"`

## Clean Up

After you are done, you can clean up the Docker environment using these commands.

1. Disconnect the `loggerator` container from the Docker network.
    ```bash
    docker network disconnect loggerator_network loggerator_container
    ```

2. Disconnect the `loggerator_challenge` container from the Docker network.
    ```bash
    docker network disconnect loggerator_network loggerator_challenge_container
    ```

3. Delete the Docker network.
    ```bash
    docker network rm loggerator_network
    ```

4. Stop and remove the Loggerator container.
    ```bash
    docker stop loggerator_container
    docker rm loggerator_container
    ```

5. Stop and remove the `loggerator_challenge` container.
    ```bash
    docker stop loggerator_challenge_container
    docker rm loggerator_challenge_container
    ```
