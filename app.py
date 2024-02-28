from flask import Flask, jsonify, abort, make_response, request, render_template, redirect, url_for
import subprocess
import psutil
import threading
from threading import Lock

# Create a lock for controlling access to the endpoint
endpoint_lock = Lock()

from modules.use_case.use_cases import *

app = Flask(__name__)

running_thread = None

# region Template Render
@app.route('/')
def main_page():
    return render_template('use_case/uc_local.html')

@app.route('/uc-local')
def use_case_local():
    return render_template('use_case/uc_local.html')

@app.route('/uc-remote')
def use_case_remote():
    return render_template('use_case/uc_remote.html')

@app.route('/uc_scenarios')
def use_case_scenarios_page():
    return render_template('use_case/uc_scenarios.html')

# endregion
# region Use Case
@app.route('/api/uc_config', methods=['POST'])
def uc_update_config():
    if not endpoint_lock.acquire(blocking=False):
        # If the lock is already acquired, return an error response
        return jsonify({'error': 'Another task is currently being processed. Please try again later.'}), 429

    try:
        req_data = request.get_json()
        if not req_data:
            return jsonify({'error': 'Request data is empty or None.'}), 400
        server_ip = req_data.get('server_ip')
        if not server_ip:
            return jsonify({'error': 'Server IP is missing.'}), 400
        server_port = req_data.get('server_port')
        uc_projects = gns3_query_get_projects(server_ip, server_port)
        server_name = gns3_query_get_computes_name(server_ip, server_port)
        project_ids = [project['project_id'] for project in uc_projects]
        project_names = [project['name'] for project in uc_projects]
        project_status = [project['status'] for project in uc_projects]
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM uc_config WHERE server_ip=?", (server_ip,))
        row = c.fetchone()
        if row[0] == 0:
            c.execute(
                "INSERT INTO uc_config (server_ip, server_port, server_name, project_list, project_name, project_status) VALUES (?, ?, ?, ?, ?, ?)",
                (server_ip, server_port, server_name, json.dumps(project_ids), json.dumps(project_names),
                 json.dumps(project_status)))
        else:
            c.execute(
                "UPDATE uc_config SET server_port = ?, server_name = ?, project_list = ?, project_name = ?, project_status = ? WHERE server_ip = ?",
                (server_port, server_name, json.dumps(project_ids), json.dumps(project_names), json.dumps(project_status),
                 server_ip))
        # Insert data into the uc_projects table if project_id is present
        if 'project_id' in req_data:
            project_id = req_data['project_id']
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute("SELECT project_list FROM uc_config WHERE server_ip = ? AND server_port = ?",
                      (server_ip, server_port))
            row = c.fetchone()
            if row:
                project_list = json.loads(row[0])
                if project_id in project_list:
                    index = project_list.index(project_id)
                    c.execute("SELECT project_name, project_status FROM uc_config WHERE server_ip = ? AND server_port = ?",
                              (server_ip, server_port))
                    row = c.fetchone()
                    if row:
                        project_name = json.loads(row[0])[index]
                        project_status = json.loads(row[1])[index]
                        # Check if the project_id already exists in the uc_projects table
                        c.execute("SELECT COUNT(*) FROM uc_projects WHERE project_id=?", (project_id,))
                        row = c.fetchone()
                        if row[0] == 0:
                            c.execute(
                                "INSERT INTO uc_projects (server_name, server_ip, server_port, project_id, project_name, project_status) VALUES (?, ?, ?, ?, ?, ?)",
                                (req_data.get('server_name'), server_ip, server_port, project_id, project_name,
                                 project_status))
        conn.commit()
        conn.close()
    finally:
        endpoint_lock.release()

    return jsonify({'scenario': {'running': True}}), 201

@app.route('/api/uc_config', methods=['GET'])
def uc_get_config():
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM uc_config")
    rows = c.fetchall()
    conn.close()
    uc_config_data = [dict(row) for row in rows]
    return jsonify(uc_config_data)

