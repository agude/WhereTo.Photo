from app import app
from flask import render_template, request
from settings import APP_ROOT, APP_STATIC
import helpers
import json
import re

@app.route('/')
@app.route('/index')
def cities_input():
  return render_template("input.html")

@app.route('/output')
def cities_output():
    #pull 'ID' from input field and store it
    tag = request.args.get('ID')
    if tag is None:
        return render_template("error.html",
                title = "Missing Tag",
                text = "It looks like you didn't enter anything!",
                )

    # Get the city
    city_id = request.args.get('CITY')
    if city_id not in [1, 2, '1', '2']:
        return render_template("error.html",
                title = "Invalid City",
                text = "We only support San Francisco and Seattle for now, sorry!",
                )

    # Clean up the tag
    clean_tag = tag.strip().lower().replace(' ', '')
    clean_tag = re.sub("[\W_]+", '', clean_tag)

    # Get coords from results
    try:
        best_coord = helpers.get_results_from_tag(clean_tag, city_id)
    except IndexError:
        return render_template("error.html",
                title = "Unknown Tag",
                text = "No one has used that tag in the dataset, yet!",
                )

    # Get all the photos
    photo_coords = helpers.get_photos_from_tags((clean_tag,), city_id)
    leaflet_coords = []
    seen_photos = []
    for (views, photo_id, url, coord) in photo_coords:
        datum = {
                "lat": coord.lat,
                "lon": coord.lon,
                "url": url,
                "photo_id": photo_id,
                "views": views,
                }
        seen_photos.append(photo_id)
        leaflet_coords.append(datum)

    seen_photos = set(seen_photos)

    # Set the page title string
    title = tag.capitalize()

    # Render the page
    return render_template("output.html",
            title = title,
            city_id = city_id,
            best_lon = best_coord.lon,
            best_lat = best_coord.lat,
            tag_coords = json.dumps(list(leaflet_coords)),
            )

@app.errorhandler(404)
def page_not_found(e):
    return render_template("error.html",
            title = str(e),
            text = "Sorry, that page doesn't exist."
            )
