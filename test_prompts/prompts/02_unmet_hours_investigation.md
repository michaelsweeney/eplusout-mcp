Using the EnergyPlus outputs in the `example-files/` directory of this repository, do the following:

1. Scan the directory and list all available models with their file types.
2. Search the HTML reports for tables related to "setpoint not met" and "zone sensible heating", then retrieve those tables for each model.
3. Identify which model(s) have non-zero unmet heating hours, and which specific zone has the highest unmet heating hours. Report the exact zone name, hour count, and the facility-level total.
4. For that worst-performing zone, find its heating design load and setpoint temperature from the Zone Sensible Heating table.
5. Check the SQL database for that model — list available hourly variables. Is there a zone-level temperature timeseries for the worst zone? If not, explain what Output:Variable would need to be added to the IDF to enable hourly cross-referencing, and describe what analysis you would perform if the data were available.
6. The Buffalo model has Boiler Heating Rate variables in its SQL. Pull those hourly timeseries and identify the peak heating day. Does the peak boiler day correlate with the design day listed in the Zone Sensible Heating table?
7. Using the SQL electricity and gas meter data, verify that the annual sums match the HTML End Uses totals for that model.
