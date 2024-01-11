from flask import Flask, render_template
import os, json

app = Flask(__name__)

@app.route('/')
def index():
    
    logical_proc_count = os.cpu_count()
    mem_bytes = os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES')
    mem_gib = int(mem_bytes/(1024.**3))

    inp_ops = {}
    sys_ops = {
            "proc_count": logical_proc_count,
            "mem_in_gbs": mem_gib
            }
    with open(os.path.join("data", "input_ops.json")) as f:
        inp_ops = json.loads(f.read())
    return render_template('base.j2', inp_ops=inp_ops, sys_ops=sys_ops)

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=8668)
