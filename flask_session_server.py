from flask import Flask, render_template, request
import socket, json, os
from datetime import datetime
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/port_heartbeat": {"origins": "*"}})
port_in_use = {}

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
    this_port = 0
    for this_port in range(49152, 65536, 1):
        if str(this_port) not in port_in_use:
            p_stat = is_port_free(this_port)
            if p_stat == "OPEN":
                p_stat = "IN USE / CLOSED"
                client_ip = request.headers.get('X-Forwarded-For')
                if not client_ip:
                    client_ip = request.remote_addr
                port_in_use[str(this_port)] = { "source_ip": [client_ip], "inactivity_timer": "0" }
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
    # Attempt to get the client IP from X-Forwarded-For header (common in proxy setups)
    client_ip = request.headers.get('X-Forwarded-For')

    if not client_ip:
        # If X-Forwarded-For header is not present, use the remote_addr attribute
        client_ip = request.remote_addr

    this_port = request.args.get("this_port")
    inactive  = request.args.get("inactive")
    if port_in_use.get(this_port, "NA") == "NA":
        port_in_use[this_port] = { "source_ip": [client_ip], "inactivity_timer": inactive }
    else:
        port_in_use[this_port]["inactivity_timer"] = inactive

        if client_ip not in port_in_use[this_port]["source_ip"]:
            port_in_use[this_port]["source_ip"].append(client_ip)

    print(port_in_use)

    return json.dumps({'success':True}), 200, {'ContentType':'application/json'}


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8778)

