# PROJECT UNDER DEVELOPMENT NOT FOR PRODUCTION USE!!!

### Testing

```bash
git clone git@github.com:Presslabs/cobalt
cd cobalt
mkvirtualenv -p python3 cobalt
pip install -r requirements/development.txt
PYTHONPATH=src py.test tests --cov=src
```

### Sample

To run the sample cluster you need ~4GB of space

From the project root folder
```bash
docker built -t presslabs/cobalt:latest .
sample/setup.sh
docker-compose up
```