@app.route('/api/uc_projects', methods=['GET'])
def uc_get_project_list():
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT server_ip, server_port FROM uc_config")
    row = c.fetchone()
    if row is None:
        conn.close()
        return jsonify({'error': 'Server IP and Port not set in uc_config table'}), 500
    server_ip = row[0]
    server_port = row[1]
    c.execute("SELECT project_list, project_name, project_status FROM uc_config WHERE server_ip=? AND server_port=?",
              (server_ip, server_port))
    row = c.fetchone()
    if row is None:
        conn.close()
        return jsonify({'error': 'Project list not found in uc_config file'}), 500
    project_list = json.loads(row[0])
    project_name = json.loads(row[1])
    project_status = json.loads(row[2])
    project_data = [{'id': project_list[i], 'name': project_name[i], 'status': project_status[i]} for i in
                    range(len(project_list))]
    conn.close()
    return jsonify({'projects': project_data})

@app.route('/api/uc_scenarios', methods=['GET', 'POST', 'PUT'])
def uc_scenarios():
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    if request.method == 'GET':
        c.execute("SELECT id, scenario_name AS title, scenario_description AS description FROM uc_scenarios")
        rows = c.fetchall()
        uc_scenarios = [{'id': row[0], 'title': row[1], 'description': row[2]} for row in rows]
        conn.close()
        return jsonify({'scenarios': uc_scenarios})
    elif request.method == 'POST':
        # Get the payload
        scenario_name = request.json.get('scenario_name')
        scenario_description = request.json.get('scenario_description')
        scenario_id = request.json.get('scenario_id')
        # If scenario_id is not provided, insert a new scenario
        if scenario_id is None:
            c.execute("INSERT INTO uc_scenarios (scenario_name, scenario_description) VALUES (?, ?)",
                      (scenario_name, scenario_description))
            scenario_id = c.lastrowid
            conn.commit()
        # If scenario_id is provided, update an existing scenario
        else:
            # Check if the scenario exists
            c.execute("SELECT * FROM uc_scenarios WHERE id=?", (scenario_id,))
            row = c.fetchone()
            if not row:
                conn.close()
                return jsonify({'error': 'Scenario not found.'}), 404
            # Update the scenario values
            if scenario_name:
                c.execute("UPDATE uc_scenarios SET scenario_name=? WHERE id=?", (scenario_name, scenario_id))
            if scenario_description:
                c.execute("UPDATE uc_scenarios SET scenario_description=? WHERE id=?",
                          (scenario_description, scenario_id))
            conn.commit()
        # Return the scenario
        c.execute("SELECT id, scenario_name AS title, scenario_description AS description FROM uc_scenarios WHERE id=?",
                  (scenario_id,))
        row = c.fetchone()
        scenario = {'id': row[0], 'title': row[1], 'description': row[2]}
        conn.close()
        return jsonify({'scenario': scenario})
    elif request.method == 'PUT':
        # Get the payload
        scenario_id = request.view_args.get('scenario_id')
        scenario_name = request.json.get('scenario_name')
        scenario_description = request.json.get('scenario_description')

        # Check if the scenario exists
        c.execute("SELECT * FROM uc_scenarios WHERE id=?", (scenario_id,))
        row = c.fetchone()
        if not row:
            conn.close()
            return jsonify({'error': 'Scenario not found.'}), 404
        # Update the scenario values
        if scenario_name:
            c.execute("UPDATE uc_scenarios SET scenario_name=? WHERE id=?", (scenario_name, scenario_id))
        if scenario_description:
            c.execute("UPDATE uc_scenarios SET scenario_description=? WHERE id=?", (scenario_description, scenario_id))
        conn.commit()
        # Return the updated scenario
        c.execute("SELECT id, scenario_name AS title, scenario_description AS description FROM uc_scenarios WHERE id=?",
                  (scenario_id,))
        row = c.fetchone()
        scenario = {'id': row[0], 'title': row[1], 'description': row[2]}
        conn.close()
        return jsonify({'scenario': scenario})

