FROM ubuntu:14.04
MAINTAINER frikfry@gmail.com # Someone let me know an appropriate email for the project

# Needed to fix pip install of requirements due to strange char encoding issue.
ENV LC_CTYPE C.UTF-8
RUN apt-get clean
RUN apt-get update
RUN apt-get install -y vim supervisor postgresql postgresql-contrib postgresql-client libpq-dev libffi-dev nodejs node npm python-pip python-dev python3-dev build-essential
RUN pip install --upgrade pip
RUN pip install virtualenv

# Make our directories
RUN mkdir -p /opt/spacedock
WORKDIR /opt/spacedock

# Install coffee-script
RUN npm install coffee-script

# Create our database.
# TODO: Rename from kerbalstuff to spacedock?
RUN /etc/init.d/postgresql start && \
    sudo -u postgres createdb kerbalstuff

# Breaking up the installing of requirements like this so that it gets cached by docker
ADD requirements.txt /opt/spacedock/requirements.txt
RUN virtualenv --python=python3 --no-site-packages /venv/spacedock
RUN . /venv/spacedock/bin/activate && pip install -r requirements.txt

# Add everything else from the project root to the install dir.
ADD . /opt/spacedock

# Make postgres trust all localhost connections implicitly.
ADD docker/pb_hba.conf /etc/postgresql/9.3/main/pg_hba.conf

# Make a supervisord process for actually running the commands.
ADD docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Create the alembic config and add a default admin user for development.
RUN /etc/init.d/postgresql start && \
    . /venv/spacedock/bin/activate && \
    python -c 'from alembic.config import Config; from alembic import command; alembic_cfg = Config("alembic.ini"); command.stamp(alembic_cfg, "head"); exit()' && \
    alembic upgrade head && \
    python -c 'from KerbalStuff.objects import *; from KerbalStuff.database import db; u = User("admin", "admin@example.com", "development"); u.admin = True; u.confirmation = None; db.add(u); db.commit()'

# Start postgres and run the app when the container starts.
CMD ["/usr/bin/supervisord"]
