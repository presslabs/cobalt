# PROJECT UNDER DEVELOPMENT NOT FOR PRODUCTION USE!!!

### Testing

```bash
git clone git@github.com:Presslabs/cobalt
cd cobalt
mkvirtualenv -p python3 cobalt
pip install -r requirements/development.txt
PYTHONPATH=src py.test tests --cov=src
```
