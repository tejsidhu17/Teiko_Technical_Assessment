File Descriptions:

Python Files (Code predominantly written by Claude):
load_data.py - Script that creates a database schema and initializes the database with data from the provided csv file
helper_functions.py - Python File that stores all the functions that I have wrote to complete the various tasks provided in the assessment
initial_data_mining.ipynb - Python notebook that investigates certain columns and properties of the csv file to ensure that my planned database schema is valid
initial_analysis.ipynb - Python notebook that utilizes helper functions to complete all the tasks in Part 2 (Initial Analysis)
statistical_analysis.ipynb - Python notebook that utilizes helper functions to complete all the tasks in Part 3 (Statistical Analysis)
data_subset_analysis.ipynb - Python notebook that utilizes helper functions to complete all the tasks in Part 4 (Data Subset Analysis)

Data Files:
cell_counts.db - SQLite database that is used to store the provided CSV data
cell_frequencies.csv - CSV file that stores the summary table of the relative frequencies of each of the cell types for each sample
miraclib_response_analysis.png - Boxplot that compares the relative frequencies of each cell type for responders and non-responders using miraclib
miraclib_statistical_results.csv - CSV file that stores the results of the statistical testing done on the relative frequenceis of each cell type for responders and non-responders using miraclib

Code Structure:
For my code structure, I utilized a simple organization. All of the data is stored in a SQLite database. 
For all the tasks given, I created a a function stored in helper_functions.py that would query the database for any data needed, and then I would use python libraries to analyze and visualize the data as needed.
I then created seperate python notebooks for each of the tasks that were provided and called these functions from these notebooks. Depending on the format of the data, I would either leave the output within the notebook itself, or I stored in a seperate CSV or png file depending on its format.
I decided on this simple organization predominantly due to the time constraints I faced during this technical assessment. 
Due to midterms and school homework, I was only able to dedicate 4 hours to complete this assessment, hence, I decided to keep the code organization simple and easy to follow.

Database Schema and Reasoning:
Format: Table Name: Column 1, Column 2, ...
Projects Table: project_id (PK), name
Subjects Table: subject_id (PK), project_id (FK → projects), condition, age, sex, treatment, response
Samples Table: sample_id (PK), subject_id (FK → subjects), sample_type, time_from_treatment_start
Cell Types Table: cell_type_id (PK), name
Cell Counts Table: sample_id (FK → samples), cell_type_id (FK → cell_types), cell_count, PRIMARY KEY(sample_id, cell_type_id)

Reasoning:
The database schema was designed by separating the dataset into distinct biological and analytical entities rather than keeping the original flat CSV structure. The primary goal was to normalize the data, eliminate redundancy, and reflect the hierarchical structure of the study design.
At a high level, the data naturally organizes into projects, subjects, and samples. Each project represents a study. Each subject belongs to a specific project, and each subject may contribute multiple biological samples over time. These entities are therefore modeled as separate tables with foreign key relationships that reflect this hierarchy.
Separating these entities ensures that subject-level attributes such as condition, age, sex, treatment, and response are stored only once per subject instead of being repeated for every sample. Similarly, sample-specific attributes such as sample type and time from treatment start are stored at the sample level, since they may vary across different samples from the same subject.
Because the dataset includes immune cell measurements, the schema also separates cell populations from their measurements. The cell_types table stores the list of valid immune cell populations. The cell_counts table stores the measured count of each cell type for each sample. Instead of keeping cell counts in a wide format with one column per cell type, the schema stores each measurement as its own row linked to a specific sample and cell type. This design improves flexibility and prevents the need to modify the schema when new cell types are introduced.
The tables are structured to avoid redundant data and prevent unnecessary null values. Referential integrity is enforced through foreign key relationships, ensuring that subjects must belong to valid projects and samples must belong to valid subjects.
The schema is designed to be scalable and extensible. New projects, subjects, samples, or immune cell types can be added without altering the overall structure of the database. If a future study introduces additional cell populations, they can simply be inserted into the cell_types table, and their measurements recorded in the cell_counts table without requiring a redesign of the schema.
Overall, the schema focuses on breaking down the data into logical tables that allow future projects to be added without having to redesign the entire database.

