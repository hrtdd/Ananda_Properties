from flask import Flask, render_template, request, redirect
import psycopg2
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

def get_db_connection():
    return psycopg2.connect(
        host="localhost",
        database="Tanant_Records",
        user="postgres",
        password="Hanuman123.."
    )

ALLOWED_DOC_EXTENSIONS = {"png", "jpg", "jpeg", "pdf"}

def allowed_document(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_DOC_EXTENSIONS

@app.route("/")
def home():
    return render_template("dashboard.html")

@app.route("/add-building", methods=["GET", "POST"])
def add_building():
    if request.method == "POST":
        building_name = request.form["building_name"]
        address = request.form["address"]
        total_floors = request.form["total_floors"]
        has_lift = "has_lift" in request.form
        has_parking = "has_parking" in request.form

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO buildings
            (user_id, building_name, address, total_floors, has_lift, has_parking)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (1, building_name, address, total_floors, has_lift, has_parking))

        conn.commit()
        cur.close()
        conn.close()

        return redirect("/add-building")

    return render_template("add_building.html")

@app.route("/buildings")
def view_buildings():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT 
            b.id,
            b.building_name,
            b.address,
            b.total_floors,
            CASE 
                WHEN EXISTS (
                    SELECT 1 FROM flats f
                    WHERE f.building_id = b.id AND f.is_occupied = true
                )
                THEN 'Occupied'
                ELSE 'Vacant'
            END AS status
        FROM buildings b
        ORDER BY b.id DESC
    """)

    buildings = cur.fetchall()
    cur.close()
    conn.close()

    return render_template("view_buildings.html", buildings=buildings)

@app.route("/add-flat", methods=["GET", "POST"])
def add_flat():
    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == "POST":
        building_id = request.form["building_id"]
        floor_no = request.form["floor_no"]
        flat_no = request.form["flat_no"]
        bhk = request.form["bhk"]
        area_sqft = request.form.get("area_sqft")
        rent_amount = request.form["rent_amount"]
        security_deposit = request.form.get("security_deposit")

        cur.execute("""
            INSERT INTO flats
            (building_id, floor_no, flat_no, bhk, area_sqft, rent_amount, security_deposit)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (building_id, floor_no, flat_no, bhk, area_sqft, rent_amount, security_deposit))

        conn.commit()
        cur.close()
        conn.close()

        return redirect("/add-flat")

    # GET request: load buildings for dropdown
    cur.execute("SELECT * FROM buildings ORDER BY id DESC")
    buildings = cur.fetchall()
    cur.close()
    conn.close()

    return render_template("add_flat.html", buildings=buildings)
