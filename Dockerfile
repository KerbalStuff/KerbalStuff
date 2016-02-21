FROM ubuntu:14.04
MAINTAINER frikfry@gmail.com # Someone let me know an appropriate email for the project

# Needed to fix pip install of requirements due to strange char encoding issue.
ENV LC_CTYPE C.UTF-8
# Set this to suppress 'debconf: unable to initialize frontend' errors
ENV DEBIAN_FRONTEND noninteractive
RUN apt-get clean
RUN apt-get update
RUN apt-get install -y curl
# This needs to be broken up because curl isn't available at the start and we need curl to install nodejs
RUN curl -sL https://deb.nodesource.com/setup | sudo bash -
# Don't need to apt-get update first because the script above does it for us.
RUN apt-get install -y nodejs redis-server vim supervisor postgresql postgresql-contrib postgresql-client libpq-dev libffi-dev python-pip python-dev python3-dev build-essential
RUN pip install --upgrade pip
RUN pip install virtualenv

# Make our directories
RUN mkdir -p /opt/spacedock
WORKDIR /opt/spacedock

# Install coffee-script
RUN npm install --global coffee-script

# Create our database.
# TODO: Rename from kerbalstuff to spacedock?
RUN /etc/init.d/postgresql start && sudo -u postgres createdb kerbalstuff

# Breaking up the installing of requirements like this so that it gets cached by docker
COPY requirements.txt /opt/spacedock/requirements.txt
RUN virtualenv --python=python3 --no-site-packages /venv/spacedock
RUN . /venv/spacedock/bin/activate && pip install -r requirements.txt

# Add everything else from the project root to the install dir.
COPY . /opt/spacedock

# Setup the config files, if they don't already exist.
RUN test -f /opt/spacedock/config.ini || cp /opt/spacedock/config.ini.example /opt/spacedock/config.ini
RUN test -f /opt/spacedock/alembic.ini || cp /opt/spacedock/alembic.ini.example /opt/spacedock/alembic.ini

# Make postgres trust all localhost connections implicitly.
COPY docker/pb_hba.conf /etc/postgresql/9.3/main/pg_hba.conf

# Make a supervisord process for actually running the commands.
COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Create the alembic config.
RUN /etc/init.d/postgresql start && \
    /venv/spacedock/bin/python -c 'from alembic.config import Config; from alembic import command; alembic_cfg = Config("alembic.ini"); command.stamp(alembic_cfg, "head"); exit()' && \
    /venv/spacedock/bin/alembic upgrade head

# Add a default admin user for development.
RUN /etc/init.d/postgresql start && \
    /venv/spacedock/bin/python -c 'from KerbalStuff.objects import *; from KerbalStuff.database import db; u = User("admin", "admin@example.com", "development"); u.admin = True; u.confirmation = None; db.add(u); db.commit()'

# Add a default test user for development.
RUN /etc/init.d/postgresql start && \
    /venv/spacedock/bin/python -c 'from KerbalStuff.objects import *; from KerbalStuff.database import db; u = User("user", "user@example.com", "development"); u.confirmation = None; db.add(u); db.commit()'

# Start postgres and run the app when the container starts.
CMD ["/usr/bin/supervisord"]
