Using the EnergyPlus outputs in `test_prompts/models/`, do the following:

1. Scan the directory and list all available models. How many models are there, and what building types and climates are represented?
2. For each model, retrieve the "End Uses" table from the HTML reports. Build a summary table showing annual Heating (electricity + gas, in GJ) and Cooling (electricity, in GJ) for every model.
3. Rank the models by total heating load (highest first) and total cooling load (highest first). Which 3 models have the highest heating? Which 3 have the highest cooling?
4. Search for "unmet hours" tables across all models. Which models have non-zero unmet heating hours? List the model name, facility total, and worst zone for each.
5. For the model with the most unmet heating hours, list the available SQL hourly variables and pull the timeseries for any heating-related variable. What's the peak hourly value and when does it occur?
6. Cross-reference: Do the models with the highest heating loads also have the most unmet heating hours, or are they different? What might explain any discrepancy?
