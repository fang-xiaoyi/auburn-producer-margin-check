# Producer Margin Check

This is a working Streamlit prototype for a producer-facing Alabama cow-calf
margin and benchmark tool.

## Run locally

From this folder:

```text
python -m pip install -r requirements.txt
streamlit run app.py
```

The app includes:

- farm-level input fields for production, revenue, scale, and cost categories;
- gross revenue, break-even price, total cost, margin, and annual margin;
- Alabama Extension enterprise and representative-farm benchmarks;
- USDA ERS national cost benchmarks by herd-size category;
- optional previous-year, three-year, and five-year cost comparisons;
- category-level gap diagnosis and management prompts;
- a scenario lab for testing production, price, and cost assumptions;
- a downloadable JSON report and import function for continuing a saved analysis.

The public reference values are documented in the Sources and definitions tab.
They are reference scenarios, not a statistical claim that one representative
farm describes every Alabama operation.
