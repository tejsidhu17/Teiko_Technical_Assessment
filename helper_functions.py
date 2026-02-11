import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

DB_PATH = "cell_counts.db"
CSV_PATH = "cell-count.csv"

def calculate_cell_frequencies():
    """Calculate the relative frequency of each cell type in each sample."""
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT 
            samples.sample_id AS sample,
            SUM(cell_counts.cell_count) OVER (PARTITION BY samples.sample_id) AS total_count,
            cell_types.name AS population,
            cell_counts.cell_count AS count,
            ROUND(100.0 * cell_counts.cell_count / SUM(cell_counts.cell_count) OVER (PARTITION BY samples.sample_id), 2) AS percentage
        FROM cell_counts
        JOIN samples ON cell_counts.sample_id = samples.sample_id
        JOIN cell_types ON cell_counts.cell_type_id = cell_types.cell_type_id
        ORDER BY samples.sample_id, cell_types.name;
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    return df

def calculate_cell_frequencies_pandas():
    """Calculate the relative frequency of each cell type in each sample using pandas."""
    df = pd.read_csv(CSV_PATH)
    
    # Define the cell type columns
    cell_type_cols = ["b_cell", "cd8_t_cell", "cd4_t_cell", "nk_cell", "monocyte"]
    
    # Melt the dataframe to convert cell types from columns to rows
    df_melted = df.melt(
        id_vars=["sample"],
        value_vars=cell_type_cols,
        var_name="population",
        value_name="count"
    )
    
    # Calculate total count per sample
    total_counts = df_melted.groupby("sample")["count"].transform("sum")
    df_melted["total_count"] = total_counts
    
    # Calculate percentage
    df_melted["percentage"] = round(100.0 * df_melted["count"] / df_melted["total_count"], 2)
    
    # Reorder columns to match the required format
    result = df_melted[["sample", "total_count", "population", "count", "percentage"]]
    
    # Sort by sample and population for consistency
    result = result.sort_values(["sample", "population"]).reset_index(drop=True)
    
    return result

