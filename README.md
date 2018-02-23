# cc_emergency_corpus

Code used for conducting the experiments in the papers

- Judit Ács, Dávid Márk Nemeskey, András Kornai: Identification of Disaster-implicated Named Entities. Proceedings of the First International Workshop on Exploitation of Social Media for Emergency Relief and Preparedness, 2017.
- Dávid Márk Nemeskey, András Kornai: Emergency Vocabulary. Information Systems Frontiers, 2018 (to be published)

The code in the repository implements the preprocessing steps described in the papers, and contains all the components required to replicate the experiments therein. A few words of warning:

- the code is not production quality ... at all
- because we had to conduct a lot of experiments in a very short time, the documentation is not up to date, and there might be inconsistencies between the various scripts in the data format they expect or emit
- the kind of parallellism implemented in `run_pipeline.py` worked well for the smaller, pilot dataset; however, it is ill suited to the full CC News dataset. It should have been replaced with something more robust and scalable.

Still I put it up here hoping that parts of it might be useful for somebody. If so, please cite the papers above.
