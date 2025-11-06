"""
Columbia's COMS W4111.001 Introduction to Databases
Example Webserver
To run locally:
    python server.py
Go to http://localhost:8111 in your browser.
A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""
import os
# accessible as a variable in index.html:
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response, abort
from flask import redirect, url_for
from sqlalchemy import create_engine, text

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)


#
# The following is a dummy URI that does not connect to a valid database. You will need to modify it to connect to your Part 2 database in order to use the data.
#
# XXX: The URI should be in the format of: 
#
#     postgresql://USER:PASSWORD@34.139.8.30/proj1part2
#
# For example, if you had username ab1234 and password 123123, then the following line would be:
#
#     DATABASEURI = "postgresql://ab1234:123123@34.139.8.30/proj1part2"
#
# Modify these with your own credentials you received from TA!
DATABASE_USERNAME = "sr3986"
DATABASE_PASSWRD = "717191"
DATABASE_HOST = "34.139.8.30"
DATABASEURI = f"postgresql://sr3986:717191@34.139.8.30/proj1part2"


#
# This line creates a database engine that knows how to connect to the URI above.
#
engine = create_engine(DATABASEURI)

#
# Example of running queries in your database
# Note that this will probably not work if you already have a table named 'test' in your database, containing meaningful data. This is only an example showing you how to run queries in your database using SQLAlchemy.
#
with engine.connect() as conn:
	create_table_command = """
	CREATE TABLE IF NOT EXISTS test (
		id serial,
		name text
	)
	"""
	res = conn.execute(text(create_table_command))
	insert_table_command = """INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace')"""
	res = conn.execute(text(insert_table_command))
	# you need to commit for create, insert, update queries to reflect
	conn.commit()


@app.before_request
def before_request():
	"""
	This function is run at the beginning of every web request 
	(every time you enter an address in the web browser).
	We use it to setup a database connection that can be used throughout the request.

	The variable g is globally accessible.
	"""
	try:
		g.conn = engine.connect()
	except:
		print("uh oh, problem connecting to database")
		import traceback; traceback.print_exc()
		g.conn = None

@app.teardown_request
def teardown_request(exception):
	"""
	At the end of the web request, this makes sure to close the database connection.
	If you don't, the database could run out of memory!
	"""
	try:
		g.conn.close()
	except Exception as e:
		pass


#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to, for example, localhost:8111/foobar/ with POST or GET then you could use:
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
# 
# see for routing: https://flask.palletsprojects.com/en/1.1.x/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#
@app.route('/')
def index():
	"""
	request is a special object that Flask provides to access web request information:

	request.method:   "GET" or "POST"
	request.form:     if the browser submitted a form, this contains the data in the form
	request.args:     dictionary of URL arguments, e.g., {a:1, b:2} for http://localhost?a=1&b=2

	See its API: https://flask.palletsprojects.com/en/1.1.x/api/#incoming-request-data
	"""

	# DEBUG: this is debugging code to see what request looks like
	print(request.args)


	#
	# example of a database query
	#
	select_query = "SELECT name from test"
	cursor = g.conn.execute(text(select_query))
	names = []
	for result in cursor:
		names.append(result[0])
	cursor.close()

	#
	# Flask uses Jinja templates, which is an extension to HTML where you can
	# pass data to a template and dynamically generate HTML based on the data
	# (you can think of it as simple PHP)
	# documentation: https://realpython.com/primer-on-jinja-templating/
	#
	# You can see an example template in templates/index.html
	#
	# context are the variables that are passed to the template.
	# for example, "data" key in the context variable defined below will be 
	# accessible as a variable in index.html:
	#
	#     # will print: [u'grace hopper', u'alan turing', u'ada lovelace']
	#     <div>{{data}}</div>
	#     
	#     # creates a <div> tag for each element in data
	#     # will print: 
	#     #
	#     #   <div>grace hopper</div>
	#     #   <div>alan turing</div>
	#     #   <div>ada lovelace</div>
	#     #
	#     {% for n in data %}
	#     <div>{{n}}</div>
	#     {% endfor %}
	#
	context = dict(data = names)


	#
	# render_template looks in the templates/ folder for files.
	# for example, the below file reads template/index.html
	#
	return render_template("home.html")


#
# This is an example of a different path.  You can see it at:
# 
#     localhost:8111/another
#
# Notice that the function name is another() rather than index()

@app.route('/another')
def another():
	return render_template("another.html")


# Example of adding new data to the database
@app.route('/add', methods=['POST'])
def add():
	# accessing form inputs from user
	name = request.form['name']
	
	# passing params in for each variable into query
	params = {}
	params["new_name"] = name
	g.conn.execute(text('INSERT INTO test(name) VALUES (:new_name)'), params)
	g.conn.commit()
	return redirect('/')


