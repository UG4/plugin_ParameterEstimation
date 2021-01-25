# UGParamaterEstimator

[![Documentation Status](https://readthedocs.org/projects/ugparameterestimator/badge/?version=latest)](https://ugparameterestimator.readthedocs.io/en/latest/?badge=latest)
![Python package](https://github.com/UG4/plugin_ParameterEstimation/workflows/Python%20package/badge.svg)

Docs: [here](https://ugparameterestimator.readthedocs.io/en/latest/).

More or less generic parameter estimator for [UG4](https://gcsc.uni-frankfurt.de/simulation-and-modelling/ug4).

# Installing

To use this package, you need python3 installed. You can then use

```python -m pip install -r requirements.txt```

# Importing

As this package is under heavy development, I chose not to build a python binary package after each change.
I opted to have the package importable by folder. 

If this package is used with UG installed (probably):

When using this package, just make sure the eniviroment variable "UG4-ROOT" is defined. Then, just append the lines

```import sys, os
sys.path.append(os.path.join(os.environ["UG4_ROOT"],"plugins","ParameterEstimation"))
```

to the top of your script.


If this package is used standalone:

To use this, add the folder containing the "UGParameterErstimator"-folder
to your PYTHONPATH-enveriment variable. Under Linux, add ```export PYTHONPATH=$PYTHONPATH:$HOME/git``` (depending on the location of the folder) to your ~/.bashrc and execute ```source ~/.bashrc``` to update your PYTHONPATH.

In both cases the package can be imported with
```from UGParameterEstimator import *```

# Usage Example

See the folder "example".
