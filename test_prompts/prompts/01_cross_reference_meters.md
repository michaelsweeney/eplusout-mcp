Using the EnergyPlus outputs in the `example-files/` directory of this repository, do the following:

1. Scan the `example-files/` directory and list all available models with their file types (HTML, SQL, epJSON, etc.).
2. For each model that has an HTML report, search for the "End Uses" table and retrieve it. Report the annual consumption for Heating, Interior Lighting, and Interior Equipment (electricity and natural gas), plus the Total End Uses.
3. List the available hourly timeseries variables in each model's SQL database.
4. Pull the full 8760-hour timeseries for the Electricity:Facility and NaturalGas:Facility variables in the Buffalo model.
5. Cross-reference: Sum the hourly SQL timeseries for Electricity:Facility and NaturalGas:Facility, convert from Joules to GJ, and compare against the Total End Uses values from the HTML End Uses table. Do they match exactly? Show the values side by side for both models.
