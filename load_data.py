import pandas as pd
import sqlite3

CSV_PATH = "cell-count.csv"
DB_PATH = "cell_counts.db"

def create_schema():
    conn = sqlite3.connect("cell_counts.db")
    cur = conn.cursor()

    # Enforce foreign keys
    cur.execute("PRAGMA foreign_keys = ON;")

    cur.executescript("""
    CREATE TABLE IF NOT EXISTS projects (
        project_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    );

    CREATE TABLE IF NOT EXISTS subjects (
        subject_id TEXT PRIMARY KEY,
        project_id INTEGER NOT NULL,
        condition TEXT,
        age INTEGER,
        sex TEXT,
        treatment TEXT,
        response TEXT,
        FOREIGN KEY (project_id) REFERENCES projects(project_id)
    );

    CREATE TABLE IF NOT EXISTS samples (
        sample_id TEXT PRIMARY KEY,
        subject_id TEXT NOT NULL,
        sample_type TEXT,
        time_from_treatment_start REAL,
        FOREIGN KEY (subject_id) REFERENCES subjects(subject_id)
    );

    CREATE TABLE IF NOT EXISTS cell_types (
        cell_type_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    );

    CREATE TABLE IF NOT EXISTS cell_counts (
        sample_id TEXT NOT NULL,
        cell_type_id INTEGER NOT NULL,
        cell_count INTEGER NOT NULL,
        PRIMARY KEY (sample_id, cell_type_id),
        FOREIGN KEY (sample_id) REFERENCES samples(sample_id),
        FOREIGN KEY (cell_type_id) REFERENCES cell_types(cell_type_id)
    );
    """)

    conn.commit()
    conn.close()
    print("Database schema created successfully")

def load_data():
    df = pd.read_csv(CSV_PATH)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys = ON;")

    # Insert data into Projects Table:
    projects = df["project"].dropna().unique()
    for p in projects:
        cur.execute(
            "INSERT OR IGNORE INTO projects (name) VALUES (?)", (p,)
        )
    project_map = dict(cur.execute("SELECT name, project_id FROM projects").fetchall())

    # Insert data into Subjects Table:
    subject_cols = [
        "project",
        "subject",
        "condition",
        "age",
        "sex",
        "treatment",
        "response"
    ]

    subjects = (
        df[subject_cols]
        .drop_duplicates("subject")
    )

    for _, row in subjects.iterrows():
        cur.execute("""
            INSERT OR IGNORE INTO subjects
            (subject_id, project_id, condition, age, sex, treatment, response)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            row["subject"],
            project_map[row["project"]],
            row["condition"],
            row["age"],
            row["sex"],
            row["treatment"],
            row["response"]
        ))

    # Insert data into Samples Table:
    sample_cols = [
        "sample",
        "subject",
        "sample_type",
        "time_from_treatment_start"
    ]

    samples = (
        df[sample_cols]
        .drop_duplicates("sample")
    )

    for _, row in samples.iterrows():
        cur.execute("""
            INSERT OR IGNORE INTO samples
            (sample_id, subject_id, sample_type, time_from_treatment_start)
            VALUES (?, ?, ?, ?)
        """, (
            row["sample"],
            row["subject"],
            row["sample_type"],
            row["time_from_treatment_start"]
        ))


    # Insert data into Cell Types Table:
    cell_type_cols = [
        "b_cell",
        "cd8_t_cell",
        "cd4_t_cell",
        "nk_cell",
        "monocyte"
    ]

    for cell_type in cell_type_cols:
        cur.execute(
            "INSERT OR IGNORE INTO cell_types (name) VALUES (?)",
            (cell_type,)
        )

    cell_type_map = dict(
        cur.execute("SELECT name, cell_type_id FROM cell_types").fetchall()
    )

    # Insert data into Cell Counts Table:
    for _, row in df.iterrows():
        for cell_type in cell_type_cols:
            cur.execute("""
                INSERT INTO cell_counts
                (sample_id, cell_type_id, cell_count)
                VALUES (?, ?, ?)
            """, (
                row["sample"],
                cell_type_map[cell_type],
                row[cell_type]
            ))

    conn.commit()
    conn.close()
    print("Data loaded successfully")

def main():
    print("Creating database schema...")
    create_schema()
    
    print("Loading data...")
    load_data()

if __name__ == "__main__":
    main()
