import pandas as pd
import numpy as np
from datetime import datetime
import glob
import os

def validate_participant_data(df, participant_id, task_mapping):
    """
    Validates and reports detailed information about a participant's data
    Returns a dictionary of issues found
    """
    issues = []
    
    # Check all expected task markers
    for task_num in range(1, 13):
        start_marker = f'Task{task_num} Start'
        end_marker = f'Task{task_num} End'
        
        # Check start marker
        start_exists = start_marker in df['Marker'].values
        if not start_exists:
            issues.append(f"Missing {start_marker}")
        
        # Check end marker
        end_exists = end_marker in df['Marker'].values
        if not end_exists:
            issues.append(f"Missing {end_marker}")
        
        # If both markers exist, check points between them
        if start_exists and end_exists:
            start_idx = df.index[df['Marker'] == start_marker][0]
            end_idx = df.index[df['Marker'] == end_marker][0]
            points = df.loc[start_idx:end_idx]
            point_count = len(points[points['Marker'] == 'Point'])
            if point_count < 2:
                issues.append(f"Task {task_num}: Insufficient points (found {point_count})")
    
    return issues

def custom_sort_tasks(task):
    """
    Custom sorting function for tasks:
    1-8 sort numerically first
    9-12 maintain their coded position after tasks 1-8
    """
    if str(task).isdigit():
        return int(task)  # Tasks 1-8 will come first
    else:
        # For coded tasks (9-12), add 9 to ensure they come after numeric tasks
        if "(4115)" in str(task):  # 4A-L maps to task 10
            return 10
        elif "(4210)" in str(task):  # 4B-R maps to task 9
            return 9
        elif "(5119)" in str(task):  # 5A-R maps to task 11
            return 11
        elif "(5214)" in str(task):  # 5B-L maps to task 12
            return 12
        return 999  # Fallback for unexpected values

def create_task_mapping():
    """
    Creates a mapping for each participant's specific task sequence based on randomization file.
    """
    try:
        randomization_df = pd.read_csv('randomization sequence.csv')
        mapping = {}
        
        for _, row in randomization_df.iterrows():
            participant = str(int(row['Participant_ID']))
            mapping[participant] = {
                '9': row['T9'],
                '10': row['T10'],
                '11': row['T11'],
                '12': row['T12']
            }
        return mapping
    except Exception as e:
        print(f"Error creating task mapping: {str(e)}")
        return None

def get_mapped_task_code(participant_id, original_task, task_mapping):
    """
    Maps a task number to the correct code for this specific participant.
    """
    try:
        task_str = str(original_task)
        if task_str in ['9', '10', '11', '12']:
            if participant_id in task_mapping and task_str in task_mapping[participant_id]:
                mapped_code = task_mapping[participant_id][task_str]
                return mapped_code
        return str(original_task)
    except Exception as e:
        print(f"Error mapping task {original_task} for participant {participant_id}: {str(e)}")
        return str(original_task)

def load_participant_data(file_path):
    """
    Load and preprocess a single participant's CSV file.
    """
    try:
        df = pd.read_csv(file_path)
        df['Unix'] = pd.to_numeric(df['Unix'])
        df['X'] = pd.to_numeric(df['X'])
        df['Y'] = pd.to_numeric(df['Y'])
        return df
    except Exception as e:
        print(f"Error loading {file_path}: {str(e)}")
        return None

def get_task_points(df, task_number):
    """
    Extract points for a specific task between task markers.
    """
    try:
        start_marker = f'Task{task_number} Start'
        end_marker = f'Task{task_number} End'
        
        if start_marker not in df['Marker'].values:
            return None
            
        if end_marker not in df['Marker'].values:
            return None
            
        start_idx = df.index[df['Marker'] == start_marker][0]
        end_idx = df.index[df['Marker'] == end_marker][0]
        
        task_data = df.loc[start_idx:end_idx]
        points = task_data[task_data['Marker'] == 'Point'].copy()
        
        if len(points) < 2:
            return None
            
        return points
        
    except IndexError:
        return None