def bcell_average_in_melanoma_male_responders():
    """Calculate average B cell count for Melanoma male responders at time=0."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    query = """
    SELECT 
        ROUND(AVG(cell_counts.cell_count), 2) AS average_b_cells
    FROM cell_counts
    JOIN samples ON cell_counts.sample_id = samples.sample_id
    JOIN subjects ON samples.subject_id = subjects.subject_id
    JOIN cell_types ON cell_counts.cell_type_id = cell_types.cell_type_id
    WHERE subjects.condition = 'melanoma'
        AND subjects.sex = 'M'
        AND subjects.response = 'yes'
        AND samples.time_from_treatment_start = 0
        AND cell_types.name = 'b_cell';
    """
    
    cur.execute(query)
    result = cur.fetchone()[0]
    conn.close()
    
    print(f"Average B cells for Melanoma male responders at time=0: {result}")
    return result


def analyze_miraclib_response():
    """
    Compare cell population frequencies between responders and non-responders
    for Melanoma patients receiving miraclib treatment (PBMC samples only).
    """
    conn = sqlite3.connect(DB_PATH)
    
    # Get the frequency data for Melanoma patients on miraclib with PBMC samples
    query = """
    SELECT 
        subjects.response,
        cell_types.name AS cell_type_name,
        ROUND(100.0 * cell_counts.cell_count / 
              SUM(cell_counts.cell_count) OVER (PARTITION BY samples.sample_id), 2) AS percentage
    FROM cell_counts
    JOIN samples ON cell_counts.sample_id = samples.sample_id
    JOIN subjects ON samples.subject_id = subjects.subject_id
    JOIN cell_types ON cell_counts.cell_type_id = cell_types.cell_type_id
    WHERE subjects.condition = 'melanoma'
        AND subjects.treatment = 'miraclib'
        AND samples.sample_type = 'PBMC';
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    # Separate responders and non-responders
    responders = df[df['response'] == 'yes']
    non_responders = df[df['response'] == 'no']
    
    # Get unique cell type names
    cell_type_names = df['cell_type_name'].unique()
    
    # Statistical testing
    print("=" * 80)
    print("STATISTICAL ANALYSIS: Melanoma Patients on Miraclib (PBMC Samples)")
    print("Comparing Cell Population Frequencies: Responders vs Non-Responders")
    print("=" * 80)
    
    results = []
    for cell_type in cell_type_names:
        resp_data = responders[responders['cell_type_name'] == cell_type]['percentage']
        non_resp_data = non_responders[non_responders['cell_type_name'] == cell_type]['percentage']
        
        # Perform Mann-Whitney U test (non-parametric alternative to t-test)
        statistic, p_value = stats.mannwhitneyu(resp_data, non_resp_data, alternative='two-sided')
        
        # Calculate means and medians
        resp_mean = resp_data.mean()
        resp_median = resp_data.median()
        non_resp_mean = non_resp_data.mean()
        non_resp_median = non_resp_data.median()
        
        results.append({
            'cell_type_name': cell_type,
            'responders_mean': resp_mean,
            'responders_median': resp_median,
            'non_responders_mean': non_resp_mean,
            'non_responders_median': non_resp_median,
            'difference_in_means': resp_mean - non_resp_mean,
            'p_value': p_value,
            'significant': 'Yes' if p_value < 0.05 else 'No'
        })
        
        print(f"{cell_type}:")
        print(f"  Responders:     Mean = {resp_mean:.2f}%, Median = {resp_median:.2f}%")
        print(f"  Non-Responders: Mean = {non_resp_mean:.2f}%, Median = {non_resp_median:.2f}%")
        print(f"  Difference:     {resp_mean - non_resp_mean:.2f}%")
        print(f"  p-value:        {p_value:.4f} {'***' if p_value < 0.001 else '**' if p_value < 0.01 else '*' if p_value < 0.05 else 'ns'}")
        print()
    
    # Create summary dataframe
    results_df = pd.DataFrame(results)
    
    print("\nSIGNIFICANT POPULATIONS (p < 0.05):")
    print("=" * 80)
    significant = results_df[results_df['significant'] == 'Yes']
    if len(significant) > 0:
        for _, row in significant.iterrows():
            direction = "higher" if row['difference_in_means'] > 0 else "lower"
            print(f"• {row['cell_type_name']}: Responders have {direction} frequencies (p = {row['p_value']:.4f})")
    else:
        print("No significant differences found at p < 0.05 threshold.")
    print()

    # Create boxplot visualization with separate subplots
    fig, axes = plt.subplots(1, len(cell_type_names), figsize=(15, 5))

    # Prepare data for boxplot
    df['group'] = df['response'].map({'yes': 'Responders', 'no': 'Non-Responders'})

    # Create a subplot for each cell type
    for i, cell_type in enumerate(cell_type_names):
        cell_data = df[df['cell_type_name'] == cell_type]
        
        sns.boxplot(data=cell_data, x='group', y='percentage', ax=axes[i], hue='group', palette='deep')
        axes[i].set_title(f'{cell_type}', fontweight='bold')
        axes[i].set_xlabel('')
        axes[i].set_ylabel('Relative Frequency (%)' if i == 0 else '')
        axes[i].tick_params(axis='x', rotation=45)
        
        # Add significance marker if p < 0.05
        result = results_df[results_df['cell_type_name'] == cell_type].iloc[0]
        if result['p_value'] < 0.05:
            y_max = cell_data['percentage'].max()
            axes[i].text(0.5, y_max * 1.15, '*', 
                        ha='center', fontsize=20, fontweight='bold', 
                        transform=axes[i].transData)

    plt.suptitle('Cell Population Frequencies: Responders vs Non-Responders\n(Melanoma Patients on Miraclib, PBMC Samples)', 
                fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()

    plt.savefig('miraclib_response_analysis.png', dpi=300, bbox_inches='tight')
    print(f"Boxplot saved as 'miraclib_response_analysis.png'")

    # Save statistical results
    results_df.to_csv('miraclib_statistical_results.csv', index=False)
    print(f"Statistical results saved as 'miraclib_statistical_results.csv'")

    plt.show()

    return results_df

def explore_baseline_miraclib_samples():
    """
    Explore melanoma PBMC samples at baseline (time=0) for patients treated with miraclib.
    Provides breakdown by project, response, and sex.
    """
    conn = sqlite3.connect(DB_PATH)
    
    print("=" * 80)
    print("BASELINE ANALYSIS: Melanoma PBMC Samples (time=0) with Miraclib Treatment")
    print("=" * 80)
    print()
    
    # Query 1: Get all melanoma PBMC samples at baseline from miraclib patients
    baseline_query = """
    SELECT 
        samples.sample_id,
        samples.subject_id,
        subjects.project_id,
        projects.name AS project_name,
        subjects.response,
        subjects.sex
    FROM samples
    JOIN subjects ON samples.subject_id = subjects.subject_id
    JOIN projects ON subjects.project_id = projects.project_id
    WHERE subjects.condition = 'melanoma'
        AND subjects.treatment = 'miraclib'
        AND samples.sample_type = 'PBMC'
        AND samples.time_from_treatment_start = 0;
    """
    
    df = pd.read_sql_query(baseline_query, conn)
    
    print(f"Total baseline samples found: {len(df)}")
    print()
    
    # Query 2a: Samples per project
    print("1. SAMPLES PER PROJECT:")
    print("-" * 40)
    samples_by_project = df.groupby('project_name').size().reset_index(name='sample_count')
    for _, row in samples_by_project.iterrows():
        print(f"   {row['project_name']}: {row['sample_count']} samples")
    print()
    
    # Query 2b: Subjects by response status
    print("2. SUBJECTS BY RESPONSE STATUS:")
    print("-" * 40)
    subjects_by_response = df.groupby('response')['subject_id'].nunique().reset_index(name='subject_count')
    subjects_by_response['response'] = subjects_by_response['response'].map({
        'yes': 'Responders',
        'no': 'Non-Responders'
    })
    for _, row in subjects_by_response.iterrows():
        print(f"   {row['response']}: {row['subject_count']} subjects")
    
    total_subjects = df['subject_id'].nunique()
    responders = df[df['response'] == 'yes']['subject_id'].nunique()
    non_responders = df[df['response'] == 'no']['subject_id'].nunique()
    print(f"   Total: {total_subjects} subjects")
    print()
    
    # Query 2c: Subjects by sex
    print("3. SUBJECTS BY SEX:")
    print("-" * 40)
    subjects_by_sex = df.groupby('sex')['subject_id'].nunique().reset_index(name='subject_count')
    subjects_by_sex['sex'] = subjects_by_sex['sex'].map({
        'M': 'Males',
        'F': 'Females'
    })
    for _, row in subjects_by_sex.iterrows():
        print(f"   {row['sex']}: {row['subject_count']} subjects")
    print()
    
    # Additional breakdown: Response by sex
    print("4. RESPONSE BY SEX (CROSS-TABULATION):")
    print("-" * 40)
    crosstab = pd.crosstab(
        df.drop_duplicates('subject_id')['sex'],
        df.drop_duplicates('subject_id')['response'],
        margins=True
    )
    crosstab.index = crosstab.index.map({'M': 'Males', 'F': 'Females', 'All': 'Total'})
    crosstab.columns = crosstab.columns.map({'yes': 'Responders', 'no': 'Non-Responders', 'All': 'Total'})
    print(crosstab)
    print()
    
    conn.close()
    
    # Save summary
    summary = {
        'total_samples': len(df),
        'total_subjects': df['subject_id'].nunique(),
        'samples_by_project': samples_by_project.to_dict('records'),
        'responders': responders,
        'non_responders': non_responders,
        'males': df[df['sex'] == 'M']['subject_id'].nunique(),
        'females': df[df['sex'] == 'F']['subject_id'].nunique()
    }
    
    return df, summary