@app.route('/api/uc_scenarios/<int:scenario_id>', methods=['GET'])
def uc_get_scenario(scenario_id):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT * FROM uc_scenarios WHERE id=?", (scenario_id,))
    row = c.fetchone()
    conn.close()
    if row is None:
        abort(404)
    scenario = {
        'id': row[0],
        'name': row[1],
        'description': row[2]
    }
    return jsonify({'scenario': scenario})

@app.route('/api/uc_scenario_status_old', methods=['GET'])
def uc_get_scenario_status_old():
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute(
        "SELECT uc_scenario_status.id, uc_scenario_status.server_ip, uc_config.server_port, uc_config.server_name, uc_scenario_status.project_id, uc_projects.project_name, uc_scenario_status.scenario_id, uc_scenario_status.status, uc_scenario_status.process_id FROM uc_scenario_status JOIN uc_projects ON uc_scenario_status.project_id = uc_projects.project_id JOIN uc_config ON uc_scenario_status.server_ip = uc_config.server_ip;")
    rows = c.fetchall()
    conn.close()
    data = []
    for row in rows:
        data.append({
            'id': row[0],
            'server_ip': row[1],
            'server_name': row[3],
            'server_port': row[2],
            'project_id': row[4],
            'project_name': row[5],
            'scenario_id': row[6],
            'status': row[7],
            'process_id': row[8]
        })
    return jsonify({'scenario_status': data})


@app.route('/api/uc_scenario_status', methods=['GET'])
def uc_get_scenario_status():
    # Retrieve the scenario ID from the query parameter, if provided
    scenario_id = request.args.get('id')

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    if scenario_id:
        # SQL query to get the status of a specific scenario by ID
        c.execute("""
            SELECT 
                uc_scenario_status.id, 
                uc_scenario_status.server_ip, 
                uc_config.server_port, 
                uc_config.server_name, 
                uc_scenario_status.project_id, 
                uc_projects.project_name, 
                uc_scenario_status.scenario_id, 
                uc_scenario_status.status, 
                uc_scenario_status.process_id 
            FROM 
                uc_scenario_status 
            JOIN 
                uc_projects ON uc_scenario_status.project_id = uc_projects.project_id 
            JOIN 
                uc_config ON uc_scenario_status.server_ip = uc_config.server_ip
            WHERE 
                uc_scenario_status.scenario_id = ?
        """, (scenario_id,))

        row = c.fetchone()

        if row:
            data = {
                'id': row [0], 'server_ip': row [1], 'server_port': row [2], 'server_name': row [3],
                'project_id': row [4], 'project_name': row [5], 'scenario_id': row [6], 'status': row [7],
                'process_id': row [8]
            }
            return jsonify({'scenario_status': data})
        else:
            return jsonify({'message': 'Scenario not run yet'}), 404
    else:
        # SQL query to get the status of all scenarios if no ID is provided
        c.execute("""
            SELECT 
                uc_scenario_status.id, 
                uc_scenario_status.server_ip, 
                uc_config.server_port, 
                uc_config.server_name, 
                uc_scenario_status.project_id, 
                uc_projects.project_name, 
                uc_scenario_status.scenario_id, 
                uc_scenario_status.status, 
                uc_scenario_status.process_id 
            FROM 
                uc_scenario_status 
            JOIN 
                uc_projects ON uc_scenario_status.project_id = uc_projects.project_id 
            JOIN 
                uc_config ON uc_scenario_status.server_ip = uc_config.server_ip
        """)

        rows = c.fetchall()
        data = [{
            'id': row [0], 'server_ip': row [1], 'server_port': row [2], 'server_name': row [3], 'project_id': row [4],
            'project_name': row [5], 'scenario_id': row [6], 'status': row [7], 'process_id': row [8]
        } for row in rows]

        return jsonify({'scenario_status': data})

