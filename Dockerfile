FROM ubuntu:14.04
MAINTAINER frikfry@gmail.com # Someone let me know an appropriate email for the project

# Needed to fix pip install of requirements due to strange char encoding issue.
ENV LC_CTYPE C.UTF-8
RUN apt-get clean
RUN apt-get update
RUN apt-get install -y vim postgresql postgresql-contrib postgresql-client libpq-dev libffi-dev nodejs node npm python-pip python-dev python3-dev build-essential
RUN pip install --upgrade pip
RUN pip install virtualenv

RUN mkdir -p /opt/spacedock/storage
WORKDIR /opt/spacedock

# Breaking up the installing of requirements like this so that it gets cached by docker
ADD requirements.txt /opt/spacedock/requirements.txt
RUN virtualenv --python=python3 --no-site-packages /opt/spacedock
RUN . /opt/spacedock/bin/activate && pip install -r requirements.txt

# Add everything else from the project root to the install dir.
ADD . /opt/spacedock
RUN npm install coffee-script

# Currently this means that changes to the configs are not realized on the Docker container without rebuilding it. Good way to fix?
RUN cp alembic.ini.example alembic.ini
RUN cp config.ini.example config.ini

# Setup a proper storage location instead of letting the code create /path/to/storage for real and use that.
# TODO: If the storage path doesn't exist, why not just use <project_root>/storage?
RUN sed -i -e 's|storage=.*|storage=/opt/spacedock/storage|g' config.ini

# Create our database.
# TODO: Rename from kerbalstuff to spacedock?
RUN /etc/init.d/postgresql start && \
    sudo -u postgres createdb kerbalstuff

# Make postgres trust all localhost connections implicitly.
RUN echo "local all all trust\n host all all 127.0.0.1/32 trust\n host all all ::1/128 trust" > /etc/postgresql/9.3/main/pg_hba.conf

# Create the alembic config and add a default admin user for development.
RUN /etc/init.d/postgresql start && \
. bin/activate && \
python -c 'from alembic.config import Config; from alembic import command; alembic_cfg = Config("alembic.ini"); command.stamp(alembic_cfg, "head"); exit()' && \
alembic upgrade head && \
python -c 'from KerbalStuff.objects import *; from KerbalStuff.database import db; u = User("admin", "admin@example.com", "development"); u.admin = True; u.confirmation = None; db.add(u); db.commit()'

# Start postgres and run the app when the container starts.
CMD service postgresql start && . /opt/spacedock/bin/activate && python /opt/spacedock/app.py
