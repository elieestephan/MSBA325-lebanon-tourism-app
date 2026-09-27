# Lebanon's tourism infrastructure — interactive drill-down

An interactive Streamlit page built on the **Tourism – Lebanon 2023** dataset (town-level
observations for all 1,137 Lebanese towns) from the
[AUB LINKED portal](https://linked.aub.edu.lb:8502/).

**Live app:** <!-- paste your Streamlit Community Cloud link here -->

## What the page shows

The national totals are dominated by a handful of towns, so the page lets a reader move from the
country down to a single region and then raise a quality bar within it.

Two visualisations respond to the controls:

1. **What the supply is made of** — a stacked bar of hotels, guest houses, cafés and restaurants,
   by region when viewing all of Lebanon and by town once a region is chosen, beside a donut of the
   food-versus-lodging split for the current selection.
2. **Cafés against restaurants** — one dot per town, bubble size for lodging and colour for the
   Tourism Index, with the rest of the country kept faintly in the background for context.

Two insights the page surfaces:

- Food and drink are roughly 83% of national tourism supply and hotels only 6% — infrastructure
  built for day visitors rather than overnight stays.
- Cafés and restaurants correlate strongly (r ≈ 0.73), but lodging does not follow them: towns like
  Qbaiyat Aakkar hold dozens of guest houses with almost no food service, while Ghobairi is the
  reverse.

## The two linked controls

| Control | Widget | Link |
|---|---|---|
| 1 · Region | `st.selectbox` | Sets the scope for everything below |
| 2 · Minimum Tourism Index | `st.select_slider` | Its **options are generated from the region chosen above** — only the scores that actually occur there are offered |

The Tourism Index is built from four yes/no questions (hotel, café and restaurant worth 3 points
each, guest house worth 1), so scores of 2, 5 and 8 are impossible. Reading the slider's steps from
the data avoids offering a reader values no town can hold.

## Running it locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Files

| File | Purpose |
|---|---|
| `app.py` | The Streamlit app |
| `tourism_lebanon_2023.csv` | The dataset, as downloaded from the LINKED portal |
| `requirements.txt` | Dependencies for Streamlit Community Cloud |

## Data notes

The published CSV needed two repairs, both handled in `load_data()`:

1. It is **double UTF-8 encoded** — "Zahlé" arrives as `ZahlÃ©`.
2. `refArea` stores DBpedia URIs rather than readable region names.
