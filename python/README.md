# Python scripts

This directory contains the Python scripts and packages used to generate the emergency vocabulary and corpus from the dataset
output by the Java component. It also contains code that extends an already existing emergency vocabulary.

For the former, a pipeline-based, parameterizable transformation library is invoked. For the latter, several methods have been proposed:

1. Embedding-based similarity
1. Dictionary-based similarity
1. The (semi-supervised) method introduced in the paper.

## A "functional" pipeline library

A "functional", parallel stream-based framework that runs on a single, multi-core machine. The concepts (classes) are:

- `Resource`: a computing resource, that might need initialization and cleanup.
  - `Source`: a data source. Currently only JSON files are supported.
  - `Transform`: a step in the parallel part of the pipeline. Reads records and does something with them:
    - `Map`: transforms a record. It may return a `None`, in which case the record is skipped
             (the `None` won't be forwarded to the next `Transform`)
    - `Filter`: returns a boolean that tells the pipeline whether to keep the current record or not
  - `Collector`: aggregates a stream of records. Returns a list of values.
  
The script [run_pipeline.py](https://github.com/DavidNemeskey/cc_emergency_corpus/blob/master/python/scripts/run_pipeline.py) builds
a pipeline based on a JSON configuration file; there are several examples in the
[conf](https://github.com/DavidNemeskey/cc_emergency_corpus/tree/master/python/cc_emergency/conf) directory. Some of the configuration
files can be run as-is, while others are parameterized, which parameters the user must provide on the command line via the `-R`
switch (e.g. `-Rset_file=my_set_file.lst`). The configuration files define the `pipeline` key, whose value is a list of `Resource`s:
a `Source`, then any number of `Transform`s, ending with a `Collector`. If the goal is not to just transform the data, but to aggregate
the output over all files, a final `Collector` can be defined under the `reducer` key.

It is obvious that this framework is very similar to map-reduce, and if proper single-machine (or non-Hadoop cluster) implementations
of the latter existed, there would be no need for this framework. Later, I might just implement a map-reduce framework for local clusters
and plug it in instead.

## How to reproduce the runs in the paper

For the scripts below, we assume the following directory structure:

- `.`: the working directory
  - `cc_emergency_corpus`: the cloned repository
  - `news_json`: the output of the Java component
  - `news_...`: other data directories created by the scripts
  - `results`: search results are put here
  - `stats`: (sub)corpus statistics are put here
  - `weights`: weighted word lists
  - `queries`: query files

Provided we are in the working directory, the first step is to clone the
repository:
```bash
git clone git@github.com:DavidNemeskey/cc_emergency_corpus.git
```
Then, we create a virtualenv for the project. The scripts should work under Python 2, but it's 2017, so we shall
go with Python 3:
```bash
virtualenv -p python3 ~/venvs/cc_emergency_env
```
We shall do all our work in this environment. The environment has entered before doing any work and exited
when we are done:
```bash
source ~/venvs/cc_emergency_env/bin/activate
# Do some work
deactivate
```
The last step is to install the python package that resides in the repository. This has to be done from
the virtual environment, so that it installs there, and not in the central path:
```bash
source ~/venvs/cc_emergency_env/bin/activate
cd cc_emergency_corpus/python
pip install -e .
cd ../..
```

Finally, we are ready to do some work. Way to go! Note that all scripts accept the `-h` option, which
prints the options available to it. This can come in handy, if the following examples seem confusing.

Note that in our case, the working directory is `/mnt/permanent/Language/English/Crawl/Common_Crawl`. Most of the steps below
have already been done, so if you are going to be working there, just skip ahead to the _Search_ section.

### Language detection

The Common Crawl news dataset is not filtered to any language, and unfortunately the data does not contain a language tag. So language
detection is needed, since we only concern ourselves with English for now. Provided the repository is clone to the data directory,
the following command does just that:
```
python cc_emergency_corpus/python/scripts/run_pipeline.py -i news_json -o news_filtered -P 4 -L debug -c filter_language.json
```
We use [langid](https://pypi.python.org/pypi/langid) for language detection, which is quite slow -- be prepared to wait a lot.

### Parsing

The second step is parsing the data. For this, we employ [Stanford CoreNLP](https://stanfordnlp.github.io/CoreNLP/). At this stage,
only lemmatization and POS induction is performed -- running NER on all the documents would take 3 days at this point, and it is
not even necessary: we are only interested in emergency-related entities.
```
python cc_emergency_corpus/python/scripts/run_pipeline.py -i news_filtered/ -o news_parsed/ -P 4 -L debug -c corenlp.json
```

### Duplicate detection

As usual, the data is affected by both URL- and content-duplication, so the next step is deduplication. We use the
[datasketch](https://github.com/ekzhu/datasketch) library for this purpose, with the following settings:

- minhash encoding of word 4-grams with 128 permutations;
- locality sensitive hashing with a Jaccard threshold of 85%.

```
python cc_emergency_corpus/python/scripts/run_pipeline.py -i news_parsed/ -r unique.tsv -P8 -L debug -c duplicates.json
python cc_emergency_corpus/python/scripts/run_pipeline.py -i news_parsed/ -o news_unique/ -P8 -L debug -c unique.json
```
Of course, it would have been possible to do (character n-gram-based) deduplication first and parsing next. However, the first few
annotators in CoreNLP (lemmatization and POS) are really fast, so it is neither here nor there, at least speed-wise.

### Word count

If we are to search in documents, we will need the term frequencies, as well as the aggregated statistics (corpus-level TF and DF).
The former are computed first, and the latter is another pipeline run, that uses the output of the first step. This is also the place
to filter the fields in the data, because the search will only be needing the `url` as the unique id and the `counts`. To make
evaluation by hand easier, the unparsed text `content` is kept as well. In the first pipeline, we also replace proper nouns
(OK, so this is where proper NER would have been useful) with the `NNP` token, because we are looking for common words that are
emergency-related, not the accidental entities involved.

```
python cc_emergency_corpus/python/scripts/run_pipeline.py -i news_unique/ -o news_counts/ -P8 -L debug -c count_tf.json
python cc_emergency_corpus/python/scripts/run_pipeline.py -i news_counts/ -r stats/news_tfdf.json -P8 -L debug -c reduce_tf_df.json
```

### Word filtering

In order to make searches faster, all words whose DF is under 10 were removed from the documents. This decreased the vocabulary to
about 123k without (or so we think) the loss of any important words. Any documents that end up empty are also dropped.
```
python cc_emergency_corpus/python/scripts/run_pipeline.py -i news_counts/ -o news_lemma_tf/ -P 8 -L debug -c filter_counts.json
python cc_emergency_corpus/python/scripts/run_pipeline.py -i news_lemma_tf/ -r stats/news_tfdf_update.json -P8 -L debug -c reduce_tf_df.json
```
`filter_counts.json` needs the list of words to keep, which can be easily collected from the result of the previous run,
`news_tfdf.json`.

### Searching

#### Basic search

Finally, we can search in the filtered, reduced data:
```
python cc_emergency_corpus/python/scripts/run_pipeline.py -i news_lemma_tf/ -r results/search_result.json -P8 -L debug -c search_file.json -Ravgdl=498.4 -Rquery_file=queries/query_file.lst
```
Here, `avgdl` is a parameter to the Okapi-BM25 scorer, and it should be computed manually (hint: `sum(tf) / num_docs`); `query_file`
is the query file. It can take two forms: a `.tsv` file with two fields: the query term and its weight, or a simple list file, with
one word per line. In the latter case, the weights of all words are taken to be 1.

#### Computing IDF

There are two ways to determine the word weights, both implemented by the `weight_words.py` script:
```bash
# IDF weighting where no_docs == 976338:
python cc_emergency_corpus/python/scripts/weight_words.py stats/news_tfdf_update.json df -n 976338 > weights/idfs.tsv
# log(TF(E)/TF(C)) ratio, as in the paper; threshold at 2, with word filtering:
python cc_emergency_corpus/python/scripts/weight_words.py emergency_corpus_stats.json -t 2 -w umbc.min50.words tf --print-dfs news_tfdf_update.json > tf_ratios.tsv
```

#### Query weighting

In order to create a weighted query from the word weights, one uses the `weight_query.py` script.
This script takes as its parameter a query word list and a weighting computed in the previous step.
```
python cc_emergency_corpus/python/scripts/weight_query.py queries/bev.lst weights/idfs.tsv -s > queries/bev_0.tsv
```

#### Subsets

Typically, we would like to create subset corpora (e.g. emergency-related) from the search results. Since filtering `Transform`s
usually read their input from a simple list file (one item per line), the first step is to convert the search results to such files:
```
head -300 search_0.json | python cc_emergency_corpus/python/scripts/json_to_set.py - -f url > search_0_300.urls
```
Then, in order to compute the log TF ratio, we need the TF/DF statistics of the new subcorpus. This is computed as
```
python cc_emergency_corpus/python/scripts/run_pipeline.py -i news_lemma_tf -r stats/search_0_tfdf.json -P8 -L debug -c reduce_subset.json -Rurl_filter=results/search_0.urls
```

#### Everything put together

In what follows, we shall start with a query file, search, acquire the statistics of the resulting subcorpus,
reweight the words and search again with the reweighted query. This process can be continued for arbitrarily
long, adding or removing words from the query manually between searches.

```bash
## First iteration

# The first search
python cc_emergency_corpus/python/scripts/run_pipeline.py -i news_lemma_tf/ -r results/search_evf_0.json -P8 -L debug -c search_file.json -Ravgdl=498.4 -Rquery_file=queries/evf.lst

# Extract the urls from the result
cat results/search_evf_0.json | python cc_emergency_corpus/python/scripts/json_to_set.py - -f url > results/search_evf_0.urls 
# Or, take just the first 10,000 documents
head -10000 results/search_evf_0.json | python cc_emergency_corpus/python/scripts/json_to_set.py - -f url > results/search_evf_0_10000.urls 

# Compute the TF/DF statistics
python cc_emergency_corpus/python/scripts/run_pipeline.py -i news_lemma_tf -r stats/search_evf_0_tfdf.json -P8 -L debug -c reduce_subset.json -Rurl_filter=results/search_evf_0.urls

# Acquire the list of words that are candidates for being the most emergency-related,
# filtered by and UMBC word list
python cc_emergency_corpus/python/scripts/weight_words.py stats/search_evf_0_tfdf.json -t 2 -w umbc.min50.words tf --print-dfs stats/news_tfdf_update.json > weights/news_evf_0.tsv

# Have a look at the list, add words from it to the query, etc. You can just copy the
# lines from weights/news_evf_0.tsv, or add the words to the new query file evf_1.lst,
# and then
python cc_emergency_corpus/python/scripts/weight_query.py queries/evf_1.lst weights/news_evf_0.tsv -t 2 > queries/evf_1.tsv

## Second iteration

# The second search
python cc_emergency_corpus/python/scripts/run_pipeline.py -i news_lemma_tf/ -r results/search_evf_1.json -P8 -L debug -c search_file.json -Ravgdl=498.4 -Rquery_file=queries/evf_1.tsv

# ... you get the idea
```
