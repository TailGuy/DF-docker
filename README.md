# DF-docker

## Installation

Clone repository with submodules
```
git clone --recursive git@github.com:TailGuy/DF-docker.git
```

cd into the project directory
```
cd DF-docker
```

Create `.env` file from the template file `.envtemplate` and change all of the `changme` parts
```
cp ./.envtemplate ./.env
sudo nano .env
```

run the project
```
docker compose up --build -d
```

> [INFO]
> to stop the project run
> ```
> docker compose down
> ```