@app.route('/login')
def login():
	abort(401)
	# Your IDE may highlight this as a problem - because no such function exists (intentionally).
	# This code is never executed because of abort().
	this_is_never_executed()

@app.route('/patient')
def patient():
    try:
        # get the search query string, e.g. ?q=ava
        q = request.args.get("q", "").strip()

        # base query
        sql = """
            SELECT
                patient_id,
                firstname,
                lastname,
                birthdate,
                sex,
                contact_phone,
                contact_email,
                emergency_contact_name,
                emergency_contact_phone
            FROM patient
        """

        # if search is not empty, add WHERE clause
        params = {}
        if q:
            sql += """
                WHERE LOWER(firstname) LIKE LOWER(:q)
                   OR LOWER(lastname) LIKE LOWER(:q)
                   OR LOWER(contact_email) LIKE LOWER(:q)
                   OR LOWER(contact_phone) LIKE LOWER(:q)
            """
            params["q"] = f"%{q}%"

        sql += " ORDER BY patient_id"

        cursor = g.conn.execute(text(sql), params)
        patient_list = []
        for row in cursor:
            patient_list.append({
                "patient_id": row[0],
                "full_name": f"{row[1]} {row[2]}",
                "birthdate": row[3],
                "sex": row[4],
                "contact_phone": row[5],
                "contact_email": row[6],
                "emergency_contact_name": row[7],
                "emergency_contact_phone": row[8],
            })
        cursor.close()

        # pass results to template
        return render_template("patient.html", patient=patient_list)

    except Exception as e:
        print("Error loading patients:", e)
        return f"Error loading patients: {e}"


@app.route("/patient/new", methods=["GET", "POST"])
def patient_new():
    if request.method == "GET":
        return render_template("patient_new.html")

    fn  = request.form.get("firstname", "").strip()
    ln  = request.form.get("lastname", "").strip()
    bd  = request.form.get("birthdate", "").strip()  # expect YYYY-MM-DD
    sex = request.form.get("sex", "").strip()
    ph  = request.form.get("phone", "").strip()
    em  = request.form.get("email", "").strip()
    ecn = request.form.get("emergency_contact_name", "").strip()
    ecp = request.form.get("emergency_contact_phone", "").strip()

    # quick validation for required fields
    missing = [k for k,v in {
        "firstname": fn, "lastname": ln, "birthdate": bd, "sex": sex,
        "phone": ph, "email": em, "emergency_contact_name": ecn, "emergency_contact_phone": ecp
    }.items() if not v]
    if missing:
        return f"Missing required fields: {', '.join(missing)}", 400

    try:
        # Use to_date so 'YYYY-MM-DD' is enforced and safe
        g.conn.execute(
            text("""
                INSERT INTO patient
                    (firstname, lastname, birthdate, sex,
                     contact_phone, contact_email,
                     emergency_contact_name, emergency_contact_phone)
                VALUES
                    (:fn, :ln, to_date(:bd,'YYYY-MM-DD'), :sex,
                     :ph, :em, :ecn, :ecp)
            """),
            {"fn": fn, "ln": ln, "bd": bd, "sex": sex,
             "ph": ph, "em": em, "ecn": ecn, "ecp": ecp}
        )
        g.conn.commit()
        return redirect(url_for("patient"))
    except Exception as e:
        print("Insert failed:", e)
        return f"Insert failed: {e}", 400
@app.route('/patient/create', methods=['POST'])
def patient_create():
    sql = text("""
        INSERT INTO patient (firstname, lastname, birthdate, sex, contact_phone, contact_email)
        VALUES (:fn, :ln, :bd, :sex, :ph, :em)
        RETURNING patient_id
    """)
    vals = {
        "fn": request.form['firstname'],
        "ln": request.form['lastname'],
        "bd": request.form['birthdate'],
        "sex": request.form.get('sex'),
        "ph": request.form.get('contact_phone'),
        "em": request.form.get('contact_email'),
    }
    try:
        row = g.conn.execute(sql, vals).fetchone()
        g.conn.commit()
        return redirect(url_for('patient'))
    except Exception as e:
        g.conn.rollback()
        return f"Insert failed: {e}", 400


@app.route('/patient/<int:patient_id>/edit')
def patient_edit(patient_id):
    row = g.conn.execute(text("""
        SELECT patient_id, firstname, lastname, birthdate, sex, contact_phone, contact_email
        FROM patient WHERE patient_id = :pid
    """), {"pid": patient_id}).fetchone()
    if not row: abort(404)
    return render_template('patient_edit.html', p=row)


