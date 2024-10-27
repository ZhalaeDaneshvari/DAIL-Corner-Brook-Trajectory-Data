# DAIL-Corner-Brook-Data
Created by Zhalae Daneshvari 
### A data processing script for the Corner Brook study that creates a master file containing cleaned and interpolated trajectory data from all participants across all tasks.

## Overview
This script processes raw participant data files and creates a consolidated master file with interpolated trajectory data. It handles both standard and randomized tasks, applies proper task mapping according to the randomization sequence, and generates detailed validation reports.
Features

## Data Interpolation
- Performs linear interpolation at 2Hz frequency
-Processes trajectory data between task markers ("TaskX Start" and "TaskX End")
- Maintains all original data columns (Time, Unix, Floor, Marker, X, Y)

## Task Processing
- Processes tasks 1-8 with their original numeric identifiers
- Maps randomized tasks 9-12 according to the randomization sequence:
 - 4B-R (4210)
 - 4A-L (4115)
 - A-R (5119)
 - 5B-L (5214)

## Data Consolidation
- Creates a master file containing data from all participants
- Includes participant IDs and all trajectory data
- Maintains proper task ordering (1-8 followed by mapped 9-12)

## Validation and Error Handling
- Processes all available data even when some tasks have issues
- Generates detailed problem summary report
- Tracks missing or problematic data points


## File Structure
data folder - Raw participant data files (R1.csv to R72.csv)

interpolated_data - Output directory for processed data

randomization sequence.csv - Task mapping for randomized tasks

task_interpolation.py - Main processing script

problem_summary.txt - Generated validation report

## Notes
- Task numbers 1-8 remain numeric
- Tasks 9-12 are mapped according to the randomization sequence
- Interpolation occurs at 2Hz (one point every 0.5 seconds)
- All valid data points are included in the final output, even for participants with partial data



