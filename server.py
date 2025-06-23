from flask import Flask, jsonify, send_from_directory, request
import os
import traceback
from app import run_ikebana_qa_3d
from app_extend import run_ikebana_extend_optimization
import database
import feature_utils

app = Flask(__name__, static_folder="static")
database.init_db()


# Return the start page
@app.route("/")
def start():
    return send_from_directory(app.static_folder, "start.html")


# Return the 3D viewer
@app.route("/viewer")
def viewer():
    return send_from_directory(app.static_folder, "index.html")


# Run optimization & save metadata
@app.route("/optimize")
def optimize():
    print(">>> [optimize] HIT", flush=True)
    print(f">>> using DB at {database.DB_PATH}", flush=True)
    try:
        # 1) Get vase type from request → set W, H
        vase = request.args.get("vase", default="", type=str)
        if vase == "筒型花器":
            W, H = 10, 20
        elif vase == "皿型花器":
            W, H = 10, 15
        else:
            W, H = 10, 15

        # 2) Define fixed data (candidate flower lengths)
        flower_lengths = {
            "桜": 0.4,
            "リアトリス": 0.4,
            "ディル": 0.4,
            "モルセラ": 0.25,
            "バラ": 0.25,
            "牡丹": 0.25,
            "ユリ": 0.25,
        }
        candidate_lengths = {
            "桜": [60, 50, 30],
            "リアトリス": [60, 50, 30],
            "ディル": [60, 50, 30],
            "モルセラ": [60, 50, 30],
            "バラ": [23, 20, 15],
            "牡丹": [23, 17, 15],
            "ユリ": [23, 17, 15],
        }

        # 3) Run optimization
        forced = request.args.get("forced_flower", default="", type=str)

        result = run_ikebana_qa_3d(
            W,
            H,
            flower_lengths,
            candidate_lengths,
            forced_flower=forced,
            front_azimuth=0,
            front_elevation=0,
        )

        # 4) Save arrangements and branches to the database
        conn = database.get_conn()
        arr_id = database.save_arrangement_metadata(
            conn, artist="unknown", comment="", vase_width=W, vase_height=H
        )
        branch_map = {
            "main": (
                result["mainLen"],
                result["mainAzimuth"],
                result["mainElevation"],
            ),
            "guest": (
                result["guestLen"],
                result["guestAzimuth"],
                result["guestElevation"],
            ),
            "middle1": (
                result["middle1Len"],
                result["middle1Azimuth"],
                result["middle1Elevation"],
            ),
            "middle2": (
                result["middle2Len"],
                result["middle2Azimuth"],
                result["middle2Elevation"],
            ),
        }
        for role, params in branch_map.items():
            database.save_branch(conn, arr_id, role, *params)
        conn.commit()
        conn.close()
        # 5) Attach arr_id to the result and return it
        result["arr_id"] = arr_id
        return jsonify(result)

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# Optimize and save additional branches
@app.route("/optimize_extend", methods=["POST"])
def optimize_extend():
    data = request.get_json()
    base_assignments = data["base_assignments"]
    base_lengths = data["base_lengths"]
    base_angles = data["base_angles"]
    ext = run_ikebana_extend_optimization(
        base_assignments,
        base_lengths,
        base_angles)
    conn = database.get_conn()
    for role in ("middle3", "middle4"):
        database.save_branch(
            conn,
            data["arr_id"],
            role,
            ext["lengths"][role],
            ext["angles"][f"{role}Azimuth"],
            ext["angles"][f"{role}Elevation"],
        )
    conn.commit()
    conn.close()
    return jsonify(ext)


# Receive point cloud data & extract/save features
@app.route("/upload_pointcloud", methods=["POST"])
def upload_pointcloud():
    arr_id = request.args.get("arr_id", type=int)
    if not arr_id:
        return jsonify({"error": "missing arr_id"}), 400

    os.makedirs("pcds", exist_ok=True)
    file_path = f"pcds/{arr_id}.ply"
    data = request.get_data()
    with open(file_path, "wb") as f:
        f.write(data)
    print(f"[DEBUG] Saved PLY for arr_id={arr_id}, bytes={len(data)}")

    conn = database.get_conn()
    try:
        feats = feature_utils.extract_pointcloud_features(file_path)
        conn.execute(
            """
          INSERT OR REPLACE INTO pointclouds (
            arr_id, file_path, num_points,
            centroid_x, centroid_y, centroid_z,
            bbox_x, bbox_y, bbox_z,
            hull_volume, hull_area,
            avg_normal_x, avg_normal_y, avg_normal_z,
            curvature_mean, curvature_std
          ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
            (
                arr_id,
                file_path,
                feats["num_points"],
                *feats["centroid"],
                *feats["bbox"],
                feats["hull_volume"],
                feats["hull_area"],
                *feats["avg_normal"],
                feats["curvature_mean"],
                feats["curvature_std"],
            ),
        )
    except Exception as e:
        print(f"[WARN] extract failed for arr_id={arr_id}: {e}")
        conn.execute(
            "INSERT OR REPLACE INTO pointclouds(arr_id, file_path) VALUES (?,?)",
            (arr_id, file_path),
        )
    finally:
        conn.commit()
        count = conn.execute("SELECT count(*) FROM pointclouds").fetchone()[0]
        print(f"[DEBUG] pointclouds rows after commit: {count}")
        conn.close()

    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(debug=True)
