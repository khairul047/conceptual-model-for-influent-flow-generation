#############################################################################################################
#                                           Script Summary
#
# This script estimates daily wastewater influent flow by computing its key components:
#   - Base Wastewater Flow (BWF) 
#   - Rainfall-derived inflow (RDI) based on daily rainfall
#   - Groundwater infiltration (GWI) based on power transformed normalized WL (alpha)
#   - Rainfall-induced infiltration (RII) using an exponential decay model
#
#
#############################################################################################################

# --- Import necessary libraries ---
import os
import pandas as pd
import numpy as np
from datetime import datetime


# ----------------------------------------------------------------------------------------------------------
#                            Load Daily Rainfall and Alpha 
# ----------------------------------------------------------------------------------------------------------

# --- Set working directory to the model folder ---
os.chdir(r"Enter your path here")  # Change to your working directory

# Read daily rainfall and water level data
file_path = "./input/WRF_Rainfall_2024.csv"        # CSV file with 'Date', 'Rainfall (mm/day)', and 'alpha' columns
df = pd.read_csv(file_path, parse_dates=["Date"])  # Parse 'Date' column as datetime

# Extract weekday names from date
df["Day"] = df["Date"].dt.strftime("%a")           # e.g., 'Mon', 'Tue', etc.




# ----------------------------------------------------------------------------------------------------------
#                      Weekly Fraction Multipliers for Domestic and Industrial Use
# ----------------------------------------------------------------------------------------------------------

# Define daily adjustment factors for domestic wastewater generation
dom_weekly_fraction = {
    "Mon": 1.0,
    "Tue": 1.0,
    "Wed": 1.0,
    "Thu": 1.0,
    "Fri": 1.0,
    "Sat": 0.95,
    "Sun": 0.95
}

# Define daily adjustment factors for industrial wastewater generation
ind_weekly_fraction = {
    "Mon": 1.0,
    "Tue": 1.0,
    "Wed": 1.0,
    "Thu": 1.0,
    "Fri": 1.2,
    "Sat": 0.25,
    "Sun": 0.25
}

# Map domestic and industrial weekday multipliers
df["dom_weekly_fraction"] = df["Day"].map(dom_weekly_fraction)
df["ind_weekly_fraction"] = df["Day"].map(ind_weekly_fraction)


# ----------------------------------------------------------------------------------------------------------
#                                     Calculate Domestic Wastewater Flow
# ----------------------------------------------------------------------------------------------------------

pop = 507648          # Population in the sewershed
q = 0.31              # Daily per capita wastewater production (m3/population/day)

# Domestic flow = population * unit generation * daily fraction
df["Q_domestic"] = pop * q * df["dom_weekly_fraction"]

# ----------------------------------------------------------------------------------------------------------
#                                    Calculate Industrial Wastewater Flow
# ----------------------------------------------------------------------------------------------------------

Qind_daily = 2400     # Average daily industrial wastewater flow (m3/day)

# Industrial flow = daily industrial generation * daily fraction
df["Q_industrial"] = Qind_daily * df["ind_weekly_fraction"]

# ----------------------------------------------------------------------------------------------------------
#                             Calculate Rainfall-Derived Inflow (RDI) 
# ----------------------------------------------------------------------------------------------------------

K_RDI = 1100  # Coefficient to convert rainfall to direct inflow (m3/mm)

# RDI = coefficient * daily rainfall
df["Q_RDI"] = K_RDI * df["Rainfall (mm/day)"]

# ----------------------------------------------------------------------------------------------------------
#                        Calculate Groundwater Infiltration (GWI) 
# ----------------------------------------------------------------------------------------------------------

alpha_invert = 0.1             # Threshold value (invert level)
K_GWI = 18 * 3800              # Empirical coefficient

alpha = df['alpha']            # Read normalized groundwater level (alpha)

# GWI = K_GWI * (alpha - alpha_invert)
Q_GWI = K_GWI * (alpha - alpha_invert)

# Store in dataframe
df['Q_GWI'] = Q_GWI

# ----------------------------------------------------------------------------------------------------------
#                    Calculate Rainfall-Induced Infiltration (RII) 
# ----------------------------------------------------------------------------------------------------------

# Parameters for delayed infiltration model
kd = 0.15          # Decay constant (/day)
K_RII = 800        # Coefficient for RII

rain = df["Rainfall (mm/day)"]
n = len(rain)

# Initialize array to store delayed rainfall
delayed_rain = np.zeros(n)

# Apply exponential decay to past rainfall (slow infiltration response)
for t in range(n):
    for j in range(t + 1):
        delayed_rain[t] += rain[j] * np.exp(-kd * (t - j))

# Add delayed rainfall to dataframe
df["delayed_rain"] = delayed_rain

alpha_GL = 1.2  # Ground level threshold

# Calculate RII = K_RII * delayed_rain / (alpha_GL - alpha)
Q_RII = K_RII * delayed_rain / (alpha_GL - alpha)

# Store in dataframe
df["Q_RII"] = Q_RII

# ----------------------------------------------------------------------------------------------------------
#                          Calculate Total Influent Flow and Save to CSV
# ----------------------------------------------------------------------------------------------------------

# Total influent = sum of all flow components (m3/day)
df["Influent (m3/day)"] = df["Q_domestic"] + df["Q_industrial"] + df["Q_RDI"] + df['Q_GWI'] + df["Q_RII"]

# Convert m3/day to MGD (Million Gallons per Day)
conversion_MGD_2_m3pD = 3785.41
df["Influent (MGD)"] = df["Influent (m3/day)"] / conversion_MGD_2_m3pD

# Save final results to CSV
df.to_csv("output/Influent.csv", index=False)