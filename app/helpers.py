from math import sin, cos, sqrt, atan2, radians
import pymysql as mdb
from credentials import DB_INFO

DB_NAME = "flickr_data"
con_read = mdb.connect(
        DB_INFO['host'],
        DB_INFO['readonly_user'],
        DB_INFO['password'],
        DB_NAME,
        autocommit=True,
        )

class Coordinate:

    def __init__(self, lat, lon):
        self.lon = lon
        self.lat = lat
        self.coord = (lat, lon)

    def set_xy(self, basemap):
        self.x, self.y = basemap(self.lon, self.lat)
        self.xy = (self.x, self.y)

    def distance_to(self, other):
        """ Returns the distance between two coordinate objects in km. """
        # Radius of earth in km
        R = 6373.0

        lat1r = radians(self.lat)
        lon1r = radians(self.lon)
        lat2r = radians(other.lat)
        lon2r = radians(other.lon)

        dlon = lon2r - lon1r
        dlat = lat2r - lat1r

        a = sin(dlat / 2)**2 + cos(lat1r) * cos(lat2r) * sin(dlon / 2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        distance = R * c

        return distance

    def __str__(self):
        return self.coord.__str__()

    def __repr__(self):
        return self.coord.__repr__()


def city_coordinate(city_id, con=con_read):
    with con:
        cur = con.cursor()
        SELECT = """SELECT lat, lon
                    FROM cities
                    WHERE city_id = {city_id}""".format(
                city_id=city_id
                )
        cur.execute(SELECT)
        rows = cur.fetchall()
        cur.close()

        (lat, lon) = rows[0]
        return Coordinate(lat, lon)


def get_related_tags(tag, city_id, con=con_read):
    with con:
        cur = con.cursor()
        SELECT = """SELECT daughter.tag
        FROM tag_graph tg
        LEFT JOIN tags parent ON tg.tag_id = parent.tag_id
        LEFT JOIN tags daughter ON tg.related_tag = daughter.tag_id
        WHERE parent.tag = %s
        AND tg.city_id = %s
        AND tg.distance <= 5;
        """
        cur.execute(SELECT, (tag, city_id))
        rows = cur.fetchall()
        return [tag for (tag,) in rows]


def get_photos_from_tags(tags, city_id, radius=15, con=con_read):
    """ Returns a list of (views, lat, lon) tuples that contain one of a list
    of tags. """
    # Coordinates of the city to measure radius from
    city_center = city_coordinate(city_id, con)

    with con:
        cur = con.cursor()
        str_tags = [tag for tag in tags]
        TAGS = "('" + "','".join(str_tags) + "')"
        SELECT = """SELECT p.photo_id, url, p.views, p.lat, p.lon
        FROM photo_tags pt, photos p, tags t
        WHERE p.city_id = {city_id}
        AND pt.photo_id = p.photo_id
        AND pt.tag_id = t.tag_id
        AND t.tag in {tags}
        """.format(
                tags=TAGS,
                city_id=city_id
                )
        cur.execute(SELECT)
        output = []

        # Select photos within some distance of the city
        seen_ids = []
        for photo_id, url, views, lat, lon in cur:
            # Remove redundant photos
            if photo_id in seen_ids:
                continue
            seen_ids.append(photo_id)
            # Set up a tuple of coordinates and views
            coord = Coordinate(lat, lon)
            if city_center.distance_to(coord) <= radius:
                output.append((views, photo_id, url, coord))
        cur.close()

        return output


def get_results_from_tag(tag, city_id, con=con_read):
    with con:
        cur = con.cursor()

        # Get all tags
        SELECT = """SELECT r.lat, r.lon
        FROM results_no_related r
        LEFT JOIN tags t ON t.tag_id = r.tag_id
        WHERE t.tag = %s
        AND r.city_id = %s
        """
        cur.execute(SELECT, (tag, city_id))
        rows = cur.fetchall()
        cur.close()
        lat, lon = rows[0]
        coord = Coordinate(lat, lon)

        return coord