@app.route('/patient/<int:patient_id>/update', methods=['POST'])
def patient_update(patient_id):
    sql = text("""
        UPDATE patient SET firstname=:fn, lastname=:ln, contact_phone=:ph, contact_email=:em
        WHERE patient_id=:pid
    """)
    try:
        g.conn.execute(sql, {
            "fn": request.form['firstname'],
            "ln": request.form['lastname'],
            "ph": request.form.get('contact_phone'),
            "em": request.form.get('contact_email'),
            "pid": patient_id
        })
        g.conn.commit()
        return redirect(url_for('patient'))
    except Exception as e:
        g.conn.rollback()
        return f"Update failed: {e}", 400

@app.route('/patient/<int:patient_id>/delete', methods=['POST'])
def patient_delete(patient_id):
    try:
        g.conn.execute(text("DELETE FROM patient WHERE patient_id=:pid"), {"pid": patient_id})
        g.conn.commit()
        return redirect(url_for('patient'))
    except Exception as e:
        g.conn.rollback()
        return f"Delete failed: {e}", 400



@app.route('/provider')
def provider():
    try:
        cursor = g.conn.execute(text(
            "SELECT provider_id, full_name, specialty  FROM provider"
        ))
        provider_list = []
        for row in cursor:
            provider_list.append({
                "provider_id": row[0],
                "full_name": row[1],
                "specialty": row[2]
            })
        cursor.close()
        context = dict(provider=provider_list)
        return render_template("provider.html", **context)
    except Exception as e:
        print("Error loading providers:", e)
        return "Error loading providers."

@app.route('/visit')
def visit():
    try:
        cursor = g.conn.execute(text(
            "SELECT visit_id, patient_id, provider_id, visit_date_time, location, visit_type, reason, status FROM visit"
        ))
        visit_list = []
        for row in cursor:
            visit_list.append({
                "visit_id": row[0],
                "patient_id": row[1],
                "provider_id": row[2],
                "visit_date_time": row[3],
                "location": row[4],
                "visit_type": row[5],
		"reason": row[6],
		"status": row[7]
            })
        cursor.close()
        context = dict(visit=visit_list)
        return render_template("visit.html", **context)
    except Exception as e:
        print("Error loading visits:", e)
        return "Error loading visits."

@app.route('/patient_allergy')
def patient_allergy():
    try:
        cursor = g.conn.execute(text("""
            SELECT p.patient_id, p.firstname || ' ' || p.lastname AS full_name,
                   pa.substance, pa.reaction, pa.severity
            FROM patient p
            JOIN patient_allergy pa ON p.patient_id = pa.patient_id;
        """))
        allergy_list = []
        for row in cursor:
            allergy_list.append({
                "patient_id": row[0],
                "patient_name": row[1],
                "substance": row[2],
                "reaction": row[3],
                "severity": row[4]
            })
        cursor.close()
        context = dict(allergies=allergy_list)
        return render_template("patient_allergy.html", **context)
    except Exception as e:
        print("Error loading patient allergies:", e)

@app.route('/diagnosis')
def diagnosis():
    try:
        cursor = g.conn.execute(text("""
            SELECT v.visit_id, d.dx_code, d.dx_name
            FROM visit v
            JOIN visit_diagnosis vd ON v.visit_id = vd.visit_id
            JOIN diagnosis d ON vd.dx_code = d.dx_code;
        """))
        diagnosis_list = []
        for row in cursor:
            diagnosis_list.append({
                "visit_id": row[0],
                "dx_code": row[1],
                "dx_name": row[2]
            })
        cursor.close()
        context = dict(diagnoses=diagnosis_list)
        return render_template("diagnosis.html", **context)
    except Exception as e:
        print("Error loading diagnoses:", e)
        return "Error loading diagnoses."

@app.route('/prescription')
def prescription():
    try:
        cursor = g.conn.execute(text("""
            SELECT p.rx_id, p.provider_id, pr.full_name AS provider_name, 
                   p.visit_id, v.patient_id, pt.firstname || ' ' || pt.lastname AS patient_name,
                   p.dose, p.route, p.frequency, p.quantity, p.start_date, p.end_date
            FROM prescription p
            JOIN provider pr ON p.provider_id = pr.provider_id
            JOIN visit v ON p.visit_id = v.visit_id
            JOIN patient pt ON v.patient_id = pt.patient_id;
        """))
        prescription_list = []
        for row in cursor:
            prescription_list.append({
                "rx_id": row[0],
                "provider_id": row[1],
                "provider_name": row[2],
                "visit_id": row[3],
                "patient_id": row[4],
                "patient_name": row[5],
                "dose": row[6],
                "route": row[7],
                "frequency": row[8],
                "quantity": row[9],
                "start_date": row[10],
                "end_date": row[11]
            })
        cursor.close()
        context = dict(prescriptions=prescription_list)
        return render_template("prescription.html", **context)
    except Exception as e:
        print("Error loading prescriptions:", e)
        return "Error loading prescriptions."

