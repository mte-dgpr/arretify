Vendor packages
====================


clients-api-droit
--------------------

Pypi rejects dependencies declared as direct references (i.e. dependencies that are not on pypi themselves).
This library is not on pypi and we therefore chose to include it as a git submodule.

Original repo is here : https://gitlab-forge.din.developpement-durable.gouv.fr/dgpr/data-studio-risques/py-clients-api-droit

This is Data Studio Risque's package for using legifrance and eurlex APIs.


mistralai
------------

This is an optional dependency of our lib. 
The dependency is defined in `pyproject.toml`.