def create_interpolated_points(points_df, freq_hz=2):
    """
    Create interpolated points at specified frequency.
    """
    try:
        if points_df is None or len(points_df) < 2:
            return None
            
        # Get time range
        start_time = points_df['Unix'].min()
        end_time = points_df['Unix'].max()
        
        # Create evenly spaced timestamps
        step = 1.0 / freq_hz
        new_times = np.arange(start_time, end_time + step, step)
        
        # Interpolate X and Y coordinates
        x_interp = np.interp(new_times, points_df['Unix'], points_df['X'])
        y_interp = np.interp(new_times, points_df['Unix'], points_df['Y'])
        
        # Interpolate Floor values
        floor_interp = np.interp(new_times, points_df['Unix'], points_df['Floor'])
        floor_interp = np.round(floor_interp).astype(int)
        
        # Create result dataframe
        result = pd.DataFrame({
            'Unix': new_times,
            'X': x_interp,
            'Y': y_interp,
            'Floor': floor_interp
        })
        
        result['Time'] = pd.to_datetime(result['Unix'], unit='s')
        result['Marker'] = 'Point'
        
        # Reorder columns to match original
        result = result[['Time', 'Unix', 'Floor', 'Marker', 'X', 'Y']]
        
        return result
        
    except Exception as e:
        return None

def generate_problem_summary(data_dir, master_df, task_mapping, participant_issues):
    """
    Generates a detailed summary of problems found in the datasets
    """
    summary = []
    summary.append("="*80)
    summary.append("PROBLEM SUMMARY REPORT")
    summary.append("="*80)
    
    # Missing Files
    missing_files = []
    for i in range(1, 73):
        file_path = os.path.join(data_dir, f'R{i}.csv')
        if not os.path.exists(file_path):
            missing_files.append(f'R{i}.csv')
    
    summary.append("\n1. MISSING FILES:")
    if missing_files:
        for file in sorted(missing_files):
            summary.append(f"   - {file}")
    else:
        summary.append("   No missing files")
    
    # Problems by Participant
    summary.append("\n2. PARTICIPANTS WITH ISSUES:")
    for participant_id, issues in participant_issues.items():
        summary.append(f"\nParticipant {participant_id}:")
        # Load raw data info
        file_path = os.path.join(data_dir, f'R{participant_id}.csv')
        try:
            df = pd.read_csv(file_path)
            summary.append(f"   - File loaded successfully")
            summary.append(f"   - Total rows in file: {len(df)}")
            summary.append("   - Markers found in data:")
            for marker in sorted(df['Marker'].unique()):
                summary.append(f"     * {marker}")
        except:
            summary.append("   - Could not load file for marker analysis")
        
        # List issues
        if issues:
            for issue in issues:
                summary.append(f"   - {issue}")
        
        # Show task mapping
        if str(participant_id) in task_mapping:
            summary.append("   - Expected tasks 9-12:")
            summary.append(f"     * Task 9: {task_mapping[str(participant_id)]['9']}")
            summary.append(f"     * Task 10: {task_mapping[str(participant_id)]['10']}")
            summary.append(f"     * Task 11: {task_mapping[str(participant_id)]['11']}")
            summary.append(f"     * Task 12: {task_mapping[str(participant_id)]['12']}")
        
        # Show what made it to final output
        if master_df is not None:
            participant_data = master_df[master_df['Participant'] == int(participant_id)]
            if len(participant_data) == 0:
                summary.append("   - No data in final output")
            else:
                tasks = sorted(participant_data['Task'].unique(), key=custom_sort_tasks)
                summary.append(f"   - Tasks in final output: {tasks}")
    
    # Write summary to file
    summary_path = os.path.join(os.path.dirname(data_dir), 'problem_summary.txt')
    with open(summary_path, 'w') as f:
        f.write('\n'.join(summary))
    
    return summary_path

