from flask import Flask, render_template, request, session
from flask_session import Session
from flask_cors import CORS
import uuid
import os, json, zipfile, shutil, argparse
import logging
#from datetime import datetime

app = Flask(__name__)

DEFAULT_PORT = 5000
parser = argparse.ArgumentParser(description='Run a Flask application with a custom port.')
parser.add_argument('--port', type=int, help='Port number to run the Flask app on')
parser.add_argument('--session', type=str, help='Session Directory to store files in')
args = parser.parse_args()
this_port = args.port if args.port else DEFAULT_PORT

logging.basicConfig(filename=os.path.join('/mnt/f/Desktop/test/dockerScriptRunner/logs', 'logger_{session}.txt'.format(session=args.session)), level=logging.INFO)

app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = os.path.join('/mnt/f/Desktop/test/dockerScriptRunner/flask_session_dir', args.session)
Session(app)
CORS(app, resources={r"/session_allocate": {"origins": "*"}})
#CORS(app, resources={r"/session_allocate": {"origins": "http://localhost:8778 https://localhost:8778", "allow_headers": "*"}})

@app.before_request
def check_session():
    if request.path == '/session_allocate':
        return None
    elif request.path != '/session_allocate':
        client_ip = request.headers.get('X-Forwarded-For')
        if not client_ip:
            client_ip = request.remote_addr

        if app.config['session_id'] != "" and app.config['ip_address'] != "":
            session.clear()
            if app.config.get('session_id') == request.args.get('session_id'):
                session['session_id']    = request.args.get('session_id')
                app.config['session_id'] = ""

            if app.config.get('ip_address') == client_ip:
                session['ip_address']    = client_ip
                app.config['ip_address'] = ""

        if session.get('session_id') != request.args.get('session_id'):
            return json.dumps({'server_msg': 'Why you are seeing this message? - Session Non-Existent/Session Timed Out'}), 200, {'ContentType':'application/json'}

        if session.get('ip_address') != client_ip:
            return json.dumps({'server_msg': 'Why you are seeing this message? - Session Non-Existent/IP Changed'}), 200, {'ContentType':'application/json'}


@app.route('/session_allocate')
def session_allocate():
    client_ip = request.headers.get('X-Forwarded-For')
    if not client_ip:
        client_ip = request.remote_addr
    if 'session_id' in app.config and 'ip_address' in app.config:
        return json.dumps({'server_msg': 'Session ongoing. Removing the TAB.', 'session_id': ''}), 200, {'ContentType':'application/json'}
    else:
        #session.clear()
        #session['ip_address'] = client_ip
        #session['session_id'] = str(uuid.uuid4())
        app.config['ip_address'] = client_ip
        app.config['session_id'] = str(uuid.uuid4())
        return json.dumps({'server_msg': 'New Session Created.', 'session_id': app.config['session_id']}), 200, {'ContentType':'application/json'}

@app.route('/')
def index():
    print("HIHIHIHIHIHIHIH")
    #timestamp          = datetime.now().strftime("%Y_%m_%d_%H_%M_%S_%f")
    session_path       = os.path.join("/mnt/f/Desktop/test/dockerScriptRunner/session_dir", args.session)
    #os.makedirs(session_path)

    logical_proc_count = os.cpu_count()
    mem_bytes          = os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES')
    mem_gib            = int(mem_bytes/(1024.**3))

    inp_ops = {}
    sys_ops = {
            "proc_count": logical_proc_count,
            "mem_in_gbs": mem_gib
            }
    with open(os.path.join("data", "input_ops.json")) as f:
        inp_ops = json.loads(f.read())

    return render_template('base.j2', inp_ops=inp_ops, sys_ops=sys_ops, session_path=session_path, this_port=this_port, session_id=request.args.get('session_id'))


@app.route('/process_code_zip', methods = ["GET", "POST"])
def process_code():

    if request.method == 'POST':
        inp_info          = json.loads(request.form.get("inp_info"))
        zip_file          = request.files.get("zip_file")
        path_to_zip_file  = os.path.join(inp_info.get("session_p"), zip_file.filename)
        zip_dir_name      = zip_file.filename.split(".zip")[0].strip()
        dir_to_extract_to = os.path.join(inp_info.get("session_p"), zip_dir_name)
        session_name      = os.path.basename(inp_info.get("session_p"))
        dockerf_template  = render_template("Dockerfile.j2", inp_info=inp_info, session_name=session_name)
        dockerc_template  = render_template("docker-compose.j2", session_name=session_name, session_dir=inp_info.get("session_p"))
        usr_request_json  = json.loads(inp_info.get("inp_tarea"))
        run_script_templ  = render_template("runScript.j2", usr_request_json=usr_request_json)

        shutil.rmtree(inp_info.get("session_p"))
        shutil.os.makedirs(inp_info.get("session_p"))

        with open(path_to_zip_file, "wb+") as f:
            f.write(zip_file.read())

        with zipfile.ZipFile(path_to_zip_file, 'r') as zip_ref:
            zip_ref.extractall(inp_info.get("session_p"))

        os.remove(path_to_zip_file)
        for item in os.listdir(dir_to_extract_to):
            item_path = os.path.join(dir_to_extract_to, item)
            shutil.move(item_path, inp_info.get("session_p"))

        os.rmdir(dir_to_extract_to)

        with open(os.path.join(inp_info.get("session_p"), "Dockerfile"), "w+") as f:
            f.write(dockerf_template)

        with open(os.path.join(inp_info.get("session_p"), "docker-compose.yml"), "w+") as f:
            f.write(dockerc_template)

        with open(os.path.join(inp_info.get("session_p"), "runScript.sh"), "w+") as f:
            f.write(run_script_templ)

    return json.dumps({'success':True}), 200, {'ContentType':'application/json'}

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=this_port)
