import multiprocessing
import threading
import time
import random
import socket
import os
import json
import zipfile
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from queue import Queue
from flask import Flask, request, jsonify, render_template
from flask_sse import sse
from flask_cors import CORS

task_queue      = Queue()
worker_servers  = {}
ui_data_path = os.path.join("/mnt/f/Desktop/test/dockerScriptRunner", "data", "ui_data.json")
users_data_path = os.path.join("/mnt/f/Desktop/test/dockerScriptRunner", "data", "users.json")
users_hist_path = os.path.join("/mnt/f/Desktop/test/dockerScriptRunner", "data", "history")

def frun(ws_port, work_dir):
    worker_app = Flask(__name__)
    worker_app.config["REDIS_URL"] = "redis://localhost:6379"
    worker_app.config['WORK_DIR'] = work_dir
    worker_app.config['READY_STATE'] = False
    worker_app.register_blueprint(sse, url_prefix='/stream')

    CORS(worker_app, resources={
        r"/stream": {"origins": "*"},
        r"/execute_command": {"origins": "*"}  # Add another route here
    })
    
    command_queue = Queue()

    def background_thread():
        while True:
            try:
                # Get command from the queue
                command = command_queue.get_nowait()
            except Exception as e:
                time.sleep(1)
                continue
            
            try:
                # Execute the command using subprocess
                process = subprocess.Popen(command.get("command", "").split(), cwd=command.get("folder_path", ""), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

                # Stream output to SSE
                for line in iter(process.stdout.readline, ''):
                    with worker_app.test_request_context():
                        sse.publish({"output": line.strip()}, type='output_stream')

                # Wait for the process to complete
                process.wait()

                # Stream completion status to SSE
                with worker_app.test_request_context():
                    if command.get("ready_state") == False:
                        sse.publish({"output_status": "init_done"}, type='output_stop')
                    elif command.get("ready_state") == True:
                        sse.publish({"output_status": "completed"}, type='output_stop')
            except Exception as e:
                print(f'An error occurred: {e}')


    @worker_app.route('/execute_command')
    def execute_command():
        try:
            if worker_app.config['READY_STATE'] == False:
                command_queue.put(
                    {
                        #"command": "docker-compose up",
                        "command": "ls -la",
                        "folder_path": worker_app.config['WORK_DIR'],
                        "ready_state": worker_app.config['READY_STATE']
                    }
                    )
                worker_app.config['READY_STATE'] = True
            elif worker_app.config['READY_STATE'] == True:
                command_queue.put(
                    {
                        #"command": "docker-compose up",
                        "command": "ls -la",
                        "folder_path": worker_app.config['WORK_DIR'],
                        "ready_state": worker_app.config['READY_STATE']
                    })
        except Exception as e:
            print(f'An error occurred: {e}')
        return jsonify({'success':True, 'new_state': worker_app.config['READY_STATE']}), 200, {'ContentType':'application/json'}


    @worker_app.route('/')
    def hello_world():
        return 'Hello, World!'

    # Run the Flask app without the if __name__ == '__main__': block
    bg_thread = threading.Thread(target=background_thread)
    bg_thread.start()
    worker_app.run(host='0.0.0.0', port=ws_port)
    time.sleep(5)

def is_port_free(port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", port))
        return "OPEN"
    except socket.error:
        return "IN USE / CLOSED"

def scheduled_task():
    global worker_servers
    while True:
        try:
            task_params = task_queue.get_nowait()
        except Exception as e:
            time.sleep(1)
            continue

        try:
            if task_params.get("task_type") == "start_server":

                print('BG Task - start_server')

                with open(users_data_path) as f:
                    users_data = json.loads(f.read())

                username = task_params.get("username")

                users_data[username]["history_seq"].append(task_params.get("server_time"))
                users_data[username]["history"][task_params.get("server_time")] = {
                    "ws_port":      task_params.get("ws_port"),
                    "cpu_count":    task_params.get("cpu_count"),
                    "ram_val":      task_params.get("ram_val"),
                    "os_selected":  task_params.get("os_selected"),
                    "run_type":     task_params.get("run_type"),
                    "server_time":  task_params.get("server_time"),
                    "file_name":    task_params.get("file_name"),
                    "event_source": f'http://localhost:{task_params.get("ws_port")}'
                }

                with open(users_data_path, "w+") as f:
                    f.write(json.dumps(users_data, indent=2))

                history_seq = users_data[username]["history_seq"]
                history     = users_data[username]["history"]

                flask_proc = multiprocessing.Process(target=frun, args=(task_params.get("ws_port"), task_params.get("work_dir"), ))
                flask_proc.daemon = True
                flask_proc.start()
                worker_servers[str(task_params.get("ws_port"))]=flask_proc

        except Exception as e:
            print(f'An error occurred: {e}')

def server_func():
    current_path = Path(__file__)
    server_app = Flask(__name__, template_folder=os.path.join(current_path.parent.absolute(), "code_vessel", "templates"))

    log_timestamp   = datetime.now().strftime("%Y_%m_%d_%H_%M_%S_%f")

    def sys_ops():
        logical_proc_count = os.cpu_count()
        mem_bytes          = os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES')
        mem_gib            = int(mem_bytes/(1024.**3))
        return {
                   "proc_count": logical_proc_count,
                   "mem_in_gbs": mem_gib
               }

    @server_app.route('/')
    def home():
        with open(users_data_path) as f:
            users_data = json.loads(f.read())

        username = request.args.get("username")
        if username in users_data:
            history_seq = users_data[username]["history_seq"]
            history     = users_data[username]["history"]

            with open(ui_data_path) as f:
                inp_ops = json.loads(f.read())

            return render_template("new_ui.j2", sys_ops=sys_ops(), inp_ops=inp_ops, history_seq = history_seq, history = history, username = username)
        else:
            return jsonify({ "msg": "user not found" }), 200

    @server_app.route('/start_server', methods=['POST'])
    def start_server():
        print('Route accessed - /start_server')
        json_out = {
            "success": False
        }
        try:
            username     = request.form.get("username")
            inp_info     = json.loads(request.form.get("inp_info"))
            zip_file     = request.files.get("zip_file")

            cpu_count    = inp_info.get("cpu_count")
            ram_val      = inp_info.get("ram_val")
            os_selected  = inp_info.get("os_selected")
            file_name    = zip_file.filename
            run_type     = inp_info.get("run_type")
            timestamp    = datetime.now().strftime("%Y_%m_%d_%H_%M_%S_%f")
        
            path_to_zip  = os.path.join(users_hist_path, username, "zips", timestamp)
            path_to_file = os.path.join(users_hist_path, username, "files", timestamp)
            dir_to_extract_to = os.path.join(path_to_file, zip_file.filename.split(".zip")[0].strip())

            dockerf_template  = render_template("Dockerfile.j2", inp_info=inp_info, work_dir=timestamp)
            dockerc_template  = render_template("docker-compose.j2", all_names=timestamp, file_dir=path_to_file)
            usr_request_json  = json.loads(inp_info.get("commands"))
            run_script_templ  = render_template("runScript.j2", usr_request_json=usr_request_json)
        
            os.makedirs(path_to_zip)
            os.makedirs(path_to_file)

            with open(os.path.join(path_to_zip, zip_file.filename), "wb+") as f:
                f.write(zip_file.read())

            with zipfile.ZipFile(os.path.join(path_to_zip, zip_file.filename), 'r') as zip_ref:
                zip_ref.extractall(path_to_file)

            for item in os.listdir(dir_to_extract_to):
                item_path = os.path.join(dir_to_extract_to, item)
                shutil.move(item_path, path_to_file)

            os.rmdir(dir_to_extract_to)

            with open(os.path.join(path_to_file, "Dockerfile"), "w+") as f:
                f.write(dockerf_template)

            with open(os.path.join(path_to_file, "docker-compose.yml"), "w+") as f:
                f.write(dockerc_template)

            with open(os.path.join(path_to_file, "runScript.sh"), "w+") as f:
                f.write(run_script_templ)

            ws_port = random.choice([port for port in range(49152, 65536, 1) if is_port_free(port) == "OPEN" and str(port) not in worker_servers ])
            task_queue.put(
                {
                    "task_type":   "start_server",
                    "cpu_count":   cpu_count,
                    "ram_val":     ram_val,
                    "os_selected": os_selected, 
                    "ws_port":     ws_port,
                    "run_type":    run_type,
                    "server_time": timestamp,
                    "work_dir":    path_to_file,
                    "username":    username,
                    "file_name":   zip_file.filename
                })

            json_out = {
                    "event_source": f"http://localhost:{ws_port}",
                    "server_time":  timestamp,
                    "run_type":     run_type,
                    "file_name":    zip_file.filename,
                    "os_selected":  os_selected,
                    "ram_val":      ram_val,
                    "cpu_count":    cpu_count,
                    "success":      True
                }
            print(json_out)
        except Exception as e:
            print(f'An error occurred: {e}')
        return json_out

    @server_app.route('/stop_server')
    def stop_server():
        ws_port = request.args.get("ws_port")
        for the_port in worker_servers:
            if str(ws_port) == the_port:
                while worker_servers[the_port].is_alive():
                    worker_servers[the_port].terminate()
                    time.sleep(0.1)
                    if not worker_servers[the_port].is_alive():
                        worker_servers[the_port].join(timeout=1.0)
                        break
        return jsonify(
            {
                "status": f"Server Down {ws_port}"
            })

    server_app.run(host='0.0.0.0', port=5000)

if __name__ == "__main__":
    background_thread = threading.Thread(target=scheduled_task)
    background_thread.start()
    server_func()
    background_thread.join()
