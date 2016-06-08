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

```bash
# run from cobalt directory
# create a 1G file
dd if=/dev/zero of=../mnt/root1/cobalt-root bs=1024 count=1000000
mkfs.btrfs ../mnt/root1/cobalt-root
```