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

It is obvious that this framework is very similar to map-reduce, and it proper single-machine (or non-Hadoop cluster) implementations
of the latter existed, there would be no need for this framework. Later, I might just implement a map-reduce framework for local clusters
and plug it in instead.

## How to reproduce the runs in the paper

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
python cc_emergency_corpus/python/scripts/run_pipeline.py -i news_counts/ -r news_tfdf.json -P8 -L debug -c reduce_tf_df.json
```

### Word filtering

In order to make searches faster, all words whose DF is under 10 were removed from the documents. This decreased the vocabulary to
about 123k without (or so we think) the loss of any important words. Any documents that end up empty are also dropped.
```
python cc_emergency_corpus/python/scripts/run_pipeline.py -i news_counts/ -o news_lemma_tf/ -P 8 -L debug -c filter_counts.json
python cc_emergency_corpus/python/scripts/run_pipeline.py -i news_lemma_tf/ -r news_tfdf_update.json -P8 -L debug -c reduce_tf_df.json
```
`filter_counts.json` needs the list of words to keep, which can be easily collected from the result of the previous run,
`news_tfdf.json`.

### Searching

#### Basic search

Finally, we can search in the filtered, reduced data:
```
python cc_emergency_corpus/python/scripts/run_pipeline.py -i news_lemma_tf/ -r search_result.json -P8 -L debug -c search.json -Ravgdl=496.162
```
Here, `avgdl` is a parameter to the Okapi-BM25 scorer, and it should be computed manually (hint: `sum(tf) / num_docs`).

#### Computing IDF

The scorer also needs the IDF file, which can be created with the following commands:
```
python cc_emergency_corpus/python/scripts/weight_words.py news_tfdf_update.json -n 976338 > idfs.tsv
```

#### Query weighting

`search.json`, looks for the word _emergency_ with a weight of 1. However, one can also use a weighted query file. The obvious
example is to use the BEV as query, weighted by IDF. Provided the BEV is available as a list,
```
python cc_emergency_corpus/python/scripts/weight_query.py bev.lst idfs.tsv -s > bev_0.tsv
```

#### Subsets

Typically, we would like to create subset corpora (e.g. emergency-related) from the search results. Since filtering `Transform`s
usually read their input from a simple list file (one item per line), the first step is to convert the search results to such files:
```
head -300 search_0.json | python cc_emergency_corpus/python/scripts/json_to_set.py - -f url > search_0_300.urls
```

Then, one could just use the `FilterDocument` `Transform` with that list, and write the new subcorpus into a directory, or just
put `FilterDocument` as the first step in all pipelines dealing with the subset.
