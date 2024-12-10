---
title: austin-food-scores
emoji: 🌮🍔🍕
colorFrom: blue
colorTo: pink
sdk: gradio
sdk_version: 5.7.1
app_file: app.py
pinned: false
license: apache-2.0
---

# austin-food-scores

Does this sound like you?

- Hates dirty restaurants
- Standing in Austin, TX

Then head over to [austin-food-scores](https://huggingface.co/spaces/ThatOrJohn/austin-food-scores).

Click the `Update Location` button to plot nearby restaurants on the map. Click a restaurant to display its most recent
inspection score.

[Gradio](https://www.gradio.app/) app that displays Austin food establishment inspection scores
for locations in an 800 meter radius of your current location.

[Dataset description](https://datahub.austintexas.gov/stories/s/Food-Establishment-Inspection-Scores/7scf-8i7v/)

### If you're trying to run this on your own, you'll need to export an env var called

`AUSTIN_DATA_API_TOKEN` with a valid token for the [Austin Open Data Portal](https://data.austintexas.gov)
