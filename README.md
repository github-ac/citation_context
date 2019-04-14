# citation context
collect article citations from xml files and extract the context in which a particular article was cited.

### environment setup
- `$ cd docker`
- `docker$ ./build.sh` builds an image, see `docker/Dockerfile`
- `docker$ ./restart.sh` runs a container
- `docker$ ./shell.sh` runs a shell within the container as root
- `~# service elasticsearch start`
- `~# source venv/bin/activate`
- `~# cd citation_context`
