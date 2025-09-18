##############################################################################################################################################

                                                                # Script Summary:
# This script takes monthly water level data, normalizes it, applies a power transformation to amplify seasonal trends,
# and then interpolates it to a daily scale using PCHIP interpolation. The result is a physically meaningful, smoothly
# varying time series representing seasonal groundwater influence, suitable for use in hydrologic or sewer infiltration models.

##############################################################################################################################################


# Import necessary libraries 
import os
import pandas as pd
from scipy.interpolate import PchipInterpolator

# Set working directory to the folder containing the input water level file
os.chdir(r"Enter your path here")  # Change to your working directory

# Load daily Water Level (WL) data from CSV and parse 'Date' column as datetime format
WL = pd.read_csv("./input/WL_05485500_2023_2024.csv", parse_dates=["Date"])
WL.set_index("Date", inplace=True)  # Set 'Date' as index for time series processing

# Resample daily WL data to monthly average (beginning of each month)
monthly_WL = WL.resample("MS").mean()  # "MS" means Month Start
monthly_WL["Month"] = monthly_WL.index.month  # Add a column for month number


# ----------------------------------------------------------------------------------------------------------
#                          Normalize WL data to [0,1] and apply power transformation 
# ----------------------------------------------------------------------------------------------------------

# set bita [calibrating parameter]
bita = 0.33  # Power transformation parameter to emphasize lower values more

min_val = monthly_WL["WL"].min()
max_val = monthly_WL["WL"].max()

# Normalize the monthly WL data using min-max normalization
monthly_WL["Normalized_WL"] = (monthly_WL["WL"] - min_val) / (max_val - min_val)

# Apply power transformation to normalized WL to enhance seasonal signal
monthly_WL["Power_Transformed_Normalized_WL"] = monthly_WL["Normalized_WL"] ** bita

# Assign mid-point of each month (15th day) to represent monthly WL time stamp
monthly_WL["DayOfMonth"] = 15  # Constant value for 15th day
monthly_WL["MidDate"] = monthly_WL.index + pd.to_timedelta(monthly_WL["DayOfMonth"] - 1, unit="D")

# Limit data to 24 months (ensure consistent time window for interpolation)    [for 3 years 36]
monthly_WL = monthly_WL.iloc[:24]  # This step is optional depending on the dataset range

# Generate daily date range for interpolation (set start and end date)
daily_dates = pd.date_range(start="2023-01-01", end="2024-12-31", freq="D")

# Perform Piecewise Cubic Hermite Interpolation (PCHIP)
# PCHIP preserves monotonicity and avoids overshooting, ideal for hydrologic variables

pchip = PchipInterpolator(
    x=monthly_WL["MidDate"].map(pd.Timestamp.toordinal),  # Convert datetime to ordinal (integer days)
    y=monthly_WL["Power_Transformed_Normalized_WL"]       # Values to interpolate
)

# Interpolate power-transformed WL at daily resolution
interp_values = pchip(daily_dates.map(pd.Timestamp.toordinal))

# Save interpolated daily WL values to CSV
daily_norm = pd.DataFrame({
    "Date": daily_dates,
    "Power_Transformed_Normalized_WL": interp_values
})

daily_norm.to_csv("./output/alpha.csv", index=False)