@app.route('/api/tasks/<int:scenario_id>', methods=['POST'])
def uc_create_task(scenario_id):
    req_data = request.get_json()
    server_ip = req_data.get('server_ip')
    port = req_data.get('port')
    project_id = req_data.get('project_id')
    use_case_function = None
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM uc_scenario_status WHERE server_ip=? AND project_id=? AND scenario_id=?",
              (server_ip, project_id, scenario_id,))
    row = c.fetchone()
    if row[0] == 0:
        c.execute("INSERT INTO uc_scenario_status (server_ip, project_id, scenario_id, status) VALUES (?, ?, ?, ?)",
                  (server_ip, project_id, scenario_id, 1))
    else:
        c.execute("UPDATE uc_scenario_status SET status=? WHERE server_ip=? AND project_id=? AND scenario_id=?",
                  (1, server_ip, project_id, scenario_id))
    conn.commit()
    conn.close()
    # Call the appropriate use case function based on the scenario_id
    if scenario_id == 1:
        use_case_function_name = "use_case_1"
        use_case_function = globals().get(use_case_function_name)
    elif scenario_id == 2:
        use_case_function_name = "use_case_2"
        use_case_function = globals().get(use_case_function_name)
    elif scenario_id == 3:
        use_case_function_name = "use_case_3"
        use_case_function = globals().get(use_case_function_name)
    elif scenario_id == 4:
        use_case_function_name = "use_case_4"
        use_case_function = globals().get(use_case_function_name)
    elif scenario_id == 5:
        use_case_function_name = "use_case_5"
        use_case_function = globals().get(use_case_function_name)
    else:
        return jsonify({'error': 'Invalid scenario ID.'}), 400
    if use_case_function is not None:
        success = use_case_function(server_ip, port, project_id, 'on')
        if success:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute("UPDATE uc_scenario_status SET status=? WHERE server_ip=? AND project_id=? AND scenario_id=?",
                      (2, server_ip, project_id, scenario_id))
            conn.commit()
            conn.close()
    scenario = {
        'running': True
    }
    return jsonify({'scenario': scenario}), 201

@app.route('/api/tasks/<int:scenario_id>', methods=['DELETE'])
def uc_delete_task(scenario_id):
    req_data = request.get_json()
    server_ip = req_data.get('server_ip')
    port = req_data.get('port')
    project_id = req_data.get('project_id')
    conn = sqlite3.connect(db_path)
    status = '3'
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM uc_scenario_status WHERE server_ip=? AND project_id=? AND scenario_id=?",
              (server_ip, project_id, scenario_id,))
    row = c.fetchone()
    if row[0] == 0:
        c.execute("INSERT INTO uc_scenario_status (server_ip, project_id, scenario_id, status) VALUES (?, ?, ?, ?)",
                  (server_ip, project_id, scenario_id, status))
    else:
        c.execute("UPDATE uc_scenario_status SET status=? WHERE server_ip=? AND project_id=? AND scenario_id=?",
                  (status, server_ip, project_id, scenario_id))
    conn.commit()
    conn.close()
    # Call the appropriate use case function based on the scenario_id
    if scenario_id == 1:
        use_case_function_name = f"use_case_{scenario_id}"
        use_case_function = globals().get(use_case_function_name)
        if use_case_function is not None:
            success = use_case_function(server_ip, port, project_id, 'off')
            if success:
                status = 0
    elif scenario_id == 2:
        use_case_function_name = f"use_case_{scenario_id}"
        use_case_function = globals().get(use_case_function_name)
        if use_case_function is not None:
            success = use_case_function(server_ip, port, project_id, 'off')
            if success:
                status = 0
    elif scenario_id == 3:
        use_case_function_name = f"use_case_{scenario_id}"
        use_case_function = globals().get(use_case_function_name)
        if use_case_function is not None:
            success = use_case_function(server_ip, port, project_id, 'off')
            if success:
                status = 0
    elif scenario_id == 4:
        use_case_function_name = f"use_case_{scenario_id}"
        use_case_function = globals().get(use_case_function_name)
        if use_case_function is not None:
            success = use_case_function(server_ip, port, project_id, 'off')
            if success:
                status = 0
    elif scenario_id == 5:
        use_case_function_name = f"use_case_{scenario_id}"
        use_case_function = globals().get(use_case_function_name)
        if use_case_function is not None:
            success = use_case_function(server_ip, port, project_id, 'off')
            if success:
                status = 0
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("UPDATE uc_scenario_status SET status=? WHERE server_ip=? AND project_id=? AND scenario_id=?",
              (status, server_ip, project_id, scenario_id))
    conn.commit()
    conn.close()
    return jsonify({'scenario': "stopped"}), 201

