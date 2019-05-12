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

### print contexts for all variants of a given title
```
citation_context# python title_citation_contexts.py --help
```
Given a title, all related title/pub_id pairs are collected and their citation context is returned.

## example
```
$ title="gapped blast and psi-blast: a new generation of protein database search programs"
$ python title_citation_contexts.py --title "${title}"
```
Sequence homologues for the SCAP and SREBF 2 proteins were obtained by PSI BLAST`<XREF>`.

The resulting putative ORFs were used as BLASTp queries`<XREF>`against the NCBI non redundant database .

Sequences were compared with the GenBank NR and NCBI ENV databases using tblastx`<XREF>`.

Contig sequences for the investigated genes were identified in the transcriptome dataset by bidirectional BLAST`<XREF>`.

The template was chosen using BLASTp`<XREF>`to search against the protein data bank.

Additional high similarity sequences and were obtained from NCBI database and were added as control sequences using nucleotide Basic Local Alignment Search Tool`<XREF>`.

After which, the resulting consensus 16S rDNA sequences obtained were Blast in the NCBI database with the Basic Alignment Search Tool for homology in order to identify the probable organism in question`<XREF>`.

The partial 16S rDNA sequences obtained for the macergens were utilized in the search of reference nucleotide sequence available in NCBI GenBank database using BlastN algorithm`<XREF>`.

At 15 min intervals, 9.5 L samples was added to 0.5 L Hoechst 33372 and imaged by phase and fluorescent microscopy as described elsewhere`<XREF>`.

In pathogenic bacteria such as Streptococcus pneumoniae, an extracellular nuclease of this family degrades DNA meshes of neutrophil extracellular traps to escape host immune responses`<XREF>`, whilst conversely, in Vibrio cholerae, extracellular nucleases of this family are involved in biofilm formation , suggesting a diversity of functions for these.

Annotations were added to the EST sequences by comparing them to the Genbank non redundant and Human RefSeq nucleotide and amino acid databases using BLASTN and BLASTX ,`<XREF>`.

