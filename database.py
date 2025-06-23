import sqlite3

DB_PATH = "ikebana.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()

    cur.executescript("""
    DROP TABLE IF EXISTS pointclouds;
    DROP TABLE IF EXISTS color_features;
    DROP TABLE IF EXISTS spatial_features;
    DROP TABLE IF EXISTS branches;
    DROP TABLE IF EXISTS arrangements;

    CREATE TABLE arrangements (
      id           INTEGER PRIMARY KEY AUTOINCREMENT,
      artist       TEXT    NOT NULL,
      comment      TEXT,
      vase_width   REAL,
      vase_height  REAL,
      created_at   DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE branches (
      arr_id    INTEGER NOT NULL,
      role      TEXT    NOT NULL,
      length    REAL    NOT NULL,
      azimuth   REAL    NOT NULL,
      elevation REAL    NOT NULL,
      FOREIGN KEY(arr_id) REFERENCES arrangements(id)
    );

    CREATE TABLE spatial_features (
      arr_id        INTEGER PRIMARY KEY,
      centroid_x    REAL,
      centroid_y    REAL,
      balance_score REAL,
      FOREIGN KEY(arr_id) REFERENCES arrangements(id)
    );

    CREATE TABLE color_features (
      arr_id INTEGER PRIMARY KEY,
      avg_r  REAL,
      avg_g  REAL,
      avg_b  REAL,
      FOREIGN KEY(arr_id) REFERENCES arrangements(id)
    );

    CREATE TABLE pointclouds (
      arr_id         INTEGER PRIMARY KEY,
      file_path      TEXT    NOT NULL,
      num_points     INTEGER,
      centroid_x     REAL,
      centroid_y     REAL,
      centroid_z     REAL,
      bbox_x         REAL,
      bbox_y         REAL,
      bbox_z         REAL,
      hull_volume    REAL,
      hull_area      REAL,
      avg_normal_x   REAL,
      avg_normal_y   REAL,
      avg_normal_z   REAL,
      curvature_mean REAL,
      curvature_std  REAL,
      FOREIGN KEY(arr_id) REFERENCES arrangements(id)
    );
    """)

    conn.commit()
    conn.close()


def get_conn():
    """データベース接続を返す"""
    return sqlite3.connect(DB_PATH)


def save_arrangement_metadata(conn, artist, comment, vase_width=None, vase_height=None):
    """
    arrangements テーブルにレコードを挿入し、arr_id を返却する
    - artist: 作成者名
    - comment: コメント
    - vase_width: 使用した花器の幅
    - vase_height: 使用した花器の高さ
    """
    cur = conn.cursor()
    cur.execute(
      "INSERT INTO arrangements(artist, comment, vase_width, vase_height) VALUES (?, ?, ?, ?)",
      (artist, comment, vase_width, vase_height)
    )
    return cur.lastrowid


def save_branch(conn, arr_id, role, length, az, el):
    """
    branches テーブルに枝情報を追加する
    - arr_id: arrangements.id
    - role: "main"/"guest"/"middle1"/"middle2" 等
    - length: 枝の長さ
    - az: 水平角度
    - el: 垂直角度
    """
    conn.execute(
      "INSERT INTO branches(arr_id, role, length, azimuth, elevation) VALUES (?, ?, ?, ?, ?)",
      (arr_id, role, length, az, el)
    )
    conn.commit()
