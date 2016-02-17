# How to use the Dockerfile
It should be assumed that all commands should be run from the project root, unless otherwise noted.

## Quickstart
```
docker build -t spacedock:latest .
docker run -d -v $(pwd)/KerbalStuff:/opt/spacedock/KerbalStuff -p 5000:5000 -t --name spacedock spacedock
open http://$(docker-machine ip):5000
docker logs -f spacedock
```
Default Credentials: admin:development

## Install Docker
See [https://www.docker.com/](docker.com) for instructions on installing Docker for your platform.

## Configure, Build, and Run
The dockerfile will automatically copy the config.ini.example and alembic.ini.example to config.ini and alembic.ini, respectfully. If you wish to provide your own, copy them like below and edit as you will.
```
cp config.ini.example config.ini && cp alembic.ini.example alembic.ini
```

To build the Dockerfile and mark the image as spacedock and the latest version.
```
docker build -t spacedock:latest .
```

To run a new container based on the latest image of spacedock (which you just made above)
```
docker run -d -v $(pwd):/opt/spacedock -p 5000:5000 -t --name spacedock spacedock
```
This will automatically link ```your_project_root/KerbalStuff``` to be ```/opt/spacedock/KerbalStuff``` on the server.
This means that changes you make locally to files in your KerbalStuff folder will be instantly synced to and reflected in your local server.
This will also forward port 5000 of your docker contianer to port 5000 of your docker-machine, so you'll be able to browse to your local server.
Furthermore, this will also give the ```spacedock``` name to your container, which will make managing it easier.

This command might fail if you've already ran it in the past, probably because the old container is lying around. To fix that, type ```docker rm spacedock``` to delete the old container. Then you should be able to create a new container using the command above.

## Connecting
If you are on a mac or another environment that requires the use of docker-machine, then you must connect to the local server via that docker machine rather than localhost.

To find out the correct IP to use in your browser, use ```docker-machine ip```. You can then browser to port 5000 of that IP and all should be well.

The default username and password is admin:development.

## Starting and Stopping
If you want to stop your container without losing any data, you can simply do ```docker stop spacedock```.
Then, to start it back up, do ```docker start spacedock```.

## Odd and Ends
```
docker logs -f spacedock # View application logs
docker exec -i -t spacedock bash # Start a bash shell in the container
```