@app.route("/flats")
def view_flats():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT b.building_name, f.floor_no, f.flat_no,
               f.bhk, f.rent_amount, f.is_occupied, f.id
        FROM flats f
        JOIN buildings b ON f.building_id = b.id
        ORDER BY b.id DESC
    """)

    flats = cur.fetchall()
    cur.close()
    conn.close()

    return render_template("view_flats.html", flats=flats)
@app.route("/add-furnishing", methods=["GET","POST"])
def add_furnishing():
    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == "POST":
        flat_id = request.form["flat_id"]
        items = request.form.getlist("items")

        for item in items:
            cur.execute(
                "INSERT INTO flat_furnishings (flat_id, item_id) VALUES (%s,%s)",
                (flat_id, item)
            )

        conn.commit()
        cur.close()
        conn.close()
        return redirect("/add-furnishing")

    cur.execute("""
        SELECT f.id, b.building_name, f.flat_no
        FROM flats f JOIN buildings b ON f.building_id=b.id
    """)
    flats = cur.fetchall()

    cur.execute("SELECT * FROM furnishing_items")
    items = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("add_furnishing.html", flats=flats, items=items)

@app.route("/edit-flat/<int:flat_id>", methods=["GET", "POST"])
def edit_flat(flat_id):
    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == "POST":
        floor_no = request.form["floor_no"]
        flat_no = request.form["flat_no"]
        bhk = request.form["bhk"]
        rent_amount = request.form["rent_amount"]
        is_occupied = request.form["is_occupied"] == "true"

        cur.execute("""
            UPDATE flats
            SET floor_no=%s,
                flat_no=%s,
                bhk=%s,
                rent_amount=%s,
                is_occupied=%s
            WHERE id=%s
        """, (floor_no, flat_no, bhk, rent_amount, is_occupied, flat_id))

        conn.commit()
        cur.close()
        conn.close()
        return redirect("/flats")

    # GET request – load flat data
    cur.execute("""
        SELECT floor_no, flat_no, bhk, rent_amount, is_occupied
        FROM flats
        WHERE id=%s
    """, (flat_id,))

    flat = cur.fetchone()
    cur.close()
    conn.close()

    return render_template("edit_flat.html", flat=flat)
@app.route("/edit-furnishing/<int:flat_id>", methods=["GET","POST"])
def edit_furnishing(flat_id):
    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == "POST":
        cur.execute("DELETE FROM flat_furnishings WHERE flat_id=%s", (flat_id,))
        items = request.form.getlist("items")

        for item in items:
            cur.execute(
                "INSERT INTO flat_furnishings (flat_id, item_id) VALUES (%s,%s)",
                (flat_id, item)
            )

        conn.commit()
        cur.close()
        conn.close()
        return redirect("/flats")

    cur.execute("SELECT * FROM furnishing_items")
    items = cur.fetchall()

    cur.execute(
        "SELECT item_id FROM flat_furnishings WHERE flat_id=%s",
        (flat_id,)
    )
    selected_items = [i[0] for i in cur.fetchall()]

    cur.close()
    conn.close()

    return render_template(
        "edit_furnishing.html",
        items=items,
        selected_items=selected_items
    )
@app.route("/move-out/<int:flat_id>")
def move_out(flat_id):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("UPDATE flats SET is_occupied=false WHERE id=%s", (flat_id,))
    conn.commit()
# ✅ Tenant History में Move-Out Date Update
    cur.execute("""
    UPDATE tenant_history
    SET move_out_date = CURRENT_DATE
    WHERE flat_id=%s AND move_out_date IS NULL
""", (flat_id,))

    cur.close()
    conn.close()
    return redirect("/flats")
@app.route("/flat-history/<int:flat_id>")
def flat_history(flat_id):
    conn = get_db_connection()
    cur = conn.cursor()

    # Flat info (flat no + building)
    cur.execute("""
        SELECT f.flat_no, b.building_name
        FROM flats f
        JOIN buildings b ON f.building_id = b.id
        WHERE f.id=%s
    """, (flat_id,))
    flat_info = cur.fetchone()

    # Tenant History records
    cur.execute("""
        SELECT 
            t.full_name,
            h.move_in_date,
            h.move_out_date,
            h.rent_at_that_time
        FROM tenant_history h
        JOIN tenants t ON h.tenant_id = t.id
        WHERE h.flat_id=%s
        ORDER BY h.move_in_date DESC
    """, (flat_id,))

    history = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "flat_history.html",
        flat_info=flat_info,
        history=history
    )

@app.route("/add-tenant", methods=["GET", "POST"])
def add_tenant():
    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == "POST":
        flat_id = request.form["flat_id"]
        full_name = request.form["full_name"]
        mobile = request.form["mobile"]
        profession = request.form["profession"]
        is_family = request.form["is_family"] == "true"

        # ✅ Tenant Insert + Due Date Auto Set
        cur.execute("""
            INSERT INTO tenants 
            (flat_id, full_name, mobile, profession, is_family, rent_due_date)
            VALUES (%s, %s, %s, %s, %s, CURRENT_DATE + INTERVAL '30 days')
        """, (flat_id, full_name, mobile, profession, is_family))

        # ✅ Tenant ID निकालो
        cur.execute("SELECT LASTVAL()")
        tenant_id = cur.fetchone()[0]

        # ✅ Flat rent निकालो
        cur.execute("SELECT rent_amount FROM flats WHERE id=%s", (flat_id,))
        rent = cur.fetchone()[0]

        # ✅ Tenant History Insert
        cur.execute("""
            INSERT INTO tenant_history (flat_id, tenant_id, rent_at_that_time)
            VALUES (%s, %s, %s)
        """, (flat_id, tenant_id, rent))

        # ✅ Flat को Occupied mark करो
        cur.execute(
            "UPDATE flats SET is_occupied = true WHERE id = %s",
            (flat_id,)
        )

        conn.commit()
        cur.close()
        conn.close()

        return redirect("/flats")

    # ✅ GET request – सिर्फ vacant flats दिखाओ
    cur.execute("""
        SELECT f.id, b.building_name, f.flat_no
        FROM flats f
        JOIN buildings b ON f.building_id = b.id
        WHERE f.is_occupied = false
    """)
    flats = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("add_tenant.html", flats=flats)

@app.route("/tenants")
def tenants():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT 
            t.id,
            t.full_name,
            t.mobile,
            t.profession,
            f.flat_no,
            b.building_name
        FROM tenants t
        JOIN flats f ON t.flat_id = f.id
        JOIN buildings b ON f.building_id = b.id
        ORDER BY t.id DESC
    """)

    tenants = cur.fetchall()
    cur.close()
    conn.close()

    return render_template("tenants.html", tenants=tenants)
