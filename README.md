# DF-docker
This project is used to 

## Gettting started

### Installation

Clone repository with submodules
```
git clone --recursive https://github.com/TailGuy/DF-docker.git
```

cd into the project directory
```
cd DF-docker
```

### Setting up your environment variables

Create `.env` file from the template file `.envtemplate` and change all of the `changme` parts
```
cp ./.envtemplate ./.env
sudo nano .env
```

run the project
```
docker compose up --build -d
```


> to stop the project run
> ```
> docker compose down
> ```