@app.route('/medication')
def medication():
    try:
        cursor = g.conn.execute(text("""
            SELECT m.med_id, m.drug_name, m.brand_name, m.dosage_form,
                   p.rx_id, pt.firstname || ' ' || pt.lastname AS patient_name, pr.full_name AS provider_name
            FROM medication m
            JOIN prescription_medication pm ON m.med_id = pm.med_id
            JOIN prescription p ON pm.rx_id = p.rx_id
            JOIN visit v ON p.visit_id = v.visit_id
            JOIN patient pt ON v.patient_id = pt.patient_id
            JOIN provider pr ON p.provider_id = pr.provider_id;
        """))
        med_list = []
        for row in cursor:
            med_list.append({
                "med_id": row[0],
                "drug_name": row[1],
                "brand_name": row[2],
                "dosage_form": row[3],
                "rx_id": row[4],
                "patient_name": row[5],
                "provider_name": row[6]
            })
        cursor.close()
        context = dict(medications=med_list)
        return render_template("medication.html", **context)
    except Exception as e:
        print("Error loading medications:", e)
        return "Error loading medications" + str(e)

@app.route('/allergy_conflict')
def allergy_conflict():
    try:
        cursor = g.conn.execute(text("""
            SELECT pt.patient_id,
                   pt.firstname || ' ' || pt.lastname AS patient_name,
                   pa.substance,
                   pa.reaction,
                   pa.severity,
                   m.med_id,
                   m.drug_name AS med_generic_name,
                   m.brand_name AS med_brand_name,
                   m.dosage_form,
                   ac.med_id AS conflict_med_id
            FROM patient pt
            JOIN patient_allergy pa ON pt.patient_id = pa.patient_id
            JOIN allergyconflict ac ON pa.allergy_id = ac.allergy_id
            JOIN medication m ON ac.med_id = m.med_id;
        """))

        conflict_list = []
        for row in cursor:
            conflict_list.append({
                "patient_id": row[0],
                "patient_name": row[1],
                "allergy_substance": row[2],
                "reaction": row[3],
                "severity": row[4],
                "med_id": row[5],
                "med_generic_name": row[6],
                "med_brand_name": row[7],
                "dosage_form": row[8],
                "conflict_med_id": row[9]
            })

        cursor.close()
        context = dict(conflicts=conflict_list)
        return render_template("allergy_conflict.html", **context)

    except Exception as e:
        print("Error loading allergy conflicts:", e)
        return "Error loading allergy conflicts."

@app.route("/admin/seed_conflicts")
def seed_conflicts():
    pairs = [
        ("Penicillin", "Amoxicillin"),
        ("Penicillin", "Penicillin V"),
        ("NSAIDs", "Ibuprofen"),
        ("NSAIDs", "Naproxen"),
        ("Sulfa", "Sulfamethoxazole"),
        ("Sulfa", "Trimethoprim-Sulfamethoxazole"),
        ("Aspirin", "Aspirin"),
        ("Cephalosporins", "Ceftriaxone"),
        ("Tetracycline", "Doxycycline"),
        ("Macrolides", "Azithromycin"),
        ("ACE inhibitors", "Lisinopril"),
        ("Codeine", "Morphine"),
    ]
    inserted = 0
    with g.conn.begin() as tx:
        for substance, drug in pairs:
            rows = g.conn.execute(text("""
                SELECT pa.allergy_id, m.med_id
                FROM patient_allergy pa
                JOIN medication m ON LOWER(m.drug_name) = LOWER(:drug)
                WHERE LOWER(pa.substance) = LOWER(:sub)
            """), {"sub": substance, "drug": drug}).fetchall()

            for aid, mid in rows:
                g.conn.execute(text("""
                    INSERT INTO allergyconflict(allergy_id, med_id)
                    VALUES (:aid, :mid)
                    ON CONFLICT DO NOTHING
                """), {"aid": aid, "mid": mid})
                inserted += 1
    return redirect(url_for('allergy_conflict'))


