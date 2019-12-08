# UGParamaterEstimator
More or less generic parameter estimator for [UG4](https://gcsc.uni-frankfurt.de/simulation-and-modelling/ug4).

# Installation Note

As this package is under heavy development, I chose not to build a python binary package after each change.
I opted to have the package importable by folder. To use this, add the folder containing the "UGParameterErstimator"-folder
to your PYTHONPATH-enveriment variable. Under Linux, add ```export PYTHONPATH=$PYTHONPATH:$HOME/git``` (depending on the location of the folder) to your ~/.bashrc and execute ```source ~/.bashrc``` to update your PYTHONPATH.

# Usage Example

See the folder "example".