# dockerScriptRunner
Automatic allocation of resources on a central group of resources for containerized execution of user tasks.

## Features

1. Isolated environment for each user task execution
2. User customized environments
3. Secure processing environment

## Installing

The utility depends on the following softwares:

1. [Docker](https://docs.docker.com/engine/install/)
2. [Python](https://www.python.org/downloads/)
3. [Redis](https://redis.io/docs/install/install-redis/).

You can clone the repository and run the following :

```shell
pip install .
```

or install it from the python index via :

```shell
pip install sample_name
```

## Running

The program can be executed as a normal python utility.

```shell
sample_name --host "127.0.0.1" --port 8080 --workers 4
```
## Using

1. Open the URL displayed on the CLI on your preferred browser.
2. Sign Up/Login to the webpage.
3. Create a new session
4. Open the session, define your environment requirements
5. Specify the commands to execute in the environment.
6. Run

Sample Input Area Format:
'''{
  "jobs": [
    "python3 -m pip install wheel", 
    "python3 -m pip install -r requirements.txt",
    "python3 hello_world.py"
  ]
}'''