@app.route("/tenant-documents", methods=["GET", "POST"])
def tenant_documents_home():
    conn = get_db_connection()
    cur = conn.cursor()

    tenants = []

    if request.method == "POST":
        search = request.form.get("search", "").strip()

        if search:
            cur.execute("""
                SELECT 
                    t.id,
                    t.full_name,
                    t.mobile,
                    f.flat_no,
                    b.building_name
                FROM tenants t
                JOIN flats f ON t.flat_id = f.id
                JOIN buildings b ON f.building_id = b.id
                WHERE LOWER(t.full_name) LIKE LOWER(%s)
            """, (f"%{search}%",))

            tenants = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "tenant_documents_home.html",
        tenants=tenants
    )

@app.route("/tenant-profile/<int:tenant_id>")
def tenant_profile(tenant_id):
    conn = get_db_connection()
    cur = conn.cursor()

    # Tenant details + photo_path
    cur.execute("""
        SELECT 
            t.full_name,
            t.mobile,
            t.profession,
            f.flat_no,
            b.building_name,
            t.photo_path
        FROM tenants t
        JOIN flats f ON t.flat_id = f.id
        JOIN buildings b ON f.building_id = b.id
        WHERE t.id = %s
    """, (tenant_id,))
    tenant = cur.fetchone()

    # Tenant documents
    cur.execute("""
    SELECT 
        dt.id,
        dt.doc_name,
        td.file_path,
        COALESCE(td.is_verified, false)
    FROM document_types dt
    LEFT JOIN tenant_documents td
        ON dt.id = td.document_type_id
        AND td.tenant_id = %s
    ORDER BY dt.id
""", (tenant_id,))
    documents = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "tenant_profile.html",
        tenant=tenant,
        documents=documents,
        tenant_id=tenant_id
    )

@app.route("/upload-tenant-photo/<int:tenant_id>", methods=["GET", "POST"])
def upload_tenant_photo(tenant_id):
    if request.method == "POST":
        photo = request.files.get("photo")
        if not photo:
            return "No photo selected", 400

        from werkzeug.utils import secure_filename
        import os

        filename = secure_filename(photo.filename)

        upload_folder = os.path.join(
            app.root_path, "static", "uploads", "tenants"
        )
        os.makedirs(upload_folder, exist_ok=True)

        file_path = f"uploads/tenants/{tenant_id}_{filename}"
        full_path = os.path.join(app.root_path, "static", file_path)

        photo.save(full_path)

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "UPDATE tenants SET photo_path=%s WHERE id=%s",
            (file_path, tenant_id)
        )
        conn.commit()
        cur.close()
        conn.close()

        return redirect("/tenant-documents")

    return render_template("upload_tenant_photo.html")
