# dockerScriptRunner
dockerScriptRunner just spins up docker, runs script and shuts down

Sample Input Area Format:
{
  "jobs": [
    "python3 -m pip install wheel", 
    "python3 -m pip install -r requirements.txt",
    "python3 hello_world.py"
  ]
}
