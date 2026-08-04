INSERT INTO genre (genre_name)
VALUES
    ('Rock'),
    ('Pop'),
    ('Jazz'),
    ('Classical'),
    ('Electronic');


INSERT INTO media_type (
    media_type_name,
    file_extension,
    mime_type
)
VALUES
    ('MP3', '.mp3', 'audio/mpeg'),
    ('FLAC', '.flac', 'audio/flac'),
    ('AAC', '.aac', 'audio/aac');


INSERT INTO artist (
    artist_name,
    biography,
    website_url,
    debut_year,
    country
)
VALUES
    (
        'The Sound Waves',
        'Independent rock band',
        'https://example.com/sound-waves',
        2018,
        'India'
    ),
    (
        'Anaya Rao',
        'Independent pop artist',
        'https://example.com/anaya-rao',
        2020,
        'India'
    );