@app.route('/api/run_script', methods=['POST'])
def uc_run_script():
    # Get the script path, arguments, project ID, and scenario ID from the request
    data = request.get_json()
    script_path = data.get('script_path')
    args = data.get('args', [])
    project_id = data.get('project_id')
    scenario_id = data.get('scenario_id')
    # Start the script as a subprocess and store the Popen object
    try:
        proc = subprocess.Popen(['python', script_path] + args)
        pid = proc.pid
        processes[pid] = proc
        # Return the process information in the response
        return jsonify({'pid': pid, 'project_id': project_id, 'scenario_id': scenario_id}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stop_script', methods=['POST'])
def uc_stop_script():
    # Get the project ID and scenario ID from the request body
    project_id = str(request.json.get('project_id'))
    scenario_id = str(request.json.get('scenario_id'))
    # Get the process ID from the scenario status table
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT process_id FROM uc_scenario_status WHERE project_id=? AND scenario_id=?",
              (project_id, scenario_id,))
    row = c.fetchone()
    if row is None:
        return jsonify({'error': 'Scenario not found.'}), 404
    process_id = row[0]
    conn.close()
    # Check if the process ID is valid
    if not process_id or not isinstance(process_id, int):
        return jsonify({'error': 'Invalid process ID.'}), 400
    # Try to get the process by its ID
    try:
        process = psutil.Process(process_id)
    except psutil.NoSuchProcess:
        return jsonify({'error': 'Process not found.'}), 404
    # Try to stop the process
    try:
        process.terminate()
        # Update the scenario status table with null process ID
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("UPDATE uc_scenario_status SET process_id = NULL WHERE project_id = ? AND scenario_id = ?",
                  (project_id, scenario_id,))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Process stopped successfully.'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stop_process', methods=['POST'])
def uc_stop_process():
    # Get the process ID from the request body
    process_id = request.json.get('process_id')

    # Check if the process ID is valid
    if not process_id or not isinstance(process_id, int):
        return jsonify({'error': 'Invalid process ID.'}), 400

    # Try to get the process by its ID
    try:
        process = psutil.Process(process_id)
    except psutil.NoSuchProcess:
        return jsonify({'error': 'Process not found.'}), 404

    # Try to stop the process
    try:
        process.terminate()
        return jsonify({'message': 'Process stopped successfully.'}), 200
    except psutil.AccessDenied:
        return jsonify({'error': 'Access denied. Could not stop process.'}), 403

@app.route('/api/process_info', methods=['POST'])
def uc_process_info():
    # Get the process ID from the request
    data = request.get_json()
    pid = data.get('pid')
    # Get the process object from the global dictionary
    proc = processes.get(pid)
    if proc:
        # Return information about the process
        return jsonify({
            'pid': pid,
            'status': 'running' if proc.poll() is None else 'stopped',
            'returncode': proc.returncode
        })
    else:
        return jsonify({'error': f'Process with PID {pid} not found.'})

@app.route('/api/reset-tables', methods=['POST'])
def reset_tables():
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    # Delete all rows from the uc_config and uc_projects tables
    c.execute('DELETE FROM uc_config')
    c.execute('DELETE FROM uc_projects')
    c.execute('DELETE FROM uc_scenario_status')
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)
# endregion

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