@app.route("/upload-document/<int:tenant_id>/<int:doc_type_id>", methods=["GET", "POST"])
def upload_document(tenant_id, doc_type_id):
    if request.method == "POST":
        file = request.files.get("document")

        if not file or file.filename == "":
            return "No file selected", 400

        if not allowed_document(file.filename):
            return "Only JPG, PNG or PDF allowed", 400

        filename = secure_filename(file.filename)

        # tenant-wise folder
        tenant_folder = os.path.join(
            app.root_path, "static", "uploads", "documents", f"tenant_{tenant_id}"
        )
        os.makedirs(tenant_folder, exist_ok=True)

        file_path = f"uploads/documents/tenant_{tenant_id}/{filename}"
        full_path = os.path.join(app.root_path, "static", file_path)

        file.save(full_path)

        conn = get_db_connection()
        cur = conn.cursor()

        # insert or update document
        cur.execute("""
            INSERT INTO tenant_documents (tenant_id, document_type_id, file_path, is_verified)
            VALUES (%s, %s, %s, false)
            ON CONFLICT (tenant_id, document_type_id)
            DO UPDATE SET file_path = EXCLUDED.file_path
        """, (tenant_id, doc_type_id, file_path))

        conn.commit()
        cur.close()
        conn.close()

        return redirect(f"/tenant-profile/{tenant_id}")

    # Get document type name for display
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT doc_name FROM document_types WHERE id = %s", (doc_type_id,))
    doc_type = cur.fetchone()
    cur.close()
    conn.close()

    return render_template("upload_document.html", tenant_id=tenant_id, doc_type=doc_type[0] if doc_type else "Document")

@app.route("/delete-document/<int:tenant_id>/<int:doc_id>")
def delete_document(tenant_id, doc_id):
    conn = get_db_connection()
    cur = conn.cursor()

    # file path nikaalo
    cur.execute("""
        SELECT file_path FROM tenant_documents
        WHERE tenant_id=%s AND document_type_id=%s
    """, (tenant_id, doc_id))

    row = cur.fetchone()
    if row and row[0]:
        file_full_path = os.path.join(app.root_path, "static", row[0])
        if os.path.exists(file_full_path):
            os.remove(file_full_path)

    # DB row delete
    cur.execute("""
        DELETE FROM tenant_documents
        WHERE tenant_id=%s AND document_type_id=%s
    """, (tenant_id, doc_id))

    conn.commit()
    cur.close()
    conn.close()

    return redirect(f"/tenant-profile/{tenant_id}")
