# PROJECT UNDER DEVELOPMENT NOT FOR PRODUCTION USE!!!

# Cobalt

[![Code Climate](https://codeclimate.com/repos/575fcf4f35379340730025a4/badges/1c72b01b55f804a4de4e/gpa.svg)](https://codeclimate.com/repos/575fcf4f35379340730025a4/feed)
[![Test Coverage](https://codeclimate.com/repos/575fcf4f35379340730025a4/badges/1c72b01b55f804a4de4e/coverage.svg)](https://codeclimate.com/repos/575fcf4f35379340730025a4/coverage)
[![Issue Count](https://codeclimate.com/repos/575fcf4f35379340730025a4/badges/1c72b01b55f804a4de4e/issue_count.svg)](https://codeclimate.com/repos/575fcf4f35379340730025a4/feed)

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

### Reload drone.sec

Each time someone modifies .drone.yml this needs to be ran
```bash
drone secure --repo PressLabs/cobalt
```
