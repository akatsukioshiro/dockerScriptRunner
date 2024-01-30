from flask import Flask, render_template, request
import socket, json, os, time
from datetime import datetime
from flask_cors import CORS
import threading
import logging
import psutil
from pathlib import Path
from code_vessel.utils import get_app_location

current_path = Path(__file__)
app = Flask(__name__, template_folder=os.path.join(current_path.parent.parent.absolute(), "templates"))

CORS(app, resources={r"/port_heartbeat": {"origins": "*"}})

logger = logging.getLogger("main_server")
logger.setLevel(logging.DEBUG)

formatter    = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s] %(message)s")
app_data_dir = get_app_location()
log_loc      = os.path.join(app_data_dir, 'logs')
log_file     = os.path.join(log_loc, 'main_server.log')

if not os.path.exists(log_loc) and not os.path.isfile(log_loc):
    os.makedirs(log_loc)
    if os.path.isfile(log_file):
        open(log_file, "w").close()

file_handler = logging.FileHandler(log_file, mode="a", encoding=None, delay=False)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.info(f"Logging to {log_file}")

port_in_use = {}

def scheduled_task():
    global port_in_use
    # Your task logic here
    to_unassign = []
    for ports in port_in_use:
        if int((datetime.strptime(port_in_use[ports]["last_beat"], "%Y_%m_%d_%H_%M_%S")-datetime.now()).total_seconds() / 60)*-1 >= 5:
            to_unassign.append(ports)
        elif int(float(port_in_use[ports]["inactivity_timer"])) >= 5:
            to_unassign.append(ports)
    for ports in to_unassign:
        port_in_use.pop(ports)
        for process in psutil.process_iter(['pid', 'name', 'cmdline']):
            if "python" == process.info['name']:
                if len(process.info['cmdline']) == 6:
                    if process.info['cmdline'][1] == "run_flask_server.py":
                        if process.info['cmdline'][3] == ports:
                            print(process.info['pid'], process.info['name'], process.info['cmdline'])
                            os.kill(process.info['pid'], 9)
        print(f"Port: {ports} is now free!")
        logging.info(f"Port: {ports} is now free!")
    to_unassign = []
    print("Executing scheduled task")
    logging.info("Executing scheduled task")


def run_scheduled_tasks():
    while True:
        scheduled_task()
        time.sleep(30)

@app.route('/')
def index():
    return render_template('session_creator.j2')

def is_port_free(port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", port))
        return "OPEN"
    except socket.error:
        return "IN USE / CLOSED"

@app.route('/port_allocate')
def port_alloc():
    global port_in_use
    this_port = 0
    for this_port in range(49152, 65536, 1):
        if str(this_port) not in port_in_use:
            p_stat = is_port_free(this_port)
            if p_stat == "OPEN":
                p_stat = "IN USE / CLOSED"
                client_ip = request.headers.get('X-Forwarded-For')
                if not client_ip:
                    client_ip = request.remote_addr
                port_in_use[str(this_port)] = { "source_ip": [client_ip], "inactivity_timer": "0", "identity": "", "last_beat": datetime.now().strftime("%Y_%m_%d_%H_%M_%S") }
                break

    timestamp    = datetime.now().strftime("%Y_%m_%d_%H_%M_%S_%f")
    base_path    = "/mnt/f/Desktop/test/dockerScriptRunner"
    session_path = os.path.join(base_path, "session_dir", timestamp)
    os.makedirs(session_path)
    trig_cmd = "nohup {base_path}/env/bin/python run_flask_server.py --port {this_port} --session {timestamp} > {base_path}/logs/flask_log_{timestamp}.txt 2>&1 &".format(base_path=base_path, timestamp=timestamp, this_port=str(this_port))
    os.system(trig_cmd)
    return json.dumps({'success': True, 'this_port': str(this_port), 'session': timestamp}), 200, {'ContentType':'application/json'}

@app.route('/port_availability')
def port_avail():
    # Example data
    port_status_entries = []
    for this_port in range(49152, 65536, 1):
        if str(this_port) in port_in_use:
            p_stat = "IN USE / CLOSED"
            src_ip = ", ".join(port_in_use[str(this_port)]["source_ip"])
            i_time = "{tm} minutes".format(tm=port_in_use[str(this_port)]["inactivity_timer"]) 
        else:
            p_stat = is_port_free(this_port)
            src_ip = "-"
            i_time = "-"
        lit = {'port': this_port, 'status': p_stat, 'source_ip': src_ip, 'inactivity_timer': i_time}
        port_status_entries.append(lit)

    return render_template('port_avail.j2', port_status_entries=port_status_entries)

@app.route('/port_heartbeat')
def port_hb():
    global port_in_use
    duplicate_msg = ""
    # Attempt to get the client IP from X-Forwarded-For header (common in proxy setups)
    client_ip = request.headers.get('X-Forwarded-For')

    if not client_ip:
        # If X-Forwarded-For header is not present, use the remote_addr attribute
        client_ip = request.remote_addr

    this_port = request.args.get("this_port")
    inactive  = request.args.get("inactive")
    if port_in_use.get(this_port, "NA") == "NA":
        duplicate_msg = "Why you are seeing this message? - Session Unassigned"
    else:
        port_in_use[this_port]["inactivity_timer"] = inactive

        print("ip", client_ip, port_in_use[this_port]["source_ip"])
        print("identity", port_in_use[this_port]["identity"], request.args.get("identity"))
        port_in_use[this_port]["last_beat"] = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        if port_in_use[this_port]["identity"] == "":
            port_in_use[this_port]["identity"] = request.args.get("identity")
        if client_ip not in port_in_use[this_port]["source_ip"]:
            duplicate_msg = "Why you are seeing this message? - Duplicate TAB not allowed"
        elif port_in_use[this_port]["identity"] != request.args.get("identity"):
            duplicate_msg = "Why you are seeing this message? - Duplicate TAB not allowed"

    print(port_in_use)

    return json.dumps({'success':True, 'duplicate': duplicate_msg}), 200, {'ContentType':'application/json'}


if __name__ == '__main__':
    background_thread = threading.Thread(target=run_scheduled_tasks)
    background_thread.start()
    
    app.run(host="0.0.0.0", port=8778) #never put this server in debug mode, all functions begin to fail

