# Train Schedule Analysis and Interactive Route Enquiry System

## Project Overview

This project analyzes train schedule data using Python and provides an interactive route enquiry system using Streamlit.

The project covers data review, data processing, data quality checks, analysis, visualization, and direct train route enquiry.

## Technologies Used

- Python
- Pandas
- Streamlit
- Matplotlib
- CSV Dataset

## Project Features

### 1. Basic Data Review
- Total records and attributes
- Train starting and ending stations
- Number of stops per train
- Maximum and minimum stops

### 2. Data Processing
- Standardization of arrival and departure times
- Journey duration calculation
- Route classification
- Station-wise train frequency

### 3. Data Quality
- Missing-value checking
- Duplicate checking
- Station order validation
- Distance order validation

### 4. Analysis and Visualization
- Average journey duration by route type
- High-traffic station analysis
- Data visualizations

### 5. Advanced Analysis
- Pivot tables
- Crosstab analysis
- Comparative station analysis

### 6. Interactive Train Enquiry

Users can select

- Source station
- Destination station

The application displays available direct trains along with

- Train number
- Departure time
- Arrival time
- Estimated journey duration
- Number of stops

## How to Run

Install the required packages

```bash
pip install -r requirements.txt