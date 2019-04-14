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

### index citations
```
citation_context# python refs_to_es.py --help
```
For each citation in each citing article, index:
- citing article file
- cited article ref_id within the citing article
- cited article title
- cited article pub_id, if present

Articles are parsed in multiple processes, and data is indexed in bulk.


### list most cited titles
```
citation_context# python most_common_titles.py --help
```
