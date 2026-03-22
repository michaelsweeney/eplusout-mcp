Using the EnergyPlus outputs in `example-files/large-batch/`, do the following:

1. Scan the directory and list all available models. Summarize what building types, climate locations, and file types (HTML, SQL) are represented.
2. For each model, retrieve the "End Uses" table from HTML. Build a comparison table showing annual Heating (electricity + gas, in GJ) and Cooling (electricity, in GJ) for every model, sorted by total heating load descending.
3. Which building type has the highest heating loads on average? Which has the highest cooling loads on average?
4. Search for "unmet hours" tables across all models. Create a summary showing which models have non-zero unmet heating or cooling hours, the facility totals, and the worst zone in each case.
5. Search for "Zone Sensible Heating" tables. For the 3 models with the highest peak heating design loads, retrieve those tables and report the peak zone, design load (W), and design day conditions.
6. Compare the Hospital models across their 3 climates: how do heating load, cooling load, and unmet hours differ? Which climate is the most challenging for this building type?
7. List available hourly SQL variables for one of the Hospital models. Pull the Heating:NaturalGas and Cooling:Electricity hourly meter data, and identify the peak heating day and peak cooling day. Do these align with the design days from the HTML Zone Sensible Heating table?
8. Cross-reference: For the model with the highest unmet heating hours, sum the annual Electricity:Facility meter from SQL and compare against the Total Electricity from the HTML End Uses table. Do they match?