@app.route("/toggle-verify/<int:tenant_id>/<int:doc_id>")
def toggle_verify(tenant_id, doc_id):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE tenant_documents
        SET is_verified = NOT is_verified
        WHERE tenant_id=%s AND document_type_id=%s
    """, (tenant_id, doc_id))

    conn.commit()
    cur.close()
    conn.close()

    return redirect(f"/tenant-profile/{tenant_id}")
@app.route("/verify-document/<int:tenant_id>/<int:doc_id>", methods=["GET", "POST"])
def verify_document(tenant_id, doc_id):
    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == "POST":
        is_verified = "is_verified" in request.form

        cur.execute("""
            UPDATE tenant_documents
            SET is_verified = %s
            WHERE tenant_id = %s AND document_type_id = %s
        """, (is_verified, tenant_id, doc_id))

        conn.commit()
        cur.close()
        conn.close()

        return redirect(f"/tenant-profile/{tenant_id}")

    # GET → document info
    cur.execute("""
        SELECT 
            dt.doc_name,
            td.file_path,
            COALESCE(td.is_verified, false)
        FROM document_types dt
        JOIN tenant_documents td
            ON dt.id = td.document_type_id
        WHERE td.tenant_id = %s AND dt.id = %s
    """, (tenant_id, doc_id))

    document = cur.fetchone()

    cur.close()
    conn.close()

    return render_template(
        "verify_document.html",
        document=document,
        tenant_id=tenant_id,
        doc_id=doc_id
    )
@app.route("/delete-tenant/<int:tenant_id>")
def delete_tenant(tenant_id):
    conn = get_db_connection()
    cur = conn.cursor()

    # 1. Tenant ka flat_id निकालो
    cur.execute("SELECT flat_id, photo_path FROM tenants WHERE id=%s", (tenant_id,))
    tenant = cur.fetchone()

    if tenant:
        flat_id = tenant[0]
        photo_path = tenant[1]

        # 2. Photo delete (अगर है)
        if photo_path:
            full_photo_path = os.path.join(app.root_path, "static", photo_path)
            if os.path.exists(full_photo_path):
                os.remove(full_photo_path)

        # 3. Tenant documents delete (files + rows)
        cur.execute("""
            SELECT file_path FROM tenant_documents
            WHERE tenant_id=%s
        """, (tenant_id,))
        docs = cur.fetchall()

        for d in docs:
            if d[0]:
                full_doc_path = os.path.join(app.root_path, "static", d[0])
                if os.path.exists(full_doc_path):
                    os.remove(full_doc_path)

        cur.execute("DELETE FROM tenant_documents WHERE tenant_id=%s", (tenant_id,))

        # 4. Tenant delete
        cur.execute("DELETE FROM tenants WHERE id=%s", (tenant_id,))

        # 5. Flat vacant
        cur.execute("UPDATE flats SET is_occupied=false WHERE id=%s", (flat_id,))

    conn.commit()
    cur.close()
    conn.close()

    return redirect("/tenants")
@app.route("/delete-building/<int:building_id>")
def delete_building(building_id):
    conn = get_db_connection()
    cur = conn.cursor()

    # 1️⃣ उस building के सारे flats निकालो
    cur.execute("SELECT id FROM flats WHERE building_id=%s", (building_id,))
    flats = cur.fetchall()

    for f in flats:
        flat_id = f[0]

        # 2️⃣ उस flat के tenants निकालो
        cur.execute("SELECT id, photo_path FROM tenants WHERE flat_id=%s", (flat_id,))
        tenants = cur.fetchall()

        for t in tenants:
            tenant_id = t[0]
            photo_path = t[1]

            # Tenant photo delete
            if photo_path:
                full_photo = os.path.join(app.root_path, "static", photo_path)
                if os.path.exists(full_photo):
                    os.remove(full_photo)

            # Tenant documents delete (files)
            cur.execute("SELECT file_path FROM tenant_documents WHERE tenant_id=%s", (tenant_id,))
            docs = cur.fetchall()

            for d in docs:
                if d[0]:
                    full_doc = os.path.join(app.root_path, "static", d[0])
                    if os.path.exists(full_doc):
                        os.remove(full_doc)

            # Tenant documents delete (rows)
            cur.execute("DELETE FROM tenant_documents WHERE tenant_id=%s", (tenant_id,))

            # Tenant history delete
            cur.execute("DELETE FROM tenant_history WHERE tenant_id=%s", (tenant_id,))

            # Tenant delete
            cur.execute("DELETE FROM tenants WHERE id=%s", (tenant_id,))

        # Flat furnishings delete
        cur.execute("DELETE FROM flat_furnishings WHERE flat_id=%s", (flat_id,))

        # Flat history delete
        cur.execute("DELETE FROM tenant_history WHERE flat_id=%s", (flat_id,))

        # Flat delete
        cur.execute("DELETE FROM flats WHERE id=%s", (flat_id,))

    # 3️⃣ अब building delete
    cur.execute("DELETE FROM buildings WHERE id=%s", (building_id,))

    conn.commit()
    cur.close()
    conn.close()

    return redirect("/buildings")
@app.route("/current-info")
def current_info():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, building_name
        FROM buildings
        ORDER BY id DESC
    """)

    buildings = cur.fetchall()
    cur.close()
    conn.close()

    return render_template("current_info.html", buildings=buildings)
@app.route("/building-info/<int:building_id>")
def building_info(building_id):
    conn = get_db_connection()
    cur = conn.cursor()

    # Building details
    cur.execute("""
        SELECT building_name, total_floors
        FROM buildings
        WHERE id=%s
    """, (building_id,))
    building = cur.fetchone()

    # Tenants list + rent info
    cur.execute("""
        SELECT 
            t.id,
            t.full_name,
            f.flat_no,
            f.rent_amount,
            t.rent_paid_months,
            t.rent_pending_amount
        FROM tenants t
        JOIN flats f ON t.flat_id = f.id
        WHERE f.building_id=%s
    """, (building_id,))

    tenants = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "building_info.html",
        building=building,
        tenants=tenants
    )
@app.route("/rent-alerts")
def rent_alerts():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT 
            t.id,
            t.full_name,
            b.building_name,
            f.flat_no,
            f.rent_amount,
            t.rent_due_date,
            (CURRENT_DATE - t.rent_due_date) AS late_days
        FROM tenants t
        JOIN flats f ON t.flat_id = f.id
        JOIN buildings b ON f.building_id = b.id
        WHERE t.rent_due_date < CURRENT_DATE
        ORDER BY late_days DESC
    """)

    overdue = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("rent_alerts.html", overdue=overdue)

if __name__ == "__main__":
    app.run(debug=True)
