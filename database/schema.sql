CREATE TABLE LocalResults (
    id INTEGER PRIMARY KEY,
    title TEXT,
    place_id TEXT UNIQUE,
    rating REAL,
    reviews INTEGER,
    price TEXT,
    type TEXT,
    address TEXT,
    open_state TEXT,
    phone TEXT,
    website TEXT,
    facebook_url TEXT UNIQUE,
    instagram_url TEXT UNIQUE,
    latitude REAL,
    longitude REAL,
    reviews_link TEXT,
    photos_link TEXT,
    processed INTEGER,
    has_lunch_menu INTEGER
);

CREATE TABLE GpsCoordinates (
    id INTEGER PRIMARY KEY,
    local_result_id INTEGER,
    latitude REAL,
    longitude REAL,
    FOREIGN KEY (local_result_id) REFERENCES LocalResults(id)  ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE OperatingHours (
    id INTEGER PRIMARY KEY,
    local_result_id INTEGER,
    day TEXT,
    hours TEXT,
    FOREIGN KEY (local_result_id) REFERENCES LocalResults(id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE ServiceOptions (
    id INTEGER PRIMARY KEY,
    local_result_id INTEGER,
    option_name TEXT,
    option_value TEXT,
    FOREIGN KEY (local_result_id) REFERENCES LocalResults(id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE Types (
    id INTEGER PRIMARY KEY,
    local_result_id INTEGER,
    type TEXT,
    FOREIGN KEY (local_result_id) REFERENCES LocalResults(id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE FBPosts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_url TEXT NOT NULL,
    time DATETIME NOT NULL,
    text TEXT NOT NULL,
    post_id INTEGER NOT NULL,
    local_result_id INTEGER,
    FOREIGN KEY (local_result_id) REFERENCES LocalResults(id) ON DELETE CASCADE ON UPDATE CASCADE
);


CREATE TABLE LunchSpecs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    menu_frequency TEXT,
    lunch_hours TEXT,
    lunch_price_range TEXT,
    local_result_id INTEGER UNIQUE,
    FOREIGN KEY (local_result_id) REFERENCES LocalResults(id) ON DELETE CASCADE ON UPDATE CASCADE
);