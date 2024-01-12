from flask import Flask, render_template, request
import os, json, zipfile, shutil, argparse
#from datetime import datetime

app = Flask(__name__)
DEFAULT_PORT = 5000
parser = argparse.ArgumentParser(description='Run a Flask application with a custom port.')
parser.add_argument('--port', type=int, help='Port number to run the Flask app on')
parser.add_argument('--session', type=str, help='Session Directory to store files in')
args = parser.parse_args()
this_port = args.port if args.port else DEFAULT_PORT

@app.route('/')
def index():
    
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
    return render_template('base.j2', inp_ops=inp_ops, sys_ops=sys_ops, session_path=session_path, this_port=this_port)

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