@app.route('/reports/rx_counts')
def report_rx_counts():
    min_ct = int(request.args.get('min', 1))
    rows = g.conn.execute(text("""
        SELECT pt.patient_id,
               pt.firstname || ' ' || pt.lastname AS patient_name,
               COUNT(p.rx_id) AS rx_count
        FROM patient pt
        JOIN visit v   ON v.patient_id = pt.patient_id
        JOIN prescription p ON p.visit_id = v.visit_id
        GROUP BY pt.patient_id, patient_name
        HAVING COUNT(p.rx_id) >= :m
        ORDER BY rx_count DESC, patient_name
    """), {"m": min_ct}).fetchall()
    return render_template('report_rx_counts.html', rows=rows, min=min_ct)

@app.route("/reports/rx_counts", methods=["GET"])
def report_rx_counts():
    """
    Query param:
      q = drug generic or brand substring (case-insensitive)
    Example:
      /reports/rx_counts?q=ibuprofen
    """
    q = request.args.get("q", "").strip()
    rows = []
    error = None
    try:
        if q:
            rows = g.conn.execute(text("""
                SELECT
                    pr.provider_id,
                    pr.full_name,
                    COUNT(*) AS rx_count
                FROM prescription p
                JOIN provider pr ON pr.provider_id = p.provider_id
                JOIN prescription_medication pm ON pm.rx_id = p.rx_id
                JOIN medication m ON m.med_id = pm.med_id
                WHERE LOWER(m.drug_name) LIKE LOWER(:q)
                   OR LOWER(m.brand_name) LIKE LOWER(:q)
                GROUP BY pr.provider_id, pr.full_name
                ORDER BY rx_count DESC, pr.full_name
            """), {"q": f"%{q}%"}).fetchall()
    except Exception as e:
        print("report_rx_counts failed:", e)
        error = str(e)

    return render_template("report_rx_counts.html", q=q, rows=rows, error=error)


# --- Reports: "Patients with diagnosis (code/name) but NO prescription" ---
@app.route("/reports/no_rx_for_dx", methods=["GET"])
def report_no_rx_for_dx():
    """
    Query param:
      dx = diagnosis code exact match OR part of diagnosis name (case-insensitive)
    Example:
      /reports/no_rx_for_dx?dx=J20
      /reports/no_rx_for_dx?dx=asthma
    """
    dx = request.args.get("dx", "").strip()
    rows = []
    error = None
    try:
        if dx:
            rows = g.conn.execute(text("""
                SELECT DISTINCT
                    pt.patient_id,
                    pt.firstname || ' ' || pt.lastname AS patient_name,
                    d.dx_code,
                    d.dx_name
                FROM visit v
                JOIN patient pt ON pt.patient_id = v.patient_id
                JOIN visit_diagnosis vd ON vd.visit_id = v.visit_id
                JOIN diagnosis d ON d.dx_code = vd.dx_code
                LEFT JOIN prescription p ON p.visit_id = v.visit_id
                WHERE (LOWER(d.dx_code) = LOWER(:dx_exact)
                       OR LOWER(d.dx_name) LIKE LOWER(:dx_like))
                  AND p.rx_id IS NULL
                ORDER BY pt.patient_id
            """), {"dx_exact": dx, "dx_like": f"%{dx}%"}).fetchall()
    except Exception as e:
        print("report_no_rx_for_dx failed:", e)
        error = str(e)

    return render_template("report_no_rx_for_dx.html", dx=dx, rows=rows, error=error)

@app.route('/patients')
def patients_alias():
    return redirect(url_for('patient'))


@app.route('/providers')
def providers_alias():
    return redirect(url_for('provider'))

@app.route('/visits')
def visits_alias():
    return redirect(url_for('visit'))

@app.route('/diagnoses')
def diagnoses_alias():
    return redirect(url_for('diagnosis'))

@app.route('/medications')
def medications_alias():
    return redirect(url_for('medication'))

@app.route('/prescriptions')
def prescriptions_alias():
    return redirect(url_for('prescription'))

@app.route('/allergies')
def allergies_alias():
    return redirect(url_for('patient_allergy'))

@app.route('/reports/conflicts')
def reports_conflicts_alias():
    return redirect(url_for('allergy_conflict'))





if __name__ == "__main__":
	import click


	@click.command()
	@click.option('--debug', is_flag=True)
	@click.option('--threaded', is_flag=True)
	@click.argument('HOST', default='0.0.0.0')
	@click.argument('PORT', default=8111, type=int)
	def run(debug, threaded, host, port):
		"""
		This function handles command line parameters.
		Run the server using:

			python server.py

		Show the help text using:

			python server.py --help

		"""

		HOST, PORT = host, port
		print("running on %s:%d" % (HOST, PORT))
		app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)

run()
