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
# run from cobalt directory, /dev/sda3 shuld have ~4GB
sudo mkfs.btrfs /dev/sda3
sudo mount /dev/sda3 ../mnt/
sudo btrfs quota enable mnt

cd ../mnt
sudo btrfs subvolume create root1
sudo btrfs subvolume create root2
sudo btrfs subvolume create root3

sudo btrfs qgroup limit -e 1g root1
sudo btrfs qgroup limit -e 1g root2
sudo btrfs qgroup limit -e 1g root3

sudo btrfs filesystem sync .
sudo btrfs qgroup show .
```