def process_all_participants(data_dir):
    """
    Process all participants and create master dataframe with correct task mappings.
    """
    print(f"Processing files from: {data_dir}")
    
    task_mapping = create_task_mapping()
    if task_mapping is None:
        print("Failed to create task mapping. Exiting.")
        return None, {}
    
    csv_files = sorted(glob.glob(os.path.join(data_dir, 'R*.csv')), 
                      key=lambda x: int(os.path.basename(x).replace('R', '').replace('.csv', '')))
    
    all_data = []
    participant_issues = {}
    
    for file_path in csv_files:
        participant_id = str(int(os.path.basename(file_path).replace('R', '').replace('.csv', '')))
        print(f"\nProcessing Participant {participant_id}")
        
        df = load_participant_data(file_path)
        if df is None:
            participant_issues[participant_id] = ["Failed to load data file"]
            continue
        
        # Track issues for this participant
        issues = []
        
        participant_data = []
        processed_tasks = set()
        
        # Process tasks 1-8 first
        for task_num in range(1, 9):
            task_points = get_task_points(df, task_num)
            if task_points is None:
                issues.append(f"Task {task_num}: No valid points found")
                continue
            
            interpolated = create_interpolated_points(task_points)
            if interpolated is None:
                issues.append(f"Task {task_num}: Interpolation failed")
                continue
            
            interpolated.insert(0, 'Participant', int(participant_id))
            interpolated['Task'] = str(task_num)
            processed_tasks.add(str(task_num))
            participant_data.append(interpolated)
        
        # Then process tasks 9-12 with their codes
        for task_num in range(9, 13):
            task_points = get_task_points(df, task_num)
            if task_points is None:
                issues.append(f"Task {task_num}: No valid points found")
                continue
            
            interpolated = create_interpolated_points(task_points)
            if interpolated is None:
                issues.append(f"Task {task_num}: Interpolation failed")
                continue
            
            interpolated.insert(0, 'Participant', int(participant_id))
            mapped_task = get_mapped_task_code(participant_id, task_num, task_mapping)
            interpolated['Task'] = mapped_task
            processed_tasks.add(mapped_task)
            participant_data.append(interpolated)
        
        # Store any issues found
        if issues:
            participant_issues[participant_id] = issues
        
        # Process whatever data we got, even if incomplete
        if participant_data:
            participant_df = pd.concat(participant_data, ignore_index=True)
            
            # Sort tasks within participant data
            participant_df['sort_key'] = participant_df['Task'].map(lambda x: custom_sort_tasks(x))
            participant_df = participant_df.sort_values('sort_key')
            participant_df = participant_df.drop('sort_key', axis=1)
            
            all_data.append(participant_df)
    
    if all_data:
        master_df = pd.concat(all_data, ignore_index=True)
        
        # Final sort
        master_df['sort_key'] = master_df['Task'].map(lambda x: custom_sort_tasks(x))
        master_df = master_df.sort_values(['Participant', 'sort_key'])
        master_df = master_df.drop('sort_key', axis=1)
        
        return master_df, participant_issues
    else:
        return None, participant_issues

def main():
    """Main function to run the script"""
    data_dir = './data'
    output_dir = './interpolated_data'
    
    if not os.path.exists(data_dir):
        print(f"Error: Data directory {data_dir} not found!")
        return
    
    os.makedirs(output_dir, exist_ok=True)
    
    print("Starting interpolation process...")
    
    # Process all data
    master_df, participant_issues = process_all_participants(data_dir)
    
    if master_df is not None:
        output_file = os.path.join(output_dir, 'final_interpolated_data.csv')
        master_df.to_csv(output_file, index=False)
        print(f"\nSaved final interpolated data to: {output_file}")
        
        # Generate problem summary
        task_mapping = create_task_mapping()
        summary_path = generate_problem_summary(data_dir, master_df, task_mapping, participant_issues)
        print(f"\nProblem summary written to: {summary_path}")
        
        # Print quick summary
        print(f"\nQuick Summary:")
        print(f"Total participants processed: {master_df['Participant'].nunique()}")
        print(f"Total points in dataset: {len(master_df)}")
        print(f"Participants with issues: {len(participant_issues)}")
    
    print("\nProcessing complete!")

if __name__ == "__main__":
    main()