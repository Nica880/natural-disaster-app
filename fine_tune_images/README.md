# fine_tune_images/

Runtime folder for **operator corrections**. When an operator marks an incident
as a false alarm and picks the real class in the Monitor UI, the backend exports
the original frame to `fine_tune_images/<class>/`. `model/train_v3.py` merges
these hard cases into the next training run automatically.

The folder's contents are gitignored: images are data, not